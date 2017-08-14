import unittest

import timewarp.adapter
import timewarp.exceptions

class EmptyVirtualMachine(timewarp.adapter.VirtualMachine):
    pass

class TestEmptyAdapter(unittest.TestCase):
    def setUp(self):
        self.vm = EmptyVirtualMachine()

    def test_createCheckpointRaises(self):
        with self.assertRaises(timewarp.exceptions.NotImplemented):
            self.vm.create_checkpoint()

    def test_restoreCheckpointRaises(self):
        with self.assertRaises(timewarp.exceptions.NotImplemented):
            self.vm.restore_checkpoint(None)

    def test_listCheckpointsRaises(self):
        with self.assertRaises(timewarp.exceptions.NotImplemented):
            self.vm.list_checkpoints()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
