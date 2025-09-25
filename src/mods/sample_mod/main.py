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
    crypt_decorator,
    encoding_decorator,
)


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


def do_mod_range_table(range_table):
    range_table["3-9"]["grids"] = []

    for row in range(4, -5, -1):
        for col in range(0, 7):
            range_table["3-9"]["grids"].append(
                {
                    "row": row,
                    "col": col,
                },
            )

    return range_table


def build_sample_mod(client_version: str, res_version: str):
    res = Resource(client_version, res_version)

    res.load_anon_asset()

    res.mod_table(
        "character_table",
        do_mod_character_table,
        [
            script_decorator,
            header_decorator,
            flatc_decorator(client_version, "character_table"),
            json_decorator,
            dump_table_decorator(f"character_table_{res_version}"),
        ],
    )
    res.mod_table(
        "skill_table",
        do_mod_skill_table,
        [
            script_decorator,
            header_decorator,
            flatc_decorator(client_version, "skill_table"),
            json_decorator,
            dump_table_decorator(f"skill_table_{res_version}"),
        ],
    )
    res.mod_table(
        "range_table",
        do_mod_range_table,
        [
            script_decorator,
            header_decorator,
            crypt_decorator,
            encoding_decorator,
            json_decorator,
            dump_table_decorator(f"range_table_{res_version}"),
        ],
    )

    res.build_mod("sample_mod")


def main():
    build_sample_mod("2.6.41", "25-09-17-05-25-13_d72007")


if __name__ == "__main__":
    main()
