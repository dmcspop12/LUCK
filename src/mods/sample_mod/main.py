from pathlib import Path
import json

import UnityPy

from openbachelorm.resource import Resource
from openbachelorm.helper import (
    script_to_bytes,
    bytes_to_script,
    remove_header,
    add_header,
    decode_flatc,
    encode_flatc,
)
from openbachelorm.const import TMP_DIRPATH


def get_data_by_prefix(asset_env: UnityPy.Environment, prefix: str):
    for obj in asset_env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()

            if data.m_Name.startswith(prefix):
                return data

    return None


def debug_dump(table, prefix: str):
    with open(
        Path(
            TMP_DIRPATH,
            f"sample_mod_{prefix}.json",
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


def mod_table(res: Resource, prefix: str, do_mod_func):
    table_ab_name = None
    for anon_asset_name in res.anon_asset_name_dict:
        if anon_asset_name.startswith(prefix):
            table_ab_name = res.anon_asset_name_dict[anon_asset_name]
            break

    if table_ab_name is None:
        raise FileNotFoundError(f"{prefix} not found")

    table_asset_env = res.get_asset_env(table_ab_name)

    res.mark_modified_asset(table_ab_name)

    data = get_data_by_prefix(table_asset_env, prefix)

    script_bytes = remove_header(script_to_bytes(data.m_Script))

    table_str = decode_flatc(script_bytes, res.client_version, prefix)
    table = json.loads(table_str)

    do_mod_func(table)

    debug_dump(table, prefix)

    new_table_str = json.dumps(table)

    new_script_bytes = encode_flatc(new_table_str, res.client_version, prefix)

    data.m_Script = bytes_to_script(add_header(new_script_bytes))

    data.save()


def do_mod_character_table(character_table):
    for char in character_table["characters"]:
        if char["key"] == "char_1035_wisdel":
            data = char["value"]["phases"][-1]["attributesKeyFrames"][-1]["data"]

            data["maxHp"] *= 100
            data["atk"] *= 100


def main():
    res = Resource("2.6.41", "25-09-17-05-25-13_d72007")

    res.load_anon_asset()

    mod_table(res, "character_table", do_mod_character_table)

    res.build_mod("sample_mod")


if __name__ == "__main__":
    main()
