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
        self.someInstanceId = "i-abcdef"
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
        self.boto3.Instance(self.runningInstanceId).state = {"Name": "running", "Code": 16}
        self.boto3.Instance(self.runningInstanceId).block_device_mappings = []
        self.runningCheckpoint = self.runningVM.list_checkpoints()[0]

        self.someVM = timewarp.ec2.VirtualMachine(self.someInstanceId)
        self.boto3.Instance(self.someInstanceId).state = {"Name": "stopped"}
        self.boto3.Instance(self.someInstanceId).block_device_mappings = []

    def tearDown(self):
        self.boto3.teardown()

    def test_failIfRunning(self):
        with self.assertRaises(timewarp.exceptions.InvalidOperation):
            self.runningVM.restore_checkpoint(self.runningCheckpoint.id)

    def test_failIfNoBlockDeviceMapping(self):
        with self.assertRaises(RuntimeError):
            self.runningVM.restore_checkpoint(self.runningCheckpoint.id, force=True)

    def test_failIfNoDeviceSpecification(self):
        self.boto3.Instance(self.runningInstanceId).block_device_mappings = [{"DeviceName": "xvda", "VolumeId": "vol-1234"}]

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

        self.runningVM.restore_checkpoint(self.runningCheckpoint.id, force=True)
        vm.stop.assert_called_once()
        self.boto3.client().create_volume.assert_called_once()
        vm.start.assert_called_once()

    def create_checkpoint(self, instance_id, checkpoint_id, snapshot_count, start_dev = "a"):
        snapshots = []

        for i in range(snapshot_count):
            tags = [
                    {"Key": "timewarp:checkpoint_id", "Value": checkpoint_id},
                    {"Key": "timewarp:instance", "Value": instance_id},
                    {"Key": "timewarp:device", "Value": "/dev/xvd{}".format(chr(ord(start_dev) + i)) },
                    {"Key": "timewarp:device_specs", "Value": json.dumps({
                        "AvailabilityZone": "us-east-1", "Encrypted": False, "Iops": 100, "KmsKeyId": None,
                        "Size": 10, "VolumeType": "gp2", "Tags": []
                    })}

            ]
            snapshots.append({
                "StartTime": datetime.datetime.now(), "Tags": tags, "SnapshotId": "snap-{}".format(i)
            })

        self.boto3.paginator().paginate.return_value = [{
            "Snapshots": snapshots
        }]

    def test_multiRestore(self):
        volumes = []
        char = "a"
        volume_count = 3
        self.create_checkpoint(self.someInstanceId, "some-checkpoint-id", volume_count)
        inst = self.boto3.Instance(self.someInstanceId)
        for i in range(volume_count):
            volumes.append(self.boto3.Volume("vol-{}".format(i)))
            inst.block_device_mappings.append({
                "DeviceName": "/dev/xvd{}".format(char), "Ebs": { "VolumeId": volumes[i].id }
            })
            char = chr(ord(char)+1)

        self.boto3.client().create_volume.return_value = {"VolumeId": "vol-1234"}
        self.someVM.restore_checkpoint("some-checkpoint-id")

        for v in volumes:
            v.delete.assert_called_once()
        self.boto3.client().create_volume.assert_called()
        # TODO: validate parameters
        self.assertEquals(volume_count, len(self.boto3.client().create_volume.call_args_list))
        self.assertEquals(volume_count, len(inst.attach_volume.call_args_list))

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
