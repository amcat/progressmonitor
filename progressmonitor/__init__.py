import logging
from contextlib import contextmanager

log = logging.getLogger(__name__)

from functools import wraps


def monitored(total: int, name=None, message=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kargs):
            if 'monitor' not in kargs:
                kargs['monitor'] = NullMonitor()
            with kargs['monitor'].task(total, name, message):
                f(*args, **kargs)
        return wrapper
    return decorator


def log_listener(log:logging.Logger=None, level=logging.INFO):
    if log is None:
        log = logging.getLogger("ProgressMonitor")
    def listen(monitor):
        name = "{}: ".format(monitor.name) if monitor.name is not None else ""
        msg = "[{name}{monitor.progress:0.1f}%] {monitor.message}".format(**locals())
        log.log(level, msg)
    return listen


class ProgressMonitor(object):
    """
    A Progress Monitor keeps track of pogress of tasks with optional subtasks.

    Usage:
    m = ProgressMonitor()
    m.begin("task name", total_units[, message])
    m.update(units[, message])
    [m.done()]

    When using sub monitors, an amount of work of this monitor (e.g. 50) is delegated to the submonitor,
    who has its own total_units (e.g. 10):

    sm = m.submonitor(50)
    sm.begin("subtask name", 10)
    sm.update(1)  # this will 'update' 5 units of m's work
    sm.done()     # this will 'update' the remainig units of m's work
    """

    def __init__(self):
        self.total = None  # need to call begin before starting!
        self.worked = 0
        self.listeners = set()
        self.sub_monitors = {}  # monitor : units of (my) work

    def begin(self, total: int, name=None, message=None):
        self.total = total
        message = message or name or "Working..."
        self.name = name or "ProgressMonitor"
        self.update(0, message)

    @contextmanager
    def task(self, total: int, name=None, message=None):
        self.begin(total, name, message)
        try:
            yield self
        finally:
            self.done()

    @contextmanager
    def subtask(self, units: int):
        sm = self.submonitor(units)
        try:
            yield sm
        finally:
            sm.done()

    @property
    def progress(self):
        if self.total is None:
            return 0
        my_progress = self.worked
        my_progress += sum(s.progress * weight
                           for (s, weight) in self.sub_monitors.items())
        return min(1, my_progress / self.total)

    def update(self, units: int=1, message: str=None):
        if self.total is None:
            raise Exception("Cannot call progressmonitor.update before calling begin")
        self.worked = min(self.total, self.worked+units)
        if message:
            self.message = message
        for listener in self.listeners:
            listener(self)

    def add_listener(self, func):
        self.listeners.add(func)

    def remove_listener(self, func):
        self.listeners.remove(func)

    def submonitor(self, units: int, *args, **kargs) -> 'ProgressMonitor':
        monitor = SubMonitor(self, *args, **kargs)
        self.sub_monitors[monitor] = units
        return monitor

    def done(self, message: str=None):
        if message is None:
            message = "{self.name} done".format(**locals()) if self.name else "Done"
        self.update(units=self.total - self.worked, message=message)


class SubMonitor(ProgressMonitor):
    def __init__(self, super_monitor, *args, **kargs):
        self.super_monitor = super_monitor
        super(SubMonitor, self).__init__(*args, **kargs)

    def update(self, units=1, message: str=None):
        super(SubMonitor, self).update(units, message)
        self.super_monitor.update(0, message)

    def __hash__(self):
        return hash(id(self))


class NullMonitor(ProgressMonitor):
    def submonitor(self, total, *args, **kargs):
        return NullMonitor()

    def update(self, *args, **kargs):
        pass

