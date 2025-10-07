from openbachelorm.resource import Resource
from openbachelorm.manifest import ManifestMerger


def copy_zonemap_node(mgr: ManifestMerger):
    pass


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
