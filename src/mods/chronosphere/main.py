from openbachelorm.resource import Resource
from openbachelorm.manifest import ManifestMerger


def main():
    mgr = ManifestMerger(
        "chronosphere",
        Resource("2.6.41", "25-09-28-12-13-16_6485b3"),
        [
            Resource("2.6.21", "25-08-25-23-45-59_81c7ff"),
            Resource("2.6.01", "25-07-19-05-16-54_1e71a6"),
        ],
    )

    mgr.merge_src_res()

    mgr.prep_merger_bundle()


if __name__ == "__main__":
    main()
