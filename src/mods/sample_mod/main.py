from pathlib import Path
import json

import UnityPy

from openbachelorm.resource import Resource
from openbachelorm.helper import (
    script_decorator,
    header_decorator,
    flatc_decorator,
    json_decorator,
    dump_table_decorator,
)


def get_data_by_prefix(asset_env: UnityPy.Environment, prefix: str):
    for obj in asset_env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()

            if data.m_Name.startswith(prefix):
                return data

    return None


def mod_table(res: Resource, prefix: str, do_mod_func, decorator_lst):
    table_ab_name = None
    for anon_asset_name in res.anon_asset_name_dict:
        if anon_asset_name.startswith(prefix):
            table_ab_name = next(iter(res.anon_asset_name_dict[anon_asset_name]))
            break

    if table_ab_name is None:
        raise FileNotFoundError(f"{prefix} not found")

    table_asset_env = res.get_asset_env(table_ab_name)

    res.mark_modified_asset(table_ab_name)

    data = get_data_by_prefix(table_asset_env, prefix)

    for decorator in reversed(decorator_lst):
        do_mod_func = decorator(do_mod_func)

    data.m_Script = do_mod_func(data.m_Script)

    data.save()


def do_mod_character_table(character_table):
    for char in character_table["characters"]:
        if char["key"] == "char_1035_wisdel":
            data = char["value"]["phases"][-1]["attributesKeyFrames"][-1]["data"]

            data["maxHp"] *= 100
            data["atk"] *= 100

            data["cost"] = 1

    return character_table


def do_mod_skill_table(skill_table):
    for skill in skill_table["skills"]:
        if skill["key"] == "skchr_wisdel_3":
            data = skill["value"]["levels"][-1]

            data["spData"]["spCost"] = 1

    return skill_table


def build_sample_mod(client_version: str, res_version: str):
    res = Resource(client_version, res_version)

    res.load_anon_asset()

    mod_table(
        res,
        "character_table",
        do_mod_character_table,
        [
            script_decorator,
            header_decorator,
            flatc_decorator(client_version, "character_table"),
            json_decorator,
            dump_table_decorator("character_table"),
        ],
    )
    mod_table(
        res,
        "skill_table",
        do_mod_skill_table,
        [
            script_decorator,
            header_decorator,
            flatc_decorator(client_version, "skill_table"),
            json_decorator,
            dump_table_decorator("skill_table"),
        ],
    )

    res.build_mod("sample_mod")


def main():
    build_sample_mod("2.6.41", "25-09-17-05-25-13_d72007")


if __name__ == "__main__":
    main()
