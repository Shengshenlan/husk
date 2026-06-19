from husk.core.exceptions import HuskError, NotFound


class SnapshotNotFound(NotFound):
    code = "snapshot_not_found"


class SnapshotPullFailed(HuskError):
    status_code = 500
    code = "snapshot_pull_failed"
