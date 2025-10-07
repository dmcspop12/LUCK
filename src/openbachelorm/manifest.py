from dataclasses import dataclass, field
from copy import deepcopy
from pathlib import Path
import shutil
import random
from packaging.version import Version


from anytree import Node, PreOrderIter
from UnityPy import Environment
from UnityPy.files import SerializedFile
import UnityPy

from .resource import Resource
from .const import TMP_DIRPATH
from .helper import download_asset
from .level_helper import migrate_level


@dataclass
class ManifestBundle:
    name: str
    props: int
    sccIndex: int
    allDependencies: list[int]

    isCacheable: bool
    directDependencies: list[int]

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


def get_node_by_path(root: Node, path: str, dir_ok=False) -> Node:
    node = root
    for i in Path(path).parts:
        if not node.is_dir:
            raise KeyError(f"{get_node_path(node)} not a dir")
        if i not in node.child_dict:
            return None

        node = node.child_dict[i]

    if not dir_ok and node.is_dir:
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


PSEUDO_ASSET_SUFFIX = ".openbachelorm"


def get_asset_path(asset_name: str):
    return f"{asset_name}{PSEUDO_ASSET_SUFFIX}"


ASSET_TREE_ROOT_NAME = "openbachelorm"


class ManifestManager:
    def __init__(self, res: Resource):
        self.resource = res

        if Version(res.client_version) > Version("2.4.61"):
            self.is_legacy_unity = False
        else:
            self.is_legacy_unity = True

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
                isCacheable=bundle_dict.get("isCacheable", False),
                directDependencies=deepcopy(bundle_dict.get("directDependencies")),
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

            if not asset.assetName:
                self.dangling_asset_lst.append(asset)
                continue

            asset_path = get_asset_path(asset.assetName)

            add_file_to_tree(self.asset_tree_root, asset_path, asset=asset)

        dump_tree(self.asset_tree_root, f"asset_tree_{self.resource.res_version}.txt")


def get_special_anon_bundle(mgr: ManifestManager) -> ManifestBundle:
    return mgr.bundle_dict["arts/clue_hub.ab"].dep_on_lst[0]


def get_special_anon_bundle_serialized_file(env: Environment):
    serialized_file_obj: SerializedFile = env.assets[0]
    return serialized_file_obj


MIN_INT32 = -(2**31)
MAX_INT32 = 2**31 - 1


def get_random_int32():
    return random.randint(MIN_INT32, MAX_INT32)


def merge_special_anon_bundle(
    dst_env: Environment,
    src_env_lst: list[Environment],
):
    dst_serialized_file = get_special_anon_bundle_serialized_file(dst_env)

    src_serialized_file_lst = [
        get_special_anon_bundle_serialized_file(i) for i in src_env_lst
    ]

    dst_name_set: set[str] = set()

    for obj in dst_serialized_file.objects.values():
        if obj.type.name != "MonoScript":
            continue

        data = obj.read()

        dst_name_set.add(data.m_Name)

    for src_serialized_file in src_serialized_file_lst:
        for i, obj in src_serialized_file.objects.items():
            if obj.type.name != "MonoScript":
                continue

            data = obj.read()

            if data.m_Name in dst_name_set:
                continue

            while i in dst_serialized_file.objects:
                i = get_random_int32()

            dst_serialized_file.objects[i] = obj

            dst_name_set.add(data.m_Name)

    dst_serialized_file.objects = dict(sorted(dst_serialized_file.objects.items()))


def is_merger_tree_path_allowed(path: str) -> bool:
    if path.startswith("gamedata/"):
        if path.startswith("gamedata/levels/activities/"):
            return True

        return False

    return True


def is_anon_bundle(bundle: ManifestBundle):
    return bundle.name.startswith("anon/")


