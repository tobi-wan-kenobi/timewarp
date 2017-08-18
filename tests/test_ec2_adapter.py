import mock
import unittest
import datetime

from . import mock_boto3

import timewarp.ec2

class TestEc2Adapter(unittest.TestCase):
    def setUp(self):
        self.boto3 = mock_boto3.Boto3Mock()

        self.invalidInstanceId = "abcdef"

    def tearDown(self):
        self.boto3.teardown()

    def test_invalidInstanceId(self):
        self.boto3.Instance(self.invalidInstanceId).load.side_effect = ValueError
        with self.assertRaises(timewarp.exceptions.NoSuchVirtualMachine):
            vm = timewarp.ec2.VirtualMachine(self.invalidInstanceId)

    def test_missingInstanceId(self):
        with self.assertRaises(timewarp.exceptions.NoSuchVirtualMachine):
            vm = timewarp.ec2.VirtualMachine(None)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
