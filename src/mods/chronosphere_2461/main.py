from openbachelorm.resource import Resource
from openbachelorm.manifest import ManifestMerger


def copy_zonemap_node(mgr: ManifestMerger):
    mgr.copy_merger_tree_node(
        "activity/[uc]act40side/zonemaps/zone_map_act40side_zone1",
        "ui/zonemaps/zone_map_act40side_zone1",
    )
    mgr.copy_merger_tree_node(
        "activity/[uc]act40side/zonemaps/zone_map_act40side_zone2",
        "ui/zonemaps/zone_map_act40side_zone2",
    )
    mgr.copy_merger_tree_node(
        "activity/[uc]act40side/zonemaps/zone_map_act40side_zone3",
        "ui/zonemaps/zone_map_act40side_zone3",
    )

    # ----------

    mgr.copy_merger_tree_node(
        "activity/[uc]act39side/zonemaps/zone_map_act39side_zone1",
        "ui/zonemaps/zone_map_act39side_zone1",
    )
    mgr.copy_merger_tree_node(
        "activity/[uc]act39side/zonemaps/zone_map_act39side_zone2",
        "ui/zonemaps/zone_map_act39side_zone2",
    )

    # ----------

    mgr.copy_merger_tree_node(
        "activity/[uc]act38side/zonemaps/zone_map_act38side_zone1",
        "ui/zonemaps/zone_map_act38side_zone1",
    )
    mgr.copy_merger_tree_node(
        "activity/[uc]act38side/zonemaps/zone_map_act38side_zone2",
        "ui/zonemaps/zone_map_act38side_zone2",
    )
    mgr.copy_merger_tree_node(
        "activity/[uc]act38side/zonemaps/zone_map_act38side_zone3",
        "ui/zonemaps/zone_map_act38side_zone3",
    )


def main():
    mgr = ManifestMerger(
        "chronosphere_2461",
        Resource("2.4.61", "25-03-27-16-19-10-4d4819"),
        [
            Resource("2.4.41", "25-02-19-09-21-28-ba1f4e"),
            Resource("2.4.21", "25-01-08-07-44-44-3d8742"),
            Resource("2.4.01", "24-11-21-11-04-45-bae23b"),
        ],
    )

    mgr.merge_src_res()

    copy_zonemap_node(mgr)

    mgr.prep_merger_bundle()

    mgr.migrate_level()

    mgr.build_mod()


if __name__ == "__main__":
    main()
