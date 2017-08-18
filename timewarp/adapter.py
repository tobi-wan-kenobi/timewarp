import uuid

import timewarp.exceptions

dryrun = False

class Checkpoint(object):
    def __init__(self, uid=None):
        self.id = uid if uid else str(uuid.uuid4())
        self.name = None
        self.time = None

class VirtualMachine(object):
    def create_checkpoint(self, name=None):
        raise timewarp.exceptions.NotImplemented()

    def restore_checkpoint(self, checkpoint, force=False, keep=False):
        raise timewarp.exceptions.NotImplemented()

    def list_checkpoints(self):
        raise timewarp.exceptions.NotImplemented()

    def delete_checkpoint(self, checkpoint):
        raise timewarp.exceptions.NotImplemented()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
