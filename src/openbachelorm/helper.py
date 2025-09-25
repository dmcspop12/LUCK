import subprocess
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
import json
from functools import wraps

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from .const import TMP_DIRPATH, ASSET_DIRPATH


ORIG_ASSET_URL_PREFIX = "https://ak.hycdn.cn/assetbundle/official/Android/assets"


def remove_aria2_tmp(tmp_filepath: Path):
    tmp_filepath.unlink(missing_ok=True)

    aria2_tmp_filepath = tmp_filepath.with_suffix(tmp_filepath.suffix + ".aria2")

    aria2_tmp_filepath.unlink(missing_ok=True)


def get_tmp_filepath():
    tmp_filepath = Path(TMP_DIRPATH, str(uuid4()))

    tmp_filepath.parent.mkdir(parents=True, exist_ok=True)

    return tmp_filepath


def download_file(url: str, filepath: Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)

    tmp_filepath = get_tmp_filepath()

    try:
        proc = subprocess.run(
            [
                "aria2c",
                "-q",
                "-o",
                tmp_filepath.as_posix(),
                "--auto-file-renaming=false",
                url,
            ]
        )

        if proc.returncode:
            raise ConnectionError(f"download_file failed to download {url}")

        tmp_filepath.replace(filepath)

    finally:
        remove_aria2_tmp(tmp_filepath)


def get_asset_dat_url(res_version: str, asset_rel_filepath: Path):
    asset_dat_rel_filepath = asset_rel_filepath.with_suffix(".dat")

    asset_dat_url_filename = (
        asset_dat_rel_filepath.as_posix().replace("/", "_").replace("#", "__")
    )

    return f"{ORIG_ASSET_URL_PREFIX}/{res_version}/{asset_dat_url_filename}"


def download_asset(res_version: str, asset_rel_filepath: Path) -> Path:
    asset_filepath = Path(ASSET_DIRPATH) / res_version / asset_rel_filepath

    if asset_filepath.is_file():
        return asset_filepath

    asset_filepath.parent.mkdir(parents=True, exist_ok=True)

    asset_dat_url = get_asset_dat_url(res_version, asset_rel_filepath)

    asset_dat_filepath = asset_filepath.with_suffix(".dat")

    download_file(asset_dat_url, asset_dat_filepath)

    with ZipFile(asset_dat_filepath) as zf:
        asset_filepath.write_bytes(zf.read(asset_rel_filepath.as_posix()))

    return asset_filepath


HOT_UPDATE_LIST_JSON = "hot_update_list.json"


def download_hot_update_list(res_version: str) -> Path:
    hot_update_list_filepath = Path(ASSET_DIRPATH, res_version, HOT_UPDATE_LIST_JSON)

    if hot_update_list_filepath.is_file():
        return hot_update_list_filepath

    hot_update_list_url = (
        f"{ORIG_ASSET_URL_PREFIX}/{res_version}/{HOT_UPDATE_LIST_JSON}"
    )

    download_file(hot_update_list_url, hot_update_list_filepath)

    return hot_update_list_filepath


SURROGATE_ESCAPE = "surrogateescape"


def script_to_bytes(script: str) -> bytes:
    return script.encode("utf-8", SURROGATE_ESCAPE)


def bytes_to_script(script_bytes: bytes) -> str:
    return script_bytes.decode("utf-8", SURROGATE_ESCAPE)


HEADER_SIZE = 0x80


def remove_header(script_bytes: bytes) -> bytes:
    return script_bytes[HEADER_SIZE:]


def add_header(script_bytes: bytes) -> bytes:
    return bytes(HEADER_SIZE) + script_bytes


def get_bin_tmp_filepath(tmp_filepath):
    return tmp_filepath.with_suffix(".bin")


def get_json_tmp_filepath(tmp_filepath):
    return tmp_filepath.with_suffix(".json")


def remove_flatc_tmp(tmp_filepath: Path):
    bin_tmp_filepath = get_bin_tmp_filepath(tmp_filepath)
    json_tmp_filepath = get_json_tmp_filepath(tmp_filepath)

    bin_tmp_filepath.unlink(missing_ok=True)
    json_tmp_filepath.unlink(missing_ok=True)


def get_fbs_filepath(client_version: str, fbs_name: str) -> Path:
    return Path(
        "fbs",
        client_version,
        f"{fbs_name}.fbs",
    )


