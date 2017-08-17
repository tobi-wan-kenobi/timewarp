import mock
import unittest
import datetime

import mock_boto3

import timewarp.ec2

class TestEc2List(unittest.TestCase):
    def setUp(self):
        self.boto3 = mock_boto3.Boto3Mock()

        self.someInstanceId = "i-123456789"
        self.someCheckpointId = "12345"
        tags = [
                {"Key": "timewarp:checkpoint_id", "Value": self.someCheckpointId},
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
        ]
        self.someEC2Snapshot = {"StartTime": datetime.datetime(2016, 1, 1), "Tags": tags}
        self.earliestEC2Snapshot = {"StartTime": datetime.datetime(2016, 1, 1),
            "Tags": [
                {"Key": "timewarp:checkpoint_id", "Value": "1"},
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
            ]
        }
        self.earlierEC2Snapshot = {"StartTime": datetime.datetime(2016, 1, 10),
            "Tags": [
                {"Key": "timewarp:checkpoint_id", "Value": "4"},
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
            ]
        }
        self.latestEC2Snapshot = {"StartTime": datetime.datetime(2017, 1, 10),
            "Tags": [
                {"Key": "timewarp:checkpoint_id", "Value": "3"},
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
            ]
        }

    def tearDown(self):
        self.boto3.teardown()

    def test_listSingleCheckpoint(self):
        self.boto3.paginator().paginate.return_value = [{
            "Snapshots": [ self.someEC2Snapshot ]
        }]
        vm = timewarp.ec2.VirtualMachine(self.someInstanceId)
        checkpoints = vm.list_checkpoints()
        self.assertEquals(1, len(checkpoints))
        self.assertEquals(self.someCheckpointId, checkpoints[0].id)

    def test_listMultipleCheckpoints(self):
        self.boto3.paginator().paginate.return_value = [{
            "Snapshots": [self.latestEC2Snapshot, self.earliestEC2Snapshot, self.earlierEC2Snapshot]
        }]
        vm = timewarp.ec2.VirtualMachine(self.someInstanceId)
        checkpoints = vm.list_checkpoints()
        self.assertEquals(3, len(checkpoints))
        self.assertEquals(checkpoints[0].time, self.latestEC2Snapshot["StartTime"])
        self.assertEquals(checkpoints[1].time, self.earlierEC2Snapshot["StartTime"])
        self.assertEquals(checkpoints[2].time, self.earliestEC2Snapshot["StartTime"])

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
