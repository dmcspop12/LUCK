from enum import StrEnum

TMP_DIRPATH = "tmp/"

ASSET_DIRPATH = "asset/"

MOD_DIRPATH = "mod/"


class KnownTable(StrEnum):
    CHARACTER_TABLE = "character_table"
    SKILL_TABLE = "skill_table"
    RANGE_TABLE = "range_table"
