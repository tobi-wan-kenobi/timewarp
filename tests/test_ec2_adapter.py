import mock
import unittest
import datetime

import mock_boto3

import timewarp.ec2

class TestEc2Adapter(unittest.TestCase):
    def setUp(self):
        self.boto3 = mock_boto3.Boto3Mock()

        self.invalidInstanceId = "abcdef"
        self.someInstanceId = "i-123456789"
        self.someSnapshot = {
            "StartTime": datetime.datetime(2016, 1, 1),
            "Tags": [
                { "Key": "timewarp:backup_id", "Value": "12345" },
                { "Key": "timewarp:instance", "Value": self.someInstanceId },
            ],
        }

    def tearDown(self):
        self.boto3.teardown()

    def test_invalidInstanceId(self):
        self.boto3.instance().load.side_effect = ValueError
        with self.assertRaises(timewarp.exceptions.NoSuchVirtualMachine):
            vm = timewarp.ec2.VirtualMachine(self.invalidInstanceId)

    def test_missingInstanceId(self):
        with self.assertRaises(timewarp.exceptions.NoSuchVirtualMachine):
            vm = timewarp.ec2.VirtualMachine(None)

    def test_listSingleVolumeSnapshot(self):
        self.boto3.paginator().paginate.return_value = [{
            "Snapshots": [ self.someSnapshot ]
        }]
        vm = timewarp.ec2.VirtualMachine(self.someInstanceId)
        snapshots = vm.list_snapshots()
        self.assertEquals(1, len(snapshots))

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
