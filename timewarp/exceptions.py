
class NotImplemented(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, args, kwargs)

class NoSuchVirtualMachine(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, args, kwargs)

class InvalidOperation(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, args, kwargs)
        self._msg = args[0]

    def __str__(self):
        return self._msg

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
