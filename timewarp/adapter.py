import timewarp.exceptions

class Snapshot(object):
    pass

class VirtualMachine(object):
    def create_snapshot(self, name=None):
        raise timewarp.exceptions.NotImplemented()

    def restore_snapshot(self, snapshot, force=False):
        raise timewarp.exceptions.NotImplemented()

    def list_snapshots(self):
        raise timewarp.exceptions.NotImplemented()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
