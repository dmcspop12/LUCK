import subprocess
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

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
