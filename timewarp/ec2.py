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

class Snapshot(timewarp.adapter.Snapshot):
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

    def list_snapshots(self):
        retval = {}
        paginator = Session.client("ec2").get_paginator("describe_snapshots")
        it = paginator.paginate(
            Filters=[
                {"Name": "tag-key", "Values": ["timewarp:snapshot_id"]},
                {"Name": "tag:timewarp:instance", "Values":[self._inst.id]},
            ],
        )
        for data in it:
            for snapshot in data["Snapshots"]:
                snapshot_id = next((tag["Value"] for tag in snapshot["Tags"] if tag["Key"] == "timewarp:snapshot_id"), None)
                if snapshot_id:
                    temp = retval.get(snapshot_id, Snapshot(snapshot_id))
                    temp.time = snapshot["StartTime"]
                    retval[temp.id] = temp

        return sorted(retval.itervalues(), key=lambda b: b.time)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
