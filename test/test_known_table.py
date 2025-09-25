from openbachelorm.resource import Resource
from openbachelorm.helper import nop_mod_table_func, get_known_table_decorator_lst
from openbachelorm.const import KnownTable


def load_known_table(client_version: str, res_version: str):
    res = Resource(client_version, res_version)

    res.load_anon_asset()

    for known_table in KnownTable:
        res.mod_table(
            known_table.value,
            nop_mod_table_func,
            get_known_table_decorator_lst(known_table, client_version, res_version),
        )


def test_known_table():
    load_known_table("2.6.41", "25-09-23-16-49-33_52e0bf")
