from dataclasses import dataclass, field
from copy import deepcopy
from pathlib import Path
import shutil

from anytree import Node, PreOrderIter

from .resource import Resource
from .const import TMP_DIRPATH
from .helper import download_asset


@dataclass
class ManifestBundle:
    name: str
    props: int
    sccIndex: int
    allDependencies: list[int]

    manifest: "ManifestManager"

    dep_on_lst: list["ManifestBundle"] = field(default_factory=list)


@dataclass
class ManifestAsset:
    assetName: str
    bundleIndex: int
    name: str
    path: str

    manifest: "ManifestManager"

    bundle: "ManifestBundle"


def download_bundle(bundle: ManifestBundle) -> Path:
    return download_asset(bundle.manifest.resource.res_version, bundle.name)


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


def get_node_by_path(root: Node, path: str) -> Node:
    node = root
    for i in Path(path).parts:
        if not node.is_dir:
            raise KeyError(f"{get_node_path(node)} not a dir")
        if i not in node.child_dict:
            return None

        node = node.child_dict[i]

    if node.is_dir:
        raise KeyError(f"{get_node_path(node)} not a file")

    return node


def is_file_in_tree(root: Node, path: str) -> bool:
    node = get_node_by_path(root, path)
    if node is None:
        return False
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
                manifest=self,
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
            bundle_idx = asset_dict.get("bundleIndex", 0)
            asset = ManifestAsset(
                assetName=asset_dict.get("assetName"),
                bundleIndex=bundle_idx,
                name=asset_dict.get("name"),
                path=asset_dict.get("path"),
                manifest=self,
                bundle=self.bundle_lst[bundle_idx],
            )

            if not asset.path:
                self.dangling_asset_lst.append(asset)
                continue

            add_file_to_tree(self.asset_tree_root, asset.path, asset=asset)

        dump_tree(self.asset_tree_root, f"asset_tree_{self.resource.res_version}.txt")


@dataclass
class MergerBundle:
    bundle: "ManifestBundle"

    dep_bundle_name_lst: list[str] = field(default_factory=list)


MERGER_TREE_ROOT_NAME = "openbachelorm"


class ManifestMerger:
    def __init__(
        self, mod_name: str, target_res: Resource, src_res_lst: list[Resource]
    ):
        self.mod_name = mod_name

        self.target_res = target_res
        self.src_res_lst = src_res_lst

        self.target_res_manager = ManifestManager(target_res)
        self.src_res_manager_lst = [ManifestManager(i) for i in src_res_lst]

        self.merger_tree_root = new_dir_node(MERGER_TREE_ROOT_NAME)
        self.merger_bundle_dict: dict[str, MergerBundle] = {}

    def recursive_add_bundle(self, bundle: ManifestBundle):
        if bundle.name in self.target_res_manager.bundle_dict:
            return

        if bundle.name in self.merger_bundle_dict:
            return

        merger_bundle = MergerBundle(
            bundle=bundle,
        )

        for dep_on in bundle.dep_on_lst:
            merger_bundle.dep_bundle_name_lst.append(dep_on.name)

        self.merger_bundle_dict[bundle.name] = merger_bundle

        for dep_on in bundle.dep_on_lst:
            self.recursive_add_bundle(dep_on)

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
                bundle_name=node.asset.bundle.name,
            )

            self.recursive_add_bundle(node.asset.bundle)

    def merge_src_res(self):
        for src_res_manager in self.src_res_manager_lst:
            self.merge_single_src_res(src_res_manager)

    def copy_merger_tree_node(self, src_path: str, dst_path: str):
        src_node = get_node_by_path(self.merger_tree_root, src_path)

        add_file_to_tree(
            self.merger_tree_root,
            dst_path,
            asset=src_node.asset,
            bundle_name=src_node.bundle_name,
        )

    def get_merger_bundle_filepath(self, bundle_name: str):
        return Path(TMP_DIRPATH, self.mod_name, bundle_name)

    def prep_merger_bundle(self):
        for bundle_name, merger_bundle in self.merger_bundle_dict.items():
            bundle_filepath = download_bundle(merger_bundle.bundle)

            merger_bundle_filepath = self.get_merger_bundle_filepath(bundle_name)

            merger_bundle_filepath.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(bundle_filepath, merger_bundle_filepath)

    def build_mod_bundle_get_next_scc_idx(self):
        max_scc_idx = -1
        for bundle in self.target_res_manager.bundle_lst:
            max_scc_idx = max(max_scc_idx, bundle.sccIndex)

        return max_scc_idx + 1

    def build_mod_bundle_init_bundle_idx_dict(self):
        self.bundle_idx_dict: dict[str, int] = {}

        for i, bundle_obj in enumerate(self.new_manifest["bundles"]):
            self.bundle_idx_dict[bundle_obj["name"]] = i

    def build_mod_bundle(self):
        next_scc_idx = self.build_mod_bundle_get_next_scc_idx()

        for bundle_name, merger_bundle in self.merger_bundle_dict.items():
            merger_bundle_filepath = self.get_merger_bundle_filepath(bundle_name)

            self.target_res.register_foreign_asset(bundle_name, merger_bundle_filepath)

            bundle = merger_bundle.bundle

            self.new_manifest["bundles"].append(
                {
                    "name": bundle_name,
                    "props": bundle.props,
                    "sccIndex": next_scc_idx,
                }
            )

            next_scc_idx += 1

        self.build_mod_bundle_init_bundle_idx_dict()

        for bundle_name, merger_bundle in self.merger_bundle_dict.items():
            bundle_idx = self.bundle_idx_dict[bundle_name]

            self.new_manifest["bundles"][bundle_idx]["allDependencies"] = [
                self.bundle_idx_dict[i] for i in merger_bundle.dep_bundle_name_lst
            ]

    def build_mod_asset(self):
        for node in PreOrderIter(self.merger_tree_root):
            if node.is_dir:
                continue

            path = get_node_path(node)
            path_obj = Path(path)

            self.new_manifest["assetToBundleList"].append(
                {
                    "assetName": Path(*path_obj.parts[1:]).with_suffix("").as_posix(),
                    "bundleIndex": self.bundle_idx_dict[node.bundle_name],
                    "name": path_obj.with_suffix("").name,
                    "path": path,
                },
            )

    def build_mod(self):
        dump_tree(
            self.merger_tree_root,
            f"merger_tree_{self.target_res.res_version}.txt",
        )

        self.new_manifest = deepcopy(self.target_res.manifest)

        self.build_mod_bundle()
        self.build_mod_asset()

        self.target_res.mark_manifest(self.new_manifest)

        self.target_res.build_mod(self.mod_name)
