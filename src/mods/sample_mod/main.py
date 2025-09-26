from openbachelorm.resource import Resource
from openbachelorm.helper import (
    get_known_table_decorator_lst,
    get_mod_level_decorator_lst,
)
from openbachelorm.const import KnownTable


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
        for col in range(-6, 7):
            range_table["3-9"]["grids"].append(
                {
                    "row": row,
                    "col": col,
                },
            )

    return range_table


def do_mod_level(level):
    return level


def build_sample_mod(client_version: str, res_version: str):
    res = Resource(client_version, res_version)

    res.load_anon_asset()

    res.mod_table(
        KnownTable.CHARACTER_TABLE.value,
        do_mod_character_table,
        get_known_table_decorator_lst(
            KnownTable.CHARACTER_TABLE, client_version, res_version
        ),
    )
    res.mod_table(
        KnownTable.SKILL_TABLE.value,
        do_mod_skill_table,
        get_known_table_decorator_lst(
            KnownTable.SKILL_TABLE, client_version, res_version
        ),
    )
    res.mod_table(
        KnownTable.RANGE_TABLE.value,
        do_mod_range_table,
        get_known_table_decorator_lst(
            KnownTable.RANGE_TABLE, client_version, res_version
        ),
    )
    res.mod_level(
        "level_main_00-01",
        do_mod_level,
        get_mod_level_decorator_lst("level_main_00-01", client_version, res_version),
    )

    res.build_mod("sample_mod")


def main():
    build_sample_mod("2.6.41", "25-09-23-16-49-33_52e0bf")


if __name__ == "__main__":
    main()