def decode_flatc(script_bytes: bytes, client_version: str, fbs_name: str) -> str:
    fbs_filepath = get_fbs_filepath(client_version, fbs_name)

    tmp_filepath = get_tmp_filepath()

    bin_tmp_filepath = get_bin_tmp_filepath(tmp_filepath)
    json_tmp_filepath = get_json_tmp_filepath(tmp_filepath)

    try:
        bin_tmp_filepath.write_bytes(script_bytes)

        proc = subprocess.run(
            [
                "flatc",
                "--strict-json",
                "--natural-utf8",
                "--no-warnings",
                "--json",
                "--raw-binary",
                "-o",
                json_tmp_filepath.parent.as_posix(),
                fbs_filepath.as_posix(),
                "--",
                bin_tmp_filepath.as_posix(),
            ]
        )

        if proc.returncode:
            raise ValueError(f"decode_flatc failed to decode {fbs_name}")

        return json_tmp_filepath.read_text("utf-8")

    finally:
        remove_flatc_tmp(tmp_filepath)


def encode_flatc(json_str: str, client_version: str, fbs_name: str) -> bytes:
    fbs_filepath = get_fbs_filepath(client_version, fbs_name)

    tmp_filepath = get_tmp_filepath()

    bin_tmp_filepath = get_bin_tmp_filepath(tmp_filepath)
    json_tmp_filepath = get_json_tmp_filepath(tmp_filepath)

    try:
        json_tmp_filepath.write_text(json_str, "utf-8")

        proc = subprocess.run(
            [
                "flatc",
                "--strict-json",
                "--natural-utf8",
                "--no-warnings",
                "--binary",
                "-o",
                bin_tmp_filepath.parent.as_posix(),
                fbs_filepath.as_posix(),
                json_tmp_filepath.as_posix(),
            ]
        )

        if proc.returncode:
            raise ValueError(f"encode_flatc failed to encode {fbs_name}")

        return bin_tmp_filepath.read_bytes()

    finally:
        remove_flatc_tmp(tmp_filepath)


AES_KEY = b"UITpAi82pHAWwnzq"

AES_IV_MASK = b"HRMCwPonJLIB3WCl"


def get_iv(data: bytes) -> bytes:
    return bytes([i ^ j for i, j in zip(data, AES_IV_MASK)])


def decrypt_data(data: bytes) -> bytes:
    iv = get_iv(data)

    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv=iv)

    return unpad(cipher.decrypt(data[len(AES_IV_MASK) :]), AES.block_size)


def encrypt_data(data: bytes) -> bytes:
    header = bytes(len(AES_IV_MASK))

    iv = get_iv(header)

    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv=iv)

    return header + cipher.encrypt(pad(data, AES.block_size))


def script_decorator(func):
    @wraps(func)
    def wrapper(data):
        return bytes_to_script(func(script_to_bytes(data)))

    return wrapper


def header_decorator(func):
    @wraps(func)
    def wrapper(data):
        return add_header(func(remove_header(data)))

    return wrapper


def flatc_decorator(client_version: str, fbs_name: str):
    def _flatc_decorator(func):
        @wraps(func)
        def wrapper(data):
            return encode_flatc(
                func(
                    decode_flatc(
                        data,
                        client_version,
                        fbs_name,
                    )
                ),
                client_version,
                fbs_name,
            )

        return wrapper

    return _flatc_decorator


def json_decorator(func):
    @wraps(func)
    def wrapper(data):
        return json.dumps(func(json.loads(data)), ensure_ascii=False)

    return wrapper


def dump_table(table, dump_filename: str):
    with open(
        Path(
            TMP_DIRPATH,
            dump_filename,
        ),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            table,
            f,
            ensure_ascii=False,
            indent=4,
        )


def dump_table_decorator(name: str):
    def _dump_table_decorator(func):
        @wraps(func)
        def wrapper(data):
            dump_table(data, f"{name}_pre.json")
            data = func(data)
            dump_table(data, f"{name}_post.json")
            return data

        return wrapper

    return _dump_table_decorator


def crypt_decorator(func):
    @wraps(func)
    def wrapper(data):
        return encrypt_data(func(decrypt_data(data)))

    return wrapper


def encoding_decorator(func):
    @wraps(func)
    def wrapper(data):
        return func(data.decode("utf-8")).encode("utf-8")

    return wrapper


def nop_mod_table_func(table):
    return table
