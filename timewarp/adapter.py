import uuid

import timewarp.exceptions

class Snapshot(object):
    def __init__(self, uid=None):
        self.id = uid if uid else str(uuid.uuid4())

class VirtualMachine(object):
    def create_snapshot(self, name=None):
        raise timewarp.exceptions.NotImplemented()

    def restore_snapshot(self, snapshot, force=False):
        raise timewarp.exceptions.NotImplemented()

    def list_snapshots(self):
        raise timewarp.exceptions.NotImplemented()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
