from dataclasses import dataclass, field
from copy import deepcopy
from pathlib import Path

from anytree import Node, RenderTree

from .resource import Resource
from .const import TMP_DIRPATH


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

    bundle: "ManifestBundle" = None


def add_node_to_parent(parent: Node, name: str, node: Node):
    if parent is not None:
        if not parent.is_dir:
            raise KeyError(f"{parent} not a dir")
        if name in parent.child_dict:
            raise KeyError(f"{node} already exist")
        parent.child_dict[name] = node


def new_dir_node(dir_name: str, parent: Node = None) -> Node:
    node = Node(dir_name, parent=parent, is_dir=True, child_dict={})
    add_node_to_parent(parent, dir_name, node)
    return node


def new_file_node(file_name: str, asset: ManifestAsset, parent: Node = None):
    node = Node(file_name, parent=parent, is_dir=False, asset=asset)
    add_node_to_parent(parent, file_name, node)
    return node


def create_child_node_if_necessary(node: Node, child_name: str) -> Node:
    if not node.is_dir:
        raise KeyError(f"{node} not a dir")

    if child_name not in node.child_dict:
        child = new_dir_node(child_name, node)
    else:
        child = node.child_dict[child_name]

    return child


def dump_tree(root: Node, filename: str):
    tree_filepath = Path(
        TMP_DIRPATH,
        filename,
    )
    with open(tree_filepath, "w", encoding="utf-8") as f:
        for row in RenderTree(root):
            print(f"{row.pre}{row.node.name}", file=f)


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
        self.bundle_dict: dict[str, ManifestBundle] = {}

        for bundle_dict in self.manifest["bundles"]:
            bundle = ManifestBundle(
                name=bundle_dict.get("name"),
                props=bundle_dict.get("props", 0),
                sccIndex=bundle_dict.get("sccIndex", 0),
                allDependencies=deepcopy(bundle_dict.get("allDependencies")),
            )

            self.bundle_lst.append(bundle)
            self.bundle_dict[bundle.name] = bundle

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

        asset_node = new_file_node(asset_path.name, asset, cur_node)

        return asset_node

    def build_asset_tree(self):
        self.asset_tree_root = new_dir_node(ASSET_TREE_ROOT_NAME)
        self.dangling_asset_lst: list[ManifestAsset] = []

        for asset_dict in self.manifest["assetToBundleList"]:
            asset = ManifestAsset(
                assetName=asset_dict.get("assetName"),
                bundleIndex=asset_dict.get("bundleIndex", 0),
                name=asset_dict.get("name"),
                path=asset_dict.get("path"),
            )

            asset.bundle = self.bundle_lst[asset.bundleIndex]

            if not asset.path:
                self.dangling_asset_lst.append(asset)
                continue

            self.add_to_asset_tree(asset)

        dump_tree(self.asset_tree_root, f"asset_tree_{self.resource.res_version}.txt")
