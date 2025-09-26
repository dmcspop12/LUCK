import json
from pathlib import Path
import zipfile
from zipfile import ZipFile

import UnityPy
from packaging.version import Version

from .helper import (
    download_hot_update_list,
    download_asset,
    escape_ab_name,
    write_mod,
    get_manifest,
    dump_table,
)
from .const import TMP_DIRPATH, ASSET_DIRPATH, MOD_DIRPATH


def get_anon_asset_name_set(asset_env: UnityPy.Environment):
    anon_asset_name_set: set[str] = set()

    for obj in asset_env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()

            anon_asset_name_set.add(data.m_Name)

    return anon_asset_name_set


def get_table_data_by_prefix(asset_env: UnityPy.Environment, table_prefix: str):
    for obj in asset_env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()

            if data.m_Name.startswith(table_prefix):
                return data

    return None


class Resource:
    def __init__(self, client_version: str, res_version: str):
        self.client_version = client_version
        self.res_version = res_version

        self.asset_dict: dict[str, UnityPy.Environment] = {}
        self.modified_asset_set: set[str] = set()

        self.anon_ab_name_set: set[str] = None
        self.anon_asset_name_dict: dict[str, set[str]] = {}

        self.load_hot_update_list()

    def load_hot_update_list(self):
        hot_update_list_filepath = download_hot_update_list(self.res_version)

        with open(hot_update_list_filepath, encoding="utf-8") as f:
            hot_update_list = json.load(f)

        self.hot_update_list = hot_update_list

    def load_manifest(self):
        if Version(self.client_version) < Version("2.5.04"):
            raise NotImplementedError(
                f"version {self.client_version} does not have manifest"
            )

        self.manifest_ab_name = self.hot_update_list["manifestName"]

        self.manifest = get_manifest(
            download_asset(self.res_version, Path(self.manifest_ab_name)).read_bytes(),
            self.client_version,
        )

        dump_table(self.manifest, f"manifest_{self.res_version}_pre.json")

    def load_asset(self, ab_name: str):
        if ab_name in self.asset_dict:
            return

        asset_filepath = download_asset(self.res_version, Path(ab_name))

        asset_env = UnityPy.load(asset_filepath.as_posix())

        self.asset_dict[ab_name] = asset_env

        return asset_env

    def get_asset_env(self, ab_name: str):
        asset_env = self.asset_dict[ab_name]

        return asset_env

    def register_anon_asset_name(self, ab_name: str, asset_env: UnityPy.Environment):
        anon_asset_name_set = get_anon_asset_name_set(asset_env)

        for anon_asset_name in anon_asset_name_set:
            if anon_asset_name not in self.anon_asset_name_dict:
                self.anon_asset_name_dict[anon_asset_name] = set()

            self.anon_asset_name_dict[anon_asset_name].add(ab_name)

    ANCHOR_LEVEL_ID_SET = {
        "level_main_01-07",
        "level_camp_03",
        "level_act3d0_01",
    }

    def build_level_ab_name_set(self):
        self.level_ab_name_set: set[str] = set()

        for anchor_level_id in self.ANCHOR_LEVEL_ID_SET:
            ab_name_set = self.anon_asset_name_dict.get(anchor_level_id, set())
            if len(ab_name_set) != 1:
                raise FileNotFoundError(f"anchor_level_id {anchor_level_id} not found")

            self.level_ab_name_set.add(next(iter(ab_name_set)))

    def load_anon_asset(self) -> set[str]:
        if self.anon_ab_name_set is not None:
            return self.anon_ab_name_set

        self.anon_ab_name_set = set()

        for ab_info in self.hot_update_list["abInfos"]:
            ab_name = ab_info["name"]

            if not ab_name.startswith("anon/"):
                continue

            asset_env = self.load_asset(ab_name)
            self.anon_ab_name_set.add(ab_name)

            self.register_anon_asset_name(ab_name, asset_env)

        self.build_level_ab_name_set()

        return self.anon_ab_name_set

    def mark_modified_asset(self, ab_name: str):
        if ab_name not in self.asset_dict:
            raise KeyError(f"{ab_name} not loaded")

        self.modified_asset_set.add(ab_name)

    def build_mod(self, mod_name: str):
        mod_dirpath = Path(MOD_DIRPATH, mod_name)

        mod_dirpath.mkdir(parents=True, exist_ok=True)

        for ab_name in self.modified_asset_set:
            mod_filepath = (mod_dirpath / escape_ab_name(ab_name)).with_suffix(".dat")
            asset_env = self.asset_dict[ab_name]
            write_mod(mod_filepath, ab_name, asset_env.file.save())

    def mod_table(self, table_prefix: str, mod_table_func, decorator_lst):
        table_ab_name = None
        for anon_asset_name in self.anon_asset_name_dict:
            if anon_asset_name.startswith(table_prefix):
                table_ab_name = next(iter(self.anon_asset_name_dict[anon_asset_name]))
                break

        if table_ab_name is None:
            raise FileNotFoundError(f"{table_prefix} not found")

        table_asset_env = self.get_asset_env(table_ab_name)

        self.mark_modified_asset(table_ab_name)

        data = get_table_data_by_prefix(table_asset_env, table_prefix)

        for decorator in reversed(decorator_lst):
            mod_table_func = decorator(mod_table_func)

        data.m_Script = mod_table_func(data.m_Script)

        data.save()
