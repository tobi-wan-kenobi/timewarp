import mock
import unittest
import datetime

import mock_boto3

import timewarp.ec2

class TestEc2List(unittest.TestCase):
    def setUp(self):
        self.boto3 = mock_boto3.Boto3Mock()

        self.someInstanceId = "i-123456789"
        self.someSnapshotId = "12345"
        tags = [
                {"Key": "timewarp:snapshot_id", "Value": self.someSnapshotId},
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
        ]
        self.someSnapshot = {"StartTime": datetime.datetime(2016, 1, 1), "Tags": tags}
        self.earliestSnapshot = {"StartTime": datetime.datetime(2016, 1, 1),
            "Tags": [
                {"Key": "timewarp:snapshot_id", "Value": "1"},
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
            ]
        }
        self.earlierSnapshot = {"StartTime": datetime.datetime(2016, 1, 10),
            "Tags": [
                {"Key": "timewarp:snapshot_id", "Value": "4"},
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
            ]
        }
        self.latestSnapshot = {"StartTime": datetime.datetime(2017, 1, 10),
            "Tags": [
                {"Key": "timewarp:snapshot_id", "Value": "3"},
                {"Key": "timewarp:instance", "Value": self.someInstanceId},
            ]
        }

    def tearDown(self):
        self.boto3.teardown()

    def test_listSingleSnapshot(self):
        self.boto3.paginator().paginate.return_value = [{
            "Snapshots": [ self.someSnapshot ]
        }]
        vm = timewarp.ec2.VirtualMachine(self.someInstanceId)
        snapshots = vm.list_snapshots()
        self.assertEquals(1, len(snapshots))
        self.assertEquals(self.someSnapshotId, snapshots[0].id)

    def test_listMultipleSnapshots(self):
        self.boto3.paginator().paginate.return_value = [{
            "Snapshots": [self.latestSnapshot, self.earliestSnapshot, self.earlierSnapshot]
        }]
        vm = timewarp.ec2.VirtualMachine(self.someInstanceId)
        snapshots = vm.list_snapshots()
        self.assertEquals(3, len(snapshots))
        self.assertEquals(snapshots[0].time, self.earliestSnapshot["StartTime"])
        self.assertEquals(snapshots[1].time, self.earlierSnapshot["StartTime"])
        self.assertEquals(snapshots[2].time, self.latestSnapshot["StartTime"])

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
