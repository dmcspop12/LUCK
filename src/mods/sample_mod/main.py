from openbachelorm.resource import Resource


def get_ab_name_by_prefix(res: Resource, ab_name_set: set[str], prefix: str):
    for ab_name in ab_name_set:
        asset_env = res.get_asset_env(ab_name)

        for obj in asset_env.objects:
            if obj.type.name == "TextAsset":
                data = obj.read()

                if data.m_Name.startswith(prefix):
                    return ab_name

    return None


def main():
    res = Resource("2.6.41", "25-09-17-05-25-13_d72007")

    ab_name_set = res.load_anon_asset()

    character_table_ab_name = get_ab_name_by_prefix(res, ab_name_set, "character_table")

    if character_table_ab_name is None:
        raise FileNotFoundError("character_table not found")

    character_table_asset_env = res.get_asset_env(character_table_ab_name)

    res.mark_modified_asset(character_table_ab_name)

    res.build_mod("sample_mod")


if __name__ == "__main__":
    main()
