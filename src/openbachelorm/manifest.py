from .resource import Resource


class ManifestManager:
    def __init__(self, res: Resource):
        self.resource = res

        res.load_manifest()

        self.manifest = res.manifest
