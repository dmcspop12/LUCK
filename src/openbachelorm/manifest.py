from dataclasses import dataclass, field
from copy import deepcopy

from .resource import Resource


@dataclass
class ManifestBundle:
    name: str
    props: int
    sccIndex: int
    allDependencies: list[int]

    dep_on_lst: list["ManifestBundle"] = field(default_factory=list)


class ManifestManager:
    def __init__(self, res: Resource):
        self.resource = res

        res.load_manifest()

        self.manifest = res.manifest

        self.build_bundle_lst()

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
