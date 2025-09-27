import subprocess
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
import json
from functools import wraps
import zipfile
from zipfile import ZipFile

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import bson
from packaging.version import Version

from .const import TMP_DIRPATH, ASSET_DIRPATH, KnownTable


ORIG_ASSET_URL_PREFIX = "https://ak.hycdn.cn/assetbundle/official/Android/assets"


def remove_aria2_tmp(tmp_filepath: Path):
    tmp_filepath.unlink(missing_ok=True)

    aria2_tmp_filepath = tmp_filepath.with_suffix(tmp_filepath.suffix + ".aria2")

    aria2_tmp_filepath.unlink(missing_ok=True)


def ensure_tmp_dir():
    Path(TMP_DIRPATH).mkdir(parents=True, exist_ok=True)


def get_tmp_filepath():
    ensure_tmp_dir()

    tmp_filepath = Path(TMP_DIRPATH, str(uuid4()))

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


def escape_ab_name(ab_name: str) -> str:
    return ab_name.replace("/", "_").replace("#", "__")


def get_asset_dat_url(res_version: str, asset_rel_filepath: Path):
    asset_dat_rel_filepath = asset_rel_filepath.with_suffix(".dat")

    asset_dat_url_filename = escape_ab_name(asset_dat_rel_filepath.as_posix())

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
    ensure_tmp_dir()

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


def raw_dump(data: bytes | str, dump_filename: str):
    ensure_tmp_dir()

    dump_filepath = Path(
        TMP_DIRPATH,
        dump_filename,
    )
    if isinstance(data, bytes):
        dump_filepath = dump_filepath.with_suffix(".bin")
        dump_filepath.write_bytes(data)
    elif isinstance(data, str):
        dump_filepath = dump_filepath.with_suffix(".txt")
        dump_filepath.write_text(data, "utf-8", SURROGATE_ESCAPE)


def raw_dump_decorator(name: str):
    def _raw_dump_decorator(func):
        @wraps(func)
        def wrapper(data):
            raw_dump(data, f"{name}_pre")
            data = func(data)
            raw_dump(data, f"{name}_post")
            return data

        return wrapper

    return _raw_dump_decorator


def bson_decorator(func):
    @wraps(func)
    def wrapper(data):
        return bson.encode(func(bson.decode(data)))

    return wrapper


