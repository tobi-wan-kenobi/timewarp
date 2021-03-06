import json
import boto3

import timewarp.adapter
from timewarp.adapter import dryrun
from timewarp.util import emit

class Session(object):
    clients = {}
    resources = {}

    @classmethod
    def client(cls, name):
        cls.clients[name] = cls.clients.get(name, boto3.client(name))
        return cls.clients[name]

    @classmethod
    def resource(cls, name):
        cls.resources[name] = cls.resources.get(name, boto3.resource(name))
        return cls.resources[name]

class Checkpoint(timewarp.adapter.Checkpoint):
    def delete(self, instance_id):
        paginator = Session.client("ec2").get_paginator("describe_snapshots")
        it = paginator.paginate(
            Filters=[
                {"Name": "tag:timewarp:checkpoint_id", "Values": [self.id]},
                {"Name": "tag:timewarp:instance", "Values": [instance_id]},
            ],
        )
        for data in it:
            for snapshot in data["Snapshots"]:
                emit("deleting snapshot {} for checkpoint {}".format(snapshot["SnapshotId"], self.id))
                if not dryrun:
                    Session.resource("ec2").Snapshot(snapshot["SnapshotId"]).delete()

    def restore_volumes(self):
        volumes = {}
        paginator = Session.client("ec2").get_paginator("describe_snapshots")
        it = paginator.paginate(
            Filters=[
                {"Name": "tag:timewarp:checkpoint_id", "Values": [self.id]},
            ],
        )
        for data in it:
            for snapshot in data["Snapshots"]:
                # get device name
                dev = next((tag["Value"] for tag in snapshot["Tags"] if tag["Key"] == "timewarp:device"), None)
                if not dev:
                    raise RuntimeError("no device tag found")
                specs = next((tag["Value"] for tag in snapshot["Tags"] if tag["Key"] == "timewarp:device_specs"), None)
                if not specs:
                    raise RuntimeError("no device specs found")
                specs = json.loads(specs)

                if specs["KmsKeyId"] is None: del specs["KmsKeyId"]
                if not specs["VolumeType"].startswith("io"): del specs["Iops"]
                specs["TagSpecifications"] = [{
                    "ResourceType": "volume", "Tags": specs["Tags"],
                }]
                del specs["Tags"]
                specs["SnapshotId"] = snapshot["SnapshotId"]

                emit("creating new volume from snapshot {}".format(snapshot["SnapshotId"]))
                if not dryrun:
                    volume = Session.client("ec2").create_volume(**specs)
                else:
                    volumes[dev] = "vol-<volumeid>"
                volumes[dev] = volume["VolumeId"]
        if not dryrun:
            waiter = Session.client("ec2").get_waiter("volume_available")
            waiter.wait(VolumeIds=volumes.values())

        return volumes

