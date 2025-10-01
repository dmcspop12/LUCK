from functools import wraps

import flatbuffers

from .fbs_codegen.v2_6_41 import (
    prts___levels_generated as prts___levels_v2_6_41,
)
from .fbs_codegen.v2_6_21 import (
    prts___levels_generated as prts___levels_v2_6_21,
)
from .fbs_codegen.v2_6_01 import (
    prts___levels_generated as prts___levels_v2_6_01,
)
from .fbs_codegen.v2_5_80 import (
    prts___levels_generated as prts___levels_v2_5_80,
)
from .fbs_codegen.v2_5_60 import (
    prts___levels_generated as prts___levels_v2_5_60,
)
from .fbs_codegen.v2_5_04 import (
    prts___levels_generated as prts___levels_v2_5_04,
)
from .fbs_codegen.v2_4_61 import (
    prts___levels_generated as prts___levels_v2_4_61,
)


from .helper import (
    script_decorator,
    header_decorator,
    json_decorator,
    dump_table_decorator,
    encode_flatc,
    decode_flatc,
    nop_mod_table_func,
    get_mod_level_decorator_lst,
    apply_decorator_lst,
)


def get_prts___levels(client_version: str):
    match client_version:
        case "2.6.41":
            return prts___levels_v2_6_41

        case "2.6.21":
            return prts___levels_v2_6_21

        case "2.6.01":
            return prts___levels_v2_6_01

        case "2.5.80":
            return prts___levels_v2_5_80

        case "2.5.60":
            return prts___levels_v2_5_60

        case "2.5.04":
            return prts___levels_v2_5_04

        case "2.4.61":
            return prts___levels_v2_4_61

        case _:
            raise ValueError(f"fbs codegen not found for {client_version}")


def migrate_flatc_decorator(
    src_client_version: str, dst_client_version: str, fbs_name: str
):
    def _migrate_flatc_decorator(func):
        @wraps(func)
        def wrapper(data):
            return encode_flatc(
                func(
                    decode_flatc(
                        data,
                        src_client_version,
                        fbs_name,
                    )
                ),
                dst_client_version,
                fbs_name,
            )

        return wrapper

    return _migrate_flatc_decorator


def get_migrate_level_decorator_lst(
    level_id: str, src_client_version: str, dst_client_version: str, res_version: str
):
    return [
        script_decorator,
        header_decorator,
        migrate_flatc_decorator(
            src_client_version, dst_client_version, "prts___levels"
        ),
        json_decorator,
        dump_table_decorator(f"{level_id}_{res_version}_migrate"),
    ]


def get_codegen_migrate_level_decorator_lst():
    return [
        script_decorator,
        header_decorator,
    ]


def recursive_handle_clz_Torappu_EnemyDatabase_AttributesDataT(
    obj,
    clz_Torappu_EnemyDatabase_AttributesDataT,
    prts___levels,
):
    if isinstance(obj, clz_Torappu_EnemyDatabase_AttributesDataT):
        if hasattr(obj, "palsyImmune") and obj.palsyImmune is None:
            obj.palsyImmune = prts___levels.clz_Torappu_Undefinable_1_System_Boolean_T()

        if hasattr(obj, "attractImmune") and obj.attractImmune is None:
            obj.attractImmune = (
                prts___levels.clz_Torappu_Undefinable_1_System_Boolean_T()
            )

        if hasattr(obj, "epBreakRecoverSpeed") and obj.epBreakRecoverSpeed is None:
            obj.epBreakRecoverSpeed = (
                prts___levels.clz_Torappu_Undefinable_1_System_Single_T()
            )

        return

    if isinstance(obj, list):
        for i in obj:
            recursive_handle_clz_Torappu_EnemyDatabase_AttributesDataT(
                i,
                clz_Torappu_EnemyDatabase_AttributesDataT,
                prts___levels,
            )
        return

    if not hasattr(obj, "__dict__"):
        return

    for i in obj.__dict__.values():
        recursive_handle_clz_Torappu_EnemyDatabase_AttributesDataT(
            i,
            clz_Torappu_EnemyDatabase_AttributesDataT,
            prts___levels,
        )


def get_codegen_migrate_func(
    dst_client_version: str,
):
    def _codegen_migrate_func(level_bytes: bytes) -> bytes:
        prts___levels = get_prts___levels(dst_client_version)

        level_obj = prts___levels.clz_Torappu_LevelDataT.InitFromPackedBuf(level_bytes)

        clz_Torappu_EnemyDatabase_AttributesDataT = (
            prts___levels.clz_Torappu_EnemyDatabase_AttributesDataT
        )

        recursive_handle_clz_Torappu_EnemyDatabase_AttributesDataT(
            level_obj,
            clz_Torappu_EnemyDatabase_AttributesDataT,
            prts___levels,
        )

        builder = flatbuffers.Builder()
        builder.Finish(level_obj.Pack(builder))
        level_bytes = bytes(builder.Output())

        return level_bytes

    return _codegen_migrate_func


def migrate_level(
    level_id: str,
    src_client_version: str,
    dst_client_version: str,
    res_version: str,
    level_str: str,
) -> str:
    migrate_level_decorator_lst = get_migrate_level_decorator_lst(
        level_id, src_client_version, dst_client_version, res_version
    )

    migrate_func = nop_mod_table_func

    migrate_func = apply_decorator_lst(migrate_func, migrate_level_decorator_lst)

    level_str = migrate_func(level_str)

    # ----------

    codegen_migrate_level_decorator_lst = get_codegen_migrate_level_decorator_lst()

    codegen_migrate_func = get_codegen_migrate_func(dst_client_version)

    codegen_migrate_func = apply_decorator_lst(
        codegen_migrate_func, codegen_migrate_level_decorator_lst
    )

    level_str = codegen_migrate_func(level_str)

    # ----------

    log_decorator_lst = get_mod_level_decorator_lst(
        level_id, dst_client_version, res_version
    )

    log_func = nop_mod_table_func

    log_func = apply_decorator_lst(log_func, log_decorator_lst)

    level_str = log_func(level_str)

    return level_str
