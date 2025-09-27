from openbachelorm.resource import Resource
from openbachelorm.helper import (
    nop_mod_table_func,
    get_known_table_decorator_lst,
    is_known_table_available,
    get_known_table_asset_name_prefix,
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
            table_asset_name_prefix=get_known_table_asset_name_prefix(known_table),
        )


def test_known_table():
    load_known_table("2.4.61", "25-03-27-16-19-10-4d4819")
    load_known_table("2.5.04", "25-04-25-08-42-16_acb2f8")
    load_known_table("2.5.60", "25-05-20-12-36-22_4803e1")
    load_known_table("2.5.80", "25-06-26-04-47-55_47709b")
    load_known_table("2.6.01", "25-07-19-05-16-54_1e71a6")
    load_known_table("2.6.21", "25-08-25-23-45-59_81c7ff")
    load_known_table("2.6.41", "25-09-23-16-49-33_52e0bf")
