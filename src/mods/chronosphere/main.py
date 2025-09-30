from openbachelorm.resource import Resource
from openbachelorm.manifest import ManifestMerger


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

    mgr.prep_merger_bundle()

    mgr.build_mod()


if __name__ == "__main__":
    main()
