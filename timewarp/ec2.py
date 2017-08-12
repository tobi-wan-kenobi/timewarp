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
        return [ Snapshot() ]

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
