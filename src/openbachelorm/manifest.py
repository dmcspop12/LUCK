from dataclasses import dataclass, field
from copy import deepcopy
from pathlib import Path

from anytree import Node, PreOrderIter

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


def get_node_path(node: Node) -> str:
    return "/".join([i.name for i in node.path[1:]])


def add_node_to_parent(parent: Node, name: str, node: Node):
    if parent is not None:
        if not parent.is_dir:
            raise KeyError(f"{get_node_path(parent)} not a dir")
        if name in parent.child_dict:
            raise KeyError(f"{get_node_path(node)} already exist")
        parent.child_dict[name] = node


def new_dir_node(dir_name: str, parent: Node = None) -> Node:
    node = Node(dir_name, parent=parent, is_dir=True, child_dict={})
    add_node_to_parent(parent, dir_name, node)
    return node


def new_file_node(file_name: str, parent: Node = None, **kwargs):
    node = Node(file_name, parent=parent, is_dir=False, **kwargs)
    add_node_to_parent(parent, file_name, node)
    return node


def is_file_in_tree(root: Node, path: str) -> bool:
    node = root
    for i in Path(path).parts:
        if not node.is_dir:
            raise KeyError(f"{get_node_path(node)} not a dir")
        if i not in node.child_dict:
            return False

        node = node.child_dict[i]

    if node.is_dir:
        raise KeyError(f"{get_node_path(node)} not a file")

    return True


def create_child_node_if_necessary(node: Node, child_name: str) -> Node:
    if not node.is_dir:
        raise KeyError(f"{get_node_path(node)} not a dir")

    if child_name not in node.child_dict:
        child = new_dir_node(child_name, node)
    else:
        child = node.child_dict[child_name]

    return child


def add_file_to_tree(root: Node, path: str, **kwargs) -> Node:
    path_obj = Path(path)

    node = root

    for dir_name in path_obj.parent.parts:
        node = create_child_node_if_necessary(node, dir_name)

    node = new_file_node(path_obj.name, node, **kwargs)

    return node


def dump_tree(root: Node, filename: str):
    tree_filepath = Path(
        TMP_DIRPATH,
        filename,
    )
    indent = "    "
    with open(tree_filepath, "w", encoding="utf-8") as f:
        for node in PreOrderIter(root):
            print(f"{indent * node.depth}{node.name}", file=f)


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

            add_file_to_tree(self.asset_tree_root, asset.path, asset=asset)

        dump_tree(self.asset_tree_root, f"asset_tree_{self.resource.res_version}.txt")


MERGER_TREE_ROOT_NAME = "openbachelorm"


class ManifestMerger:
    def __init__(self, target_res: Resource, src_res_lst: list[Resource]):
        self.target_res = target_res
        self.src_res_lst = src_res_lst

        self.target_res_manager = ManifestManager(target_res)
        self.src_res_manager_lst = [ManifestManager(i) for i in src_res_lst]

        self.merger_tree_root = new_dir_node(MERGER_TREE_ROOT_NAME)

    def merge_single_src_res(self, src_res_manager: ManifestManager):
        for node in PreOrderIter(src_res_manager.asset_tree_root):
            if node.is_dir:
                continue

            path = get_node_path(node)

            if is_file_in_tree(self.target_res_manager.asset_tree_root, path):
                continue

            if is_file_in_tree(self.merger_tree_root, path):
                continue

            add_file_to_tree(
                self.merger_tree_root,
                path,
                asset=node.asset,
                src_res_manager=src_res_manager,
            )

    def merge_src_res(self):
        for src_res_manager in self.src_res_manager_lst:
            self.merge_single_src_res(src_res_manager)

        dump_tree(
            self.merger_tree_root,
            f"merger_tree_{self.target_res.res_version}.txt",
        )
