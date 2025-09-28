from dataclasses import dataclass, field
from copy import deepcopy

from anytree import Node

from .resource import Resource


@dataclass
class ManifestBundle:
    name: str
    props: int
    sccIndex: int
    allDependencies: list[int]

    dep_on_lst: list["ManifestBundle"] = field(default_factory=list)


@dataclass
class ManifestAsset:
    assetName: str
    bundleIndex: int
    name: str
    path: str


ASSET_TREE_ROOT_NAME = "openbachelorm"


class ManifestManager:
    def __init__(self, res: Resource):
        self.resource = res

        res.load_manifest()

        self.manifest = res.manifest

        self.build_bundle_lst()
        self.build_asset_tree()

    def build_bundle_lst(self):
        self.bundle_lst: list[ManifestBundle] = []

        for bundle_dict in self.manifest["bundles"]:
            bundle = ManifestBundle(
                name=bundle_dict.get("name"),
                props=bundle_dict.get("props", 0),
                sccIndex=bundle_dict.get("sccIndex", 0),
                allDependencies=deepcopy(bundle_dict.get("allDependencies")),
            )

            self.bundle_lst.append(bundle)

        for bundle in self.bundle_lst:
            if not bundle.allDependencies:
                continue

            for i in bundle.allDependencies:
                bundle.dep_on_lst.append(self.bundle_lst[i])

    def build_asset_tree(self):
        self.asset_tree_root = Node(ASSET_TREE_ROOT_NAME, is_dir=True)
        self.dangling_asset_lst: list[ManifestAsset] = []

        for asset_dict in self.manifest["assetToBundleList"]:
            asset = ManifestAsset(
                assetName=asset_dict.get("assetName"),
                bundleIndex=asset_dict.get("bundleIndex", 0),
                name=asset_dict.get("name"),
                path=asset_dict.get("path"),
            )

            if not asset.path:
                self.dangling_asset_lst.append(asset)
                continue
