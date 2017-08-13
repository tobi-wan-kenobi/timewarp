import mock
import unittest
import datetime

import mock_boto3

import timewarp.ec2

class TestEc2Create(unittest.TestCase):
    def setUp(self):
        self.boto3 = mock_boto3.Boto3Mock()
        self.volume = mock.Mock()
        self.snapshot = mock.Mock()

        self.someInstanceId = "i-123abc"
        self.anySnapshotName = "sample snapshot name"

        self.boto3.instance().id = self.someInstanceId

        self.volume.id = "vol-abcdef"
        self.volume.create_snapshot.return_value = self.snapshot
        self.snapshot.create_tags.return_value = True

    def tearDown(self):
        self.boto3.teardown()

    def test_createSingleVolumeSnapshot(self):
        volumes = [self.volume]
        self.boto3.instance().volumes.all.return_value = volumes
        snap = timewarp.ec2.VirtualMachine(self.someInstanceId).create_snapshot()
        self.volume.create_snapshot.assert_called_once()
        self.snapshot.create_tags.assert_called_once_with(
            Tags=[
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
                {"Key": "timewarp:snapshot_id", "Value": snap.id},
                {"Key": "timewarp:volume_id", "Value": self.volume.id},
                {"Key": "Name", "Value": "Timewarp Snapshot"},
            ]
        )

    def test_createNamedSnapshot(self):
        volumes = [self.volume]
        self.boto3.instance().volumes.all.return_value = volumes
        snap = timewarp.ec2.VirtualMachine(self.someInstanceId).create_snapshot(self.anySnapshotName)
        self.volume.create_snapshot.assert_called_once()
        self.snapshot.create_tags.assert_any_call(
            Tags=[
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
                {"Key": "timewarp:snapshot_id", "Value": snap.id},
                {"Key": "timewarp:volume_id", "Value": self.volume.id},
                {"Key": "Name", "Value": "Timewarp Snapshot"},
            ]
        )
        self.snapshot.create_tags.assert_any_call(
            Tags=[{"Key": "timewarp:name", "Value": self.anySnapshotName}]
        )

    def test_createMultiVolumeSnapshot(self):
        volumes = []
        snapshots = []
        for i in range(10):
            v = mock.Mock()
            s = mock.Mock()
            v.create_snapshot.return_value = s
            s.create_tags.return_value = True
            volumes.append(v)
            snapshots.append(s)

        self.boto3.instance().volumes.all.return_value = volumes
        timewarp.ec2.VirtualMachine(self.someInstanceId).create_snapshot()

        for v in volumes:
            v.create_snapshot.assert_called_once()
        for s in snapshots:
            s.create_tags.assert_called_once()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
