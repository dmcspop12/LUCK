from openbachelorm.resource import Resource
from openbachelorm.manifest import ManifestMerger


def copy_zonemap_node(mgr: ManifestMerger):
    mgr.copy_merger_tree_node(
        "activity/[uc]act42side/zonemaps/zone_map_act42side_zone1",
        "ui/zonemaps/zone_map_act42side_zone1",
    )
    mgr.copy_merger_tree_node(
        "activity/[uc]act42side/zonemaps/zone_map_act42side_zone2",
        "ui/zonemaps/zone_map_act42side_zone2",
    )
    mgr.copy_merger_tree_node(
        "activity/[uc]act42side/zonemaps/zone_map_act42side_zone3",
        "ui/zonemaps/zone_map_act42side_zone3",
    )

    # ----------

    mgr.copy_merger_tree_node(
        "activity/[uc]act43side/zonemaps/zone_map_act43side_zone1",
        "ui/zonemaps/zone_map_act43side_zone1",
    )
    mgr.copy_merger_tree_node(
        "activity/[uc]act43side/zonemaps/zone_map_act43side_zone2",
        "ui/zonemaps/zone_map_act43side_zone2",
    )

    # ----------

    mgr.copy_merger_tree_node(
        "activity/[uc]act19mini/zonemaps/zone_map_act19mini_zone1",
        "ui/zonemaps/zone_map_act19mini_zone1",
    )

    # ----------

    # mgr.copy_merger_tree_node(
    #     "activity/[uc]act44side/zonemaps/zone_map_act44side_zone1",
    #     "ui/zonemaps/zone_map_act44side_zone1",
    # )
    # mgr.copy_merger_tree_node(
    #     "activity/[uc]act44side/zonemaps/zone_map_act44side_zone2",
    #     "ui/zonemaps/zone_map_act44side_zone2",
    # )
    # mgr.copy_merger_tree_node(
    #     "activity/[uc]act44side/zonemaps/zone_map_act44side_zone3",
    #     "ui/zonemaps/zone_map_act44side_zone3",
    # )


def main():
    mgr = ManifestMerger(
        "chronosphere",
        Resource("2.6.41", "25-09-28-12-13-16_6485b3"),
        [
            Resource("2.6.21", "25-08-25-23-45-59_81c7ff"),
            Resource("2.6.01", "25-07-19-05-16-54_1e71a6"),
            Resource("2.5.80", "25-06-26-04-47-55_47709b"),
            Resource("2.5.60", "25-05-20-12-36-22_4803e1"),
            Resource("2.5.04", "25-04-25-08-42-16_acb2f8"),
        ],
    )

    mgr.merge_src_res()

    copy_zonemap_node(mgr)

    mgr.merge_special_anon_bundle()

    mgr.prep_merger_bundle()

    mgr.migrate_level()

    mgr.build_mod()


if __name__ == "__main__":
    main()
