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


def debug_dump(character_table):
    with open(
        Path(
            TMP_DIRPATH,
            "sample_mod.json",
        ),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            character_table,
            f,
            ensure_ascii=False,
            indent=4,
        )


def sample_mod(character_table):
    for char in character_table["characters"]:
        if char["key"] == "char_1035_wisdel":
            data = char["value"]["phases"][-1]["attributesKeyFrames"][-1]["data"]

            data["maxHp"] *= 100
            data["atk"] *= 100


def main():
    res = Resource("2.6.41", "25-09-17-05-25-13_d72007")

    res.load_anon_asset()

    character_table_prefix = "character_table"

    character_table_ab_name = None
    for anon_asset_name in res.anon_asset_name_dict:
        if anon_asset_name.startswith(character_table_prefix):
            character_table_ab_name = res.anon_asset_name_dict[anon_asset_name]
            break

    if character_table_ab_name is None:
        raise FileNotFoundError(f"{character_table_prefix} not found")

    character_table_asset_env = res.get_asset_env(character_table_ab_name)

    res.mark_modified_asset(character_table_ab_name)

    data = get_data_by_prefix(character_table_asset_env, character_table_prefix)

    script_bytes = remove_header(script_to_bytes(data.m_Script))

    character_table_str = decode_flatc(
        script_bytes, res.client_version, character_table_prefix
    )
    character_table = json.loads(character_table_str)

    sample_mod(character_table)

    debug_dump(character_table)

    new_character_table_str = json.dumps(character_table)

    new_script_bytes = encode_flatc(
        new_character_table_str, res.client_version, character_table_prefix
    )

    data.m_Script = bytes_to_script(add_header(new_script_bytes))

    data.save()

    res.build_mod("sample_mod")


if __name__ == "__main__":
    main()
