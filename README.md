# timewarp

[![Build Status](https://travis-ci.org/tobi-wan-kenobi/timewarp.svg?branch=master)](https://travis-ci.org/tobi-wan-kenobi/timewarp)
[![Code Climate](https://codeclimate.com/github/tobi-wan-kenobi/timewarp/badges/gpa.svg)](https://codeclimate.com/github/tobi-wan-kenobi/timewarp)
[![Test Coverage](https://codeclimate.com/github/tobi-wan-kenobi/timewarp/badges/coverage.svg)](https://codeclimate.com/github/tobi-wan-kenobi/timewarp/coverage)
[![Issue Count](https://codeclimate.com/github/tobi-wan-kenobi/timewarp/badges/issue_count.svg)](https://codeclimate.com/github/tobi-wan-kenobi/timewarp)

Supported Python versions: 2.7, 3.3, 3.4, 3.5, 3.6

`timewarp` is a small utility to snapshot and restore your virtual machines in cloud environments. Currently, only Amazon Web Services (AWS) EC2 is supported. It is primarily intended for developers that want to snapshot their instance before doing risky modifications during the development cycle.

I know it goes against the grain of the "virtual machines are cattle, not pets" paradigm of cloud computing, but we developers **do** get attached to our instances occasionally ;)

**IMPORTANT NOTE**: Please do *not* use this software in production environments, for two reasons:
1. AWS offers much superior means to keep your instances healthy (e.g. CloudFormation, Auto Recovery, Elastic Loadbalancing, etc.)
2. This is a *very* early alpha version of the software and might contain severe bugs. Among other disasters, this tool could inadvertently delete random snapshots, create random volumes and stop random instances. Having said that, I did my best to ensure this doesn't actually happen.

**IMPORTANT NOTE 2**: Due to the fact that this is a very early version, I urge you to test it with an unprivileged read-only user first to ensure it does not delete too much (as part of the recovery process, old volumes are detached and deleted, and instances might get stopped). To emphasize: If you use this tool incorrectly (or if it has stupid bugs), it might delete volumes or stop instances not intended for deletion! You have been warned.

Having said that, here's how you use it:

- "checkpoints" are point-in-time snapshots (I wanted to avoid the term "snapshot" as to not create a confusion between timewarp snapshots and AWS EC2 snapshots)
- "virtual machines" are instances
- The tool requires `boto3` to be installed and configured
- Required AWS permissions:
  - list snapshots
  - create snapshots (to create a checkpoint)
  - create volumes (to restore a checkpoint)
  - delete snapshots (to delete a checkpoint)
  - delete volumes (to restore a checkpoint, not required if you are using `--keep-volume`)
  - start/stop instances (to restore a checkpoint, not required if you manually stop the instance before restoring)
```
# list all checkpoints for a virtual machine
$ timewarp ec2 list <instance id>
# create a new checkpoint
$ timewarp ec2 create <instance id>
# optionally, you can also provide a name for the checkpoint:
$ timewarp ec2 create [-n|--name <name>] <instance id>

# restore a previous checkpoint - the checkpoint id is retrieved
# from the "list" command
$ timewarp ec2 restore <instance id> <checkpoint id>
# when restoring a checkpoint, you can specify "-k" (or "--keep-volumes")
# to keep the volumes. Otherwise, the original volumes will be deleted.
$ timewarp ec2 restore -k <instance id> <checkpoint id>
# when restoring a checkpoint, you can specify "-c" (or "--current-checkpoint")
# to automatically create a checkpoint for the current state.
$ timewarp ec2 restore -c <instance id> <checkpoint id>
# restoring will NOT work if the instance is currently running (as it needs to
# be stopped for that). In order to automatically stop and restart the instance,
# specify "-f" or "--force" to the call:
$ timewarp ec2 restore -f <instance id> <checkpoint id>

# delete a list of timewarp checkpoints
$ timewarp ec2 delete <instance id> <checkpoint id> <checkpoint id> ...
```

All commands also support a "dry-run" flag (`-d|--dry-run`) and a "verbose" flag (`-v|--verbose`). In dry-run mode, no destructive action (stopping a VM, deleting a snapshot, deleting or detaching a volume) **should** be performed - but as always: Please beware of bugs!

# Important restrictions
* Only EBS volumes are snapshotted
* The instance still has to exist (i.e. recovering a deleted instance is not possible using this tool)
* Completely untested alpha software

# Example usage
Here are some examples for a three-volume instance:

```
# dry-run a create (nothing happens)
$ timewarp -d ec2 create i-09eab02eb24cb9d1d
creating new snapshot from volume vol-0d585d48213213d01 for instance i-09eab02eb24cb9d1d
creating new snapshot from volume vol-0c48979c6b7df1514 for instance i-09eab02eb24cb9d1d
creating new snapshot from volume vol-0c79befcb7f50fb07 for instance i-09eab02eb24cb9d1d
$ timewarp ec2 list i-09eab02eb24cb9d1d
$ # no output
# actually create an unnamed checkpoint
$ bin/timewarp ec2 create i-09eab02eb24cb9d1d
$ timewarp ec2 list i-09eab02eb24cb9d1d
checkpoint-time checkpoint-id   checkpoint-name
2017-08-18 11:24:31+00:00       f0163084-db6b-4778-a5c3-e8fefac00c8e    None
# create a checkpoint named "test checkpoint"
$ timewarp ec2 create -n "test checkpoint" i-09eab02eb24cb9d1d
$ timewarp ec2 list i-09eab02eb24cb9d1d
checkpoint-time checkpoint-id   checkpoint-name
2017-08-18 11:34:07+00:00       0e8829e8-16dc-4b7c-b87a-b674e570398c    test checkpoint
2017-08-18 11:24:31+00:00       f0163084-db6b-4778-a5c3-e8fefac00c8e    None
# restore the unnamed snapshot, deleting the current volumes, but creating a backup of the current state
$ timewarp ec2 restore -f --current-checkpoint i-09eab02eb24cb9d1d f0163084-db6b-4778-a5c3-e8fefac00c8e
$ timewarp ec2 list i-09eab02eb24cb9d1d
checkpoint-time checkpoint-id   checkpoint-name
2017-08-18 11:57:32+00:00       8a44996a-da65-4a06-859e-8ef6c2f039b6    timewarp restore checkpoint
2017-08-18 11:34:07+00:00       0e8829e8-16dc-4b7c-b87a-b674e570398c    test checkpoint
2017-08-18 11:24:31+00:00       f0163084-db6b-4778-a5c3-e8fefac00c8e    None
# delete the automatic checkpoint
$ timewarp ec2 delete i-09eab02eb24cb9d1d 8a44996a-da65-4a06-859e-8ef6c2f039b6
$ timewarp ec2 list i-09eab02eb24cb9d1d
checkpoint-time checkpoint-id   checkpoint-name
2017-08-18 11:34:07+00:00       0e8829e8-16dc-4b7c-b87a-b674e570398c    test checkpoint
2017-08-18 11:24:31+00:00       f0163084-db6b-4778-a5c3-e8fefac00c8e    None
```

# Further plans
- Add more unit tests
- Roll back restore when an error occurs (e.g. start instance again)
- Add a parameter for asynchronous mode
- Upload to pypi
- Show instance id when listing checkpoints
- Provide more feedback during operation
- Bash completion
- Support for other clouds
