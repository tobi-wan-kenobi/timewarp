import unittest

import timewarp.adapter
import timewarp.exceptions

class EmptyVirtualMachine(timewarp.adapter.VirtualMachine):
    pass

class TestEmptyAdapter(unittest.TestCase):
    def setUp(self):
        self.vm = EmptyVirtualMachine()

    def test_createSnapshotRaises(self):
        with self.assertRaises(timewarp.exceptions.NotImplemented):
            self.vm.create_snapshot()

    def test_restoreSnapshotRaises(self):
        with self.assertRaises(timewarp.exceptions.NotImplemented):
            self.vm.restore_snapshot(None)

    def test_listSnapshotsRaises(self):
        with self.assertRaises(timewarp.exceptions.NotImplemented):
            self.vm.list_snapshots()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