def get_known_table_decorator_lst(
    table_name: KnownTable, client_version: str, res_version: str
):
    match table_name:
        case (
            KnownTable.ACTIVITY_TABLE
            | KnownTable.AUDIO_DATA
            | KnownTable.BATTLE_EQUIP_TABLE
            | KnownTable.BUFF_TABLE
            | KnownTable.BUILDING_DATA
            | KnownTable.BUILDING_LOCAL_DATA
            | KnownTable.CAMPAIGN_TABLE
            | KnownTable.CHAPTER_TABLE
            | KnownTable.CHARACTER_TABLE
            | KnownTable.CHARM_TABLE
            | KnownTable.CHARWORD_TABLE
            | KnownTable.CHAR_MASTER_TABLE
            | KnownTable.CHAR_META_TABLE
            | KnownTable.CHAR_PATCH_TABLE
            | KnownTable.CHECKIN_TABLE
            | KnownTable.CLIMB_TOWER_TABLE
            | KnownTable.CLUE_DATA
            | KnownTable.COOPERATE_BATTLE_TABLE
            | KnownTable.CRISIS_TABLE
            | KnownTable.CRISIS_V2_TABLE
            | KnownTable.DISPLAY_META_TABLE
            | KnownTable.ENEMY_DATABASE
            | KnownTable.ENEMY_HANDBOOK_TABLE
            | KnownTable.EP_BREAKBUFF_TABLE
            | KnownTable.EXTRA_BATTLELOG_TABLE
            | KnownTable.FAVOR_TABLE
            | KnownTable.GACHA_TABLE
            | KnownTable.GAMEDATA_CONST
            | KnownTable.HANDBOOK_INFO_TABLE
            | KnownTable.HANDBOOK_TEAM_TABLE
            | KnownTable.HOTUPDATE_META_TABLE
            | KnownTable.INIT_TEXT
            | KnownTable.ITEM_TABLE
            | KnownTable.LEGION_MODE_BUFF_TABLE
            | KnownTable.LEVEL_SCRIPT_TABLE
            | KnownTable.MAIN_TEXT
            | KnownTable.MEDAL_TABLE
            | KnownTable.META_UI_TABLE
            | KnownTable.MISSION_TABLE
            | KnownTable.OPEN_SERVER_TABLE
            | KnownTable.REPLICATE_TABLE
            | KnownTable.RETRO_TABLE
            | KnownTable.ROGUELIKE_TOPIC_TABLE
            | KnownTable.SANDBOX_PERM_TABLE
            | KnownTable.SHOP_CLIENT_TABLE
            | KnownTable.SKILL_TABLE
            | KnownTable.SKIN_TABLE
            | KnownTable.SPECIAL_OPERATOR_TABLE
            | KnownTable.STAGE_TABLE
            | KnownTable.STORY_REVIEW_META_TABLE
            | KnownTable.STORY_REVIEW_TABLE
            | KnownTable.STORY_TABLE
            | KnownTable.TIP_TABLE
            | KnownTable.TOKEN_TABLE
            | KnownTable.UNIEQUIP_TABLE
            | KnownTable.ZONE_TABLE
        ):
            return [
                script_decorator,
                header_decorator,
                flatc_decorator(client_version, table_name.value),
                json_decorator,
                dump_table_decorator(f"{table_name.value}_{res_version}"),
            ]

        case (
            KnownTable.HANDBOOK_TABLE
            | KnownTable.PLAYER_AVATAR_TABLE
            | KnownTable.RANGE_TABLE
            | KnownTable.ROGUELIKE_TABLE
            | KnownTable.SANDBOX_TABLE
            | KnownTable.TECH_BUFF_TABLE
            | KnownTable.UNIEQUIP_DATA
        ):
            return [
                script_decorator,
                header_decorator,
                crypt_decorator,
                encoding_decorator,
                json_decorator,
                dump_table_decorator(f"{table_name.value}_{res_version}"),
            ]

        case KnownTable.BATTLE_MISC_TABLE:
            return [
                script_decorator,
                header_decorator,
                crypt_decorator,
                bson_decorator,
                dump_table_decorator(f"{table_name.value}_{res_version}"),
            ]

        case KnownTable.BUFF_TEMPLATE_DATA:
            return [
                script_decorator,
                bson_decorator,
                dump_table_decorator(f"{table_name.value}_{res_version}"),
            ]

        case KnownTable.DATA_VERSION:
            return [
                script_decorator,
                encoding_decorator,
                raw_dump_decorator(f"{table_name.value}_{res_version}"),
            ]

        case _:
            raise ValueError(f"unsupported table_name {table_name}")


def is_known_table_available(table_name: KnownTable, client_version: str):
    match table_name:
        case (
            KnownTable.CLUE_DATA
            | KnownTable.CRISIS_TABLE
            | KnownTable.CRISIS_V2_TABLE
            | KnownTable.DISPLAY_META_TABLE
            | KnownTable.HANDBOOK_TEAM_TABLE
            | KnownTable.INIT_TEXT
            | KnownTable.LEGION_MODE_BUFF_TABLE
            | KnownTable.MAIN_TEXT
            | KnownTable.META_UI_TABLE
        ):
            if Version(client_version) < Version("2.5.04"):
                return False

        case KnownTable.CHAR_MASTER_TABLE | KnownTable.SPECIAL_OPERATOR_TABLE:
            if Version(client_version) < Version("2.6.01"):
                return False

        case KnownTable.LEVEL_SCRIPT_TABLE:
            if Version(client_version) < Version("2.6.21"):
                return False

    return True


def write_mod(mod_filepath: str, ab_name: str, content: bytes):
    with ZipFile(mod_filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(ab_name, content)


RESOURCE_MANIFEST = "resource_manifest"


def get_manifest(manifest_bytes: bytes, client_version: str):
    return json.loads(
        decode_flatc(
            remove_header(manifest_bytes),
            client_version,
            RESOURCE_MANIFEST,
        )
    )


def get_mod_level_decorator_lst(level_id: str, client_version: str, res_version: str):
    return [
        script_decorator,
        header_decorator,
        flatc_decorator(client_version, "prts___levels"),
        json_decorator,
        dump_table_decorator(f"{level_id}_{res_version}"),
    ]


def get_manifest_bytes(manifest, client_version: str) -> bytes:
    return add_header(
        encode_flatc(
            json.dumps(manifest, ensure_ascii=False),
            client_version,
            RESOURCE_MANIFEST,
        )
    )
