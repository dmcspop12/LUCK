from dataclasses import dataclass, field
from copy import deepcopy
from pathlib import Path

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


def create_child_node_if_necessary(node: Node, child_name: str) -> Node:
    for child in node.children:
        if child.name == child_name:
            if not child.is_dir:
                print(f"warn: file {child} used as folder")
            return child

    child = Node(child_name, parent=node, is_dir=True)

    return child


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

    def add_to_asset_tree(self, asset: ManifestAsset):
        asset_path = Path(asset.path)

        cur_node = self.asset_tree_root

        for dir_name in asset_path.parent.parts:
            cur_node = create_child_node_if_necessary(cur_node, dir_name)

        for child in cur_node.children:
            if child.name == asset_path.name:
                print(f"warn: {asset_path} already added")

        asset_node = Node(asset_path.name, parent=cur_node, is_dir=False, asset=asset)

        return asset_node

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

            self.add_to_asset_tree(asset)
