import boto3

import timewarp.adapter

class Session(object):
    clients = {}
    resources = {}

    @classmethod
    def client(cls, name):
        cls.clients[name] = cls.clients.get(name, boto3.client(name))
        return cls.clients[name]

    @classmethod
    def resource(cls, name):
        cls.resources[name] = cls.resources.get(name, boto3.resource(name))
        return cls.resources[name]

class Checkpoint(timewarp.adapter.Checkpoint):
    pass

class VirtualMachine(timewarp.adapter.VirtualMachine):
    def __init__(self, instance_id):
        if not instance_id:
            raise timewarp.exceptions.NoSuchVirtualMachine()
        self._inst = Session.resource("ec2").Instance(instance_id)
        try:
            self._inst.load()
        except Exception:
            raise timewarp.exceptions.NoSuchVirtualMachine()

    def list_checkpoints(self):
        retval = {}
        paginator = Session.client("ec2").get_paginator("describe_snapshots")
        it = paginator.paginate(
            Filters=[
                {"Name": "tag-key", "Values": ["timewarp:checkpoint_id"]},
                {"Name": "tag:timewarp:instance", "Values":[self._inst.id]},
            ],
        )
        for data in it:
            for snapshot in data["Snapshots"]:
                cid = next((tag["Value"] for tag in snapshot["Tags"] if tag["Key"] == "timewarp:checkpoint_id"), None)
                if cid:
                    temp = retval.get(cid, Checkpoint(cid))
                    temp.time = snapshot["StartTime"]
                    retval[temp.id] = temp

        return sorted(retval.itervalues(), key=lambda b: b.time)

    def create_checkpoint(self, name=None):
        checkpoint = Checkpoint()
        self._inst.reload()
        for volume in self._inst.volumes.all():
            snap = volume.create_snapshot()
            snap.create_tags(
                Tags=[
                    {"Key": "timewarp:instance", "Value": self._inst.id},
                    {"Key": "timewarp:checkpoint_id", "Value": checkpoint.id},
                    {"Key": "timewarp:volume_id", "Value": volume.id},
                    {"Key": "Name", "Value": "Timewarp Checkpoint"}
                ]
            )
            if name:
                snap.create_tags(Tags=[{"Key": "timewarp:name", "Value": name}])
            checkpoint.time = snap.start_time
        return checkpoint 

    def restore_checkpoint(self, checkpoint, force=False):
        pass

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
