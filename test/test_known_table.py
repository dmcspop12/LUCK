from openbachelorm.resource import Resource
from openbachelorm.helper import (
    nop_mod_table_func,
    get_known_table_decorator_lst,
    is_known_table_available,
)
from openbachelorm.const import KnownTable


def load_known_table(client_version: str, res_version: str):
    res = Resource(client_version, res_version)

    res.load_anon_asset()

    for known_table in KnownTable:
        if not is_known_table_available(known_table, client_version):
            continue
        res.mod_table(
            known_table.value,
            nop_mod_table_func,
            get_known_table_decorator_lst(known_table, client_version, res_version),
        )


def test_known_table():
    load_known_table("2.4.61", "25-03-27-16-19-10-4d4819")
    load_known_table("2.6.41", "25-09-23-16-49-33_52e0bf")