def migrate_activity_bundle(
    merger_bundle_filepath: Path,
    src_client_version: str,
    dst_client_version: str,
    res_version: str,
):
    env = UnityPy.load(merger_bundle_filepath.as_posix())

    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue

        data = obj.read()

        data.m_Script = migrate_level(
            data.m_Name,
            src_client_version,
            dst_client_version,
            res_version,
            data.m_Script,
        )

        data.save()

    merger_bundle_filepath.write_bytes(env.file.save())


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
            if is_anon_bundle(dep_on):
                continue
            merger_bundle.dep_bundle_name_lst.append(dep_on.name)

        self.merger_bundle_dict[bundle.name] = merger_bundle

        for dep_on in bundle.dep_on_lst:
            if is_anon_bundle(dep_on):
                continue
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

            if not is_merger_tree_path_allowed(path):
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

    def copy_merger_tree_node(self, src_asset_name: str, dst_asset_name: str):
        src_path = get_asset_path(src_asset_name)
        dst_path = get_asset_path(dst_asset_name)

        src_node = get_node_by_path(self.merger_tree_root, src_path)

        if src_node is None:
            raise KeyError(f"{src_path} not found")

        add_file_to_tree(
            self.merger_tree_root,
            dst_path,
            asset=src_node.asset,
            bundle_name=src_node.bundle_name,
        )

    def merge_special_anon_bundle(self):
        target_special_anon_bundle = get_special_anon_bundle(self.target_res_manager)

        target_env = self.target_res.load_asset(target_special_anon_bundle.name)

        self.target_res.mark_modified_asset(target_special_anon_bundle.name)

        src_env_lst = []

        for src_res_manager in self.src_res_manager_lst:
            src_special_anon_bundle = get_special_anon_bundle(src_res_manager)

            src_env = src_res_manager.resource.load_asset(src_special_anon_bundle.name)

            src_env_lst.append(src_env)

        merge_special_anon_bundle(target_env, src_env_lst)

    def get_merger_bundle_filepath(self, bundle_name: str):
        return Path(TMP_DIRPATH, self.mod_name, bundle_name)

    def prep_merger_bundle(self):
        for bundle_name, merger_bundle in self.merger_bundle_dict.items():
            bundle_filepath = download_bundle(merger_bundle.bundle)

            merger_bundle_filepath = self.get_merger_bundle_filepath(bundle_name)

            merger_bundle_filepath.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(bundle_filepath, merger_bundle_filepath)

    def migrate_level(self):
        activity_node = get_node_by_path(
            self.merger_tree_root, "gamedata/levels/activities/", dir_ok=True
        )

        bundle_name_set: set[str] = set()

        for node in PreOrderIter(activity_node):
            if node.is_dir:
                continue
            if node.bundle_name in self.merger_bundle_dict:
                bundle_name_set.add(node.bundle_name)

        for bundle_name in bundle_name_set:
            merger_bundle = self.merger_bundle_dict[bundle_name]

            merger_bundle_filepath = self.get_merger_bundle_filepath(bundle_name)

            src_client_version = merger_bundle.bundle.manifest.resource.client_version

            dst_client_version = self.target_res.client_version

            res_version = merger_bundle.bundle.manifest.resource.res_version

            migrate_activity_bundle(
                merger_bundle_filepath,
                src_client_version,
                dst_client_version,
                res_version,
            )

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

            if self.target_res_manager.is_legacy_unity:
                self.new_manifest["bundles"].append(
                    {
                        "name": bundle_name,
                        "isCacheable": bundle.isCacheable,
                        "sccIndex": next_scc_idx,
                    }
                )
            else:
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

        if self.target_res_manager.is_legacy_unity:
            for bundle_name, merger_bundle in self.merger_bundle_dict.items():
                bundle_idx = self.bundle_idx_dict[bundle_name]

                self.new_manifest["bundles"][bundle_idx]["directDependencies"] = (
                    deepcopy(
                        self.new_manifest["bundles"][bundle_idx]["allDependencies"]
                    )
                )

    def build_mod_asset(self):
        for node in PreOrderIter(self.merger_tree_root):
            if node.is_dir:
                continue

            path = get_node_path(node)
            path_obj = Path(path)

            self.new_manifest["assetToBundleList"].append(
                {
                    "assetName": path_obj.with_suffix("").as_posix(),
                    "bundleIndex": self.bundle_idx_dict[node.bundle_name],
                    "name": node.asset.name,
                    "path": node.asset.path,
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
