from husk.core.exceptions import NotFound


class VolumeNotFound(NotFound):
    code = "volume_not_found"
