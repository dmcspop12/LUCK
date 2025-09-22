import json
from pathlib import Path
import zipfile
from zipfile import ZipFile

import UnityPy

from .helper import download_hot_update_list, download_asset
from .const import TMP_DIRPATH, ASSET_DIRPATH, MOD_DIRPATH


class Resource:
    def __init__(self, client_version: str, res_version: str):
        self.client_version = client_version
        self.res_version = res_version

        self.asset_dict: dict[str, UnityPy.Environment] = {}
        self.modified_asset_set: set[str] = set()

        self.load_hot_update_list()

    def load_hot_update_list(self):
        hot_update_list_filepath = download_hot_update_list(self.res_version)

        with open(hot_update_list_filepath, encoding="utf-8") as f:
            hot_update_list = json.load(f)

        self.hot_update_list = hot_update_list

    def load_asset(self, ab_name: str):
        if ab_name in self.asset_dict:
            return

        asset_filepath = download_asset(self.res_version, Path(ab_name))

        asset_env = UnityPy.load(asset_filepath.as_posix())

        self.asset_dict[ab_name] = asset_env

    def get_asset_env(self, ab_name: str):
        asset_env = self.asset_dict[ab_name]

        return asset_env

    def load_anon_asset(self) -> set[str]:
        ab_name_set = set()

        for ab_info in self.hot_update_list["abInfos"]:
            ab_name = ab_info["name"]

            if not ab_name.startswith("anon/"):
                continue

            self.load_asset(ab_name)
            ab_name_set.add(ab_name)

        return ab_name_set

    def mark_modified_asset(self, ab_name: str):
        if ab_name not in self.asset_dict:
            raise KeyError(f"{ab_name} not loaded")

        self.modified_asset_set.add(ab_name)

    def build_mod(self, mod_name: str):
        mod_filepath = Path(MOD_DIRPATH, mod_name + ".dat")

        mod_filepath.parent.mkdir(parents=True, exist_ok=True)

        with ZipFile(mod_filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            for ab_name in self.modified_asset_set:
                asset_env = self.asset_dict[ab_name]
                zf.writestr(ab_name, asset_env.file.save())
