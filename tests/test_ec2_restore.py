import json
import mock
import unittest
import datetime

import mock_boto3

import timewarp.ec2

class TestEc2Restore(unittest.TestCase):
    def setUp(self):
        self.boto3 = mock_boto3.Boto3Mock()

        self.runningInstanceId = "i-234123432"
        self.someSnapshotId = "snap-123"
        tags = [
                {"Key": "timewarp:checkpoint_id", "Value": self.someSnapshotId},
                {"Key": "timewarp:instance", "Value": self.runningInstanceId},
                {"Key": "timewarp:device", "Value": "xvda" },
        ]
        self.someSnapshot = {"StartTime": datetime.datetime(2016, 1, 1), "Tags": tags, "SnapshotId": self.someSnapshotId}
        self.boto3.paginator().paginate.return_value = [{
            "Snapshots": [ self.someSnapshot ]
        }]

        self.runningVM = timewarp.ec2.VirtualMachine(self.runningInstanceId)
        self.boto3.Instance(self.runningInstanceId).state = { "Name": "running", "Code": 16 }
        self.boto3.Instance(self.runningInstanceId).block_device_mappings = []
        self.runningCheckpoint = self.runningVM.list_checkpoints()[0]

    def tearDown(self):
        self.boto3.teardown()

    def test_failIfRunning(self):
        with self.assertRaises(timewarp.exceptions.InvalidOperation):
            self.runningVM.restore_checkpoint(self.runningCheckpoint.id)

    def test_failIfNoBlockDeviceMapping(self):
        with self.assertRaises(RuntimeError):
            self.runningVM.restore_checkpoint(self.runningCheckpoint.id, force=True)

    def test_failIfNoDeviceSpecification(self):
        self.runningVM.block_device_mappings = [{"DeviceName": "xvda", "VolumeId": "vol-1234"}]

        with self.assertRaises(RuntimeError):
            self.runningVM.restore_checkpoint(self.runningCheckpoint.id, force=True)

    def test_restoreRunningIfForced(self):
        vm = self.boto3.Instance(self.runningInstanceId)
        vm.block_device_mappings = [{"DeviceName": "xvda", "VolumeId": "vol-1234"}]
        self.someSnapshot["Tags"].append({"Key": "timewarp:device_specs", "Value": json.dumps({
            "AvailabilityZone": "us-east-1", "Encrypted": False, "Iops": 100, "KmsKeyId": None,
            "Size": 10, "VolumeType": "gp2", "Tags": []
        })})
        self.boto3.client().create_volume.return_value = {"VolumeId": "vol-1234"}

        self.boto3.Volume(self.runningInstanceId).state = { "Name": "running", "Code": 16 }

        self.runningVM.restore_checkpoint(self.runningCheckpoint.id, force=True)
        vm.stop.assert_called_once()
        self.boto3.client().create_volume.assert_called_once()


#
#        # ensure that for each volume, a new volume gets created
#        # ensure each volume is deleted
#        # ensure each snapshot volume gets created and attached

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
