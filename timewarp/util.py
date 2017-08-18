
class Event(object):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg

callbacks = []

def emit(event):
    if isinstance(event, basestring):
        event = Event(event)
    for cb in callbacks:
        cb(event)

def register(cb):
    callbacks.append(cb)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