class VirtualMachine(timewarp.adapter.VirtualMachine):
    def __init__(self, instance_id):
        if not instance_id:
            raise timewarp.exceptions.NoSuchVirtualMachine()
        self._inst = Session.resource("ec2").Instance(instance_id)
        try:
            self._inst.load()
        except Exception:
            raise timewarp.exceptions.NoSuchVirtualMachine()

    def list_checkpoints(self):
        retval = {}
        paginator = Session.client("ec2").get_paginator("describe_snapshots")
        it = paginator.paginate(
            Filters=[
                {"Name": "tag-key", "Values": ["timewarp:checkpoint_id"]},
                {"Name": "tag:timewarp:instance", "Values":[self._inst.id]},
            ],
        )
        for data in it:
            for snapshot in data["Snapshots"]:
                cid = next((tag["Value"] for tag in snapshot["Tags"] if tag["Key"] == "timewarp:checkpoint_id"), None)
                name = next((tag["Value"] for tag in snapshot["Tags"] if tag["Key"] == "timewarp:name"), None)
                if cid:
                    temp = retval.get(cid, Checkpoint(cid))
                    temp.time = snapshot["StartTime"]
                    temp.name = name
                    retval[temp.id] = temp

        return sorted(retval.values(), key=lambda b: b.time, reverse=True)

    def create_checkpoint(self, name=None):
        checkpoint = Checkpoint()
        self._inst.reload()
        for dev in self._inst.block_device_mappings:
            if not "Ebs" in dev: continue # skip non EBS volumes
            volume = Session.resource("ec2").Volume(dev["Ebs"]["VolumeId"])
            emit("creating new snapshot from volume {} for instance {}".format(dev["Ebs"]["VolumeId"], self._inst.id))
            if not dryrun:
                snap = volume.create_snapshot()
                waiter = Session.client("ec2").get_waiter('snapshot_completed')
                waiter.wait(SnapshotIds=[snap.id])

                snap.create_tags(
                    Tags=[
                        {"Key": "timewarp:device", "Value": dev["DeviceName"]},
                        {"Key": "timewarp:instance", "Value": self._inst.id},
                        {"Key": "timewarp:checkpoint_id", "Value": checkpoint.id},
                        {"Key": "timewarp:volume_id", "Value": volume.id},
                        {"Key": "Name", "Value": "Timewarp Checkpoint"},
                    ]
                )
                if name:
                    snap.create_tags(Tags=[{"Key": "timewarp:name", "Value": name}])

                snap.create_tags(Tags=[
                    {"Key": "timewarp:device_specs", "Value": json.dumps({
                        "AvailabilityZone": volume.availability_zone,
                        "Encrypted": volume.encrypted,
                        "Iops": volume.iops,
                        "KmsKeyId": volume.kms_key_id,
                        "Size": volume.size,
                        "VolumeType": volume.volume_type,
                        "Tags": volume.tags,
                    })},
                ])
                checkpoint.time = snap.start_time
        return checkpoint 

    # TODO: keep an undo stack in case of errors
    def restore_checkpoint(self, checkpoint_id, force=False, keep_volumes=False):
        checkpoint = Checkpoint(checkpoint_id)
        self._inst.reload()

        if self._inst.state["Name"] != "stopped" and not force:
            raise timewarp.exceptions.InvalidOperation("unable to stop instance")

        volumes = checkpoint.restore_volumes()

        needs_start = False
        if self._inst.state["Name"] != "stopped":
            emit("stopping instance {}".format(self._inst.id))
            if not dryrun:
                self._inst.stop()
                waiter = Session.client("ec2").get_waiter("instance_stopped")
                waiter.wait(InstanceIds=[self._inst.id])
            needs_start = True

        old_volumes = []
        for dev in self._inst.block_device_mappings:
            if not "Ebs" in dev: continue
            emit("detaching volume {} from instance {}".format(dev["Ebs"]["VolumeId"], self._inst.id))
            if not dryrun:
                self._inst.detach_volume(VolumeId=dev["Ebs"]["VolumeId"])
            old_volumes.append(dev["Ebs"]["VolumeId"])

        if not dryrun:
            waiter = Session.client("ec2").get_waiter("volume_available")
            waiter.wait(VolumeIds=old_volumes)
        for v in old_volumes:
            if not keep_volumes:
                emit("deleting volume {}".format(v))
                if not dryrun:
                    Session.resource("ec2").Volume(v).delete()

        volume_ids = []
        for dev in volumes:
            emit("attaching volume {} as {} to instance {}".format(volumes[dev], dev, self._inst.id))
            if not dryrun:
                self._inst.attach_volume(Device=dev, VolumeId=volumes[dev])
            volume_ids.append(volumes[dev])
        if not dryrun:
            waiter = Session.client("ec2").get_waiter("volume_in_use")
            waiter.wait(VolumeIds=volume_ids)

        if needs_start:
            emit("starting instance {}".format(self._inst.id))
            if not dryrun:
                self._inst.start()
                waiter = Session.client("ec2").get_waiter("instance_running")
                waiter.wait(InstanceIds=[self._inst.id])

    def delete_checkpoint(self, checkpoint_id):
        checkpoint = Checkpoint(checkpoint_id)
        self._inst.reload()
        checkpoint.delete(self._inst.id)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
