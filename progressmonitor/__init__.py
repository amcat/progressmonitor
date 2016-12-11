import inspect
import logging
from contextlib import contextmanager

log = logging.getLogger(__name__)

from functools import wraps


def monitored(total: int, name=None, message=None):
    """
    Decorate a function to automatically begin and end a task on the progressmonitor.
    The function must have a parameter called 'monitor'
    """
    def decorator(f):
        nonlocal name
        monitor_index = list(inspect.signature(f).parameters.keys()).index('monitor')
        if name is None:
            name=f.__name__
        @wraps(f)
        def wrapper(*args, **kargs):
            if len(args) > monitor_index:
                monitor = args[monitor_index]
            elif 'monitor' in kargs:
                monitor = kargs['monitor']
            else:
                monitor = kargs['monitor'] = NullMonitor()
            with monitor.task(total, name, message):
                f(*args, **kargs)
        return wrapper
    return decorator


def log_listener(log:logging.Logger=None, level=logging.INFO):
    """Progress Monitor listener that logs all updates to the given logger"""
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

    You can also use the context managers .task and .subtask and @monitored decorator:

    @monitored(100)
    def supertask(monitor):
        ...
        with monitor.submonitor(50) as sm:
            subtask(sm)

    @monitored(10, name="My first subtask")
    def subtask(monitor):
        monitor.update(5)  # this will update 5/10 * 50 = 25 of supertask's work
    """

    def __init__(self):
        self.total = None  # need to call begin before starting!
        self.name = None  # name is given with begin(.)
        self.worked = 0
        self.listeners = set()
        self.sub_monitors = {}  # monitor : units of (my) work

    def begin(self, total: int, name=None, message=None):
        """Call before starting work on a monitor, specifying name and amount of work"""
        self.total = total
        message = message or name or "Working..."
        self.name = name or "ProgressMonitor"
        self.update(0, message)

    @contextmanager
    def task(self, total: int, name=None, message=None):
        """Wrap code into a begin and end call on this monitor"""
        self.begin(total, name, message)
        try:
            yield self
        finally:
            self.done()

    @contextmanager
    def subtask(self, units: int):
        """Create a submonitor with the given units"""
        sm = self.submonitor(units)
        try:
            yield sm
        finally:
            if sm.total is None:
                # begin was never called, so the subtask cannot be closed
                self.update(units)
            else:
                sm.done()

    @property
    def progress(self)-> float:
        """What percentage (range 0-1) of work is done (including submonitors)"""
        if self.total is None:
            return 0
        my_progress = self.worked
        my_progress += sum(s.progress * weight
                           for (s, weight) in self.sub_monitors.items())
        return min(1, my_progress / self.total)

    def update(self, units: int=1, message: str=None):
        """Increment the monitor with N units worked and an optional message"""
        if self.total is None:
            raise Exception("Cannot call progressmonitor.update before calling begin")
        self.worked = min(self.total, self.worked+units)
        if message:
            self.message = message
        for listener in self.listeners:
            listener(self)

    def add_listener(self, func):
        """Add a function to listen to updates"""
        self.listeners.add(func)

    def remove_listener(self, func):
        """REmove a function from the listeners"""
        self.listeners.remove(func)

    def submonitor(self, units: int, *args, **kargs) -> 'ProgressMonitor':
        """
        Create a sub monitor that stands for N units of work in this monitor
        The sub task should call .begin (or use @monitored / with .task) before calling updates
        """
        submonitor = ProgressMonitor(*args, **kargs)
        self.sub_monitors[submonitor] = units
        submonitor.add_listener(self._submonitor_update)
        return submonitor

    def _submonitor_update(self, submonitor):
        self.update(0, submonitor.message)

    def done(self, message: str=None):
        """
        Signal that this task is done.
        This is completely optional and will just call .update with the remaining work.
        """
        if message is None:
            message = "{self.name} done".format(**locals()) if self.name else "Done"
        self.update(units=self.total - self.worked, message=message)


class NullMonitor(ProgressMonitor):
    """Dummy monitor that will accept all calls and do nothing"""
    def submonitor(self, total, *args, **kargs):
        return NullMonitor()

    def update(self, *args, **kargs):
        pass

