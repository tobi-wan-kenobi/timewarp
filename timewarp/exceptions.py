
class NotImplemented(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, args, kwargs)

class NoSuchVirtualMachine(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, args, kwargs)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
