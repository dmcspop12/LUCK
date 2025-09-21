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


def download_file(url: str, filepath: Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)

    tmp_filepath = Path(TMP_DIRPATH, str(uuid4()))

    tmp_filepath.parent.mkdir(parents=True, exist_ok=True)

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


def download_asset(res_version: str, asset_rel_filepath: Path):
    asset_filepath = Path(ASSET_DIRPATH) / res_version / asset_rel_filepath

    if asset_filepath.is_file():
        return

    asset_filepath.parent.mkdir(parents=True, exist_ok=True)

    asset_dat_url = get_asset_dat_url(res_version, asset_rel_filepath)

    asset_dat_filepath = asset_filepath.with_suffix(".dat")

    download_file(asset_dat_url, asset_dat_filepath)

    with ZipFile(asset_dat_filepath) as zf:
        asset_filepath.write_bytes(zf.read(asset_rel_filepath.as_posix()))


HOT_UPDATE_LIST_JSON = "hot_update_list.json"


def download_hot_update_list(res_version: str):
    hot_update_list_filepath = Path(ASSET_DIRPATH, res_version, HOT_UPDATE_LIST_JSON)

    hot_update_list_url = (
        f"{ORIG_ASSET_URL_PREFIX}/{res_version}/{HOT_UPDATE_LIST_JSON}"
    )

    download_file(hot_update_list_url, hot_update_list_filepath)
