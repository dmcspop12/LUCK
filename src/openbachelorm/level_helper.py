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
