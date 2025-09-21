import json
from pathlib import Path

import UnityPy

from .helper import download_hot_update_list, download_asset
from .const import TMP_DIRPATH, ASSET_DIRPATH, MOD_DIRPATH


class Resource:
    def __init__(self, client_version: str, res_version: str):
        self.client_version = client_version
        self.res_version = res_version

        self.asset_dict = {}

        self.load_hot_update_list()

    def load_hot_update_list(self):
        hot_update_list_filepath = download_hot_update_list(self.res_version)

        with open(hot_update_list_filepath, encoding="utf-8") as f:
            hot_update_list = json.load(f)

        self.hot_update_list = hot_update_list

    def load_asset(self, ab_name: str):
        asset_filepath = download_asset(self.res_version, Path(ab_name))

        asset_env = UnityPy.load(asset_filepath.as_posix())

        self.asset_dict[ab_name] = asset_env

    def load_anon_asset(self):
        for ab_info in self.hot_update_list["abInfos"]:
            ab_name = ab_info["name"]

            if not ab_name.startswith("anon/"):
                continue

            self.load_asset(ab_name)
