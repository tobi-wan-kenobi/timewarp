import mock
import unittest
import datetime

import mock_boto3

import timewarp.ec2

class TestEc2Create(unittest.TestCase):
    def setUp(self):
        self.boto3 = mock_boto3.Boto3Mock()
        self.snapshot = mock.Mock()

        self.someInstanceId = "i-123abc"
        self.anyCheckpointName = "sample checkpoint name"

        self.volume = self.boto3.Volume("vol-abcdef")
        self.volume.create_snapshot.return_value = self.snapshot
        self.snapshot.create_tags.return_value = True

    def tearDown(self):
        self.boto3.teardown()

    def test_createSingleVolumeCheckpoint(self):
        volumes = [self.volume]
        self.boto3.Instance(self.someInstanceId).volumes.all.return_value = volumes
        snap = timewarp.ec2.VirtualMachine(self.someInstanceId).create_checkpoint()
        self.volume.create_snapshot.assert_called_once()
        self.snapshot.create_tags.assert_called()
        self.assertTrue({"Key": "timewarp:instance", "Value": self.someInstanceId} in self.snapshot.create_tags.call_args_list[0][1]["Tags"])
        self.assertTrue({"Key": "timewarp:checkpoint_id", "Value": snap.id} in self.snapshot.create_tags.call_args_list[0][1]["Tags"])
        self.assertTrue({"Key": "timewarp:volume_id", "Value": self.volume.id} in self.snapshot.create_tags.call_args_list[0][1]["Tags"])

    def test_createNamedCheckpoint(self):
        volumes = [self.volume]
        self.boto3.Instance(self.someInstanceId).volumes.all.return_value = volumes
        snap = timewarp.ec2.VirtualMachine(self.someInstanceId).create_checkpoint(self.anyCheckpointName)
        self.volume.create_snapshot.assert_called_once()
        self.snapshot.create_tags.assert_called()
        self.assertTrue({"Key": "timewarp:instance", "Value": self.someInstanceId} in self.snapshot.create_tags.call_args_list[0][1]["Tags"])
        self.assertTrue({"Key": "timewarp:checkpoint_id", "Value": snap.id} in self.snapshot.create_tags.call_args_list[0][1]["Tags"])
        self.assertTrue({"Key": "timewarp:volume_id", "Value": self.volume.id} in self.snapshot.create_tags.call_args_list[0][1]["Tags"])
        self.assertTrue({"Key": "timewarp:name", "Value": self.anyCheckpointName} in self.snapshot.create_tags.call_args_list[1][1]["Tags"])

    def test_createMultiVolumeCheckpoint(self):
        volumes = []
        snapshots = []
        for i in range(10):
            v = self.boto3.Volume("vol-{}".format(i))
            s = mock.Mock()
            v.create_snapshot.return_value = s
            s.create_tags.return_value = True
            volumes.append(v)
            snapshots.append(s)

        self.boto3.Instance(self.someInstanceId).volumes.all.return_value = volumes
        timewarp.ec2.VirtualMachine(self.someInstanceId).create_checkpoint()

        for v in volumes:
            v.create_snapshot.assert_called_once()
        for s in snapshots:
            s.create_tags.assert_called()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
