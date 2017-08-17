import mock

import timewarp.ec2

class Boto3Mock(object):
    def __init__(self):
        self._session = mock.patch("timewarp.ec2.Session").start()

        self._instances = {}
        self._volumes = {}

        self._resource = mock.Mock()
        self._resource.Instance = self.Instance
        self._resource.Volume = self.Volume
        self._session.resource.return_value = self._resource

        self._client = mock.Mock()
        self._session.client.return_value = self._client

        self._paginator = mock.Mock()
        self._client.get_paginator.return_value = self._paginator

    def paginator(self):
        return self._paginator

    def client(self):
        return self._client

    def resource(self):
        return self._resource

    def Volume(self, volume_id):
        vol = self._volumes.get(volume_id, mock.Mock())
        self._volumes[volume_id] = vol
        vol.id = volume_id

        vol.availability_zone = "us-east-1"
        vol.encrypted = False
        vol.iops = 100
        vol.kms_key_id = None
        vol.size = 10
        vol.volume_type = "gp2"
        vol.tags = []

        return vol

    def Instance(self, instance_id):
        inst = self._instances.get(instance_id, mock.Mock())
        self._instances[instance_id] = inst
        inst.id = instance_id
        return inst

    def teardown(self):
        self._session.stop()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
