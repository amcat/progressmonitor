# Progress Monitor

Python classes for tracking (sub)task progress (inspired by Eclipse ProgressMonitor, but more pythonic)

## Installation

Install directly from pypi:

```{sh}
pip install progressmonitor
```

## Usage

(See also [example.py](example.py))

### Initialization and task updates

A monitor keeps track of progress in units specified by the task.
A progress monitor is initialized with .begin(), which sets the total amount of work to be done.
Calls to update() (and optionally, done()) increment the amount of work done

Note that task name and total work is set on .begin(), not on construction, because normally
the task will receive a monitor from the code calling it.  

```{py}
m = ProgressMonitor()
m.begin("task name", total_units[, message])
m.update(units[, message])
[m.done()]
```

### Adding listeners

You can query progress and message directly with m.progress and m.message,
but in many cases you want to add a listener, which is called with the monitor as argument for every update.
A listener that outputs to the python logging facility is included:

```{py}
from progressmonitor import log_listener
m.add_listener(log_listener(mylog, logging.DEBUG))
```

### Submonitors

In most cases, a task will call various other tasks as part of its work.
These subtasks can report progress to the monitor.
Since the task and subtasks don't know how much total work the other has, two pieces of information are given:
The weight (amount of units) of the subtask for the main task and the total amount of units in the subtask.
The first is given on creating the sub monitor (in the main task), the second on calling .begin (in the subtask):

```{py}
# in the main task:
m = ProgressMonitor()
m.begin(100)
sm = m.submonitor(50)  # this submonitor will count for 50 out of the main monitor's 100 units

# in the subtask:
sm.begin(10, "subtask name")  # this submonitor has 10 units of work in total
sm.update(1)  # this will count as 1/10 * 50 = 5 out of 100 units of the main task monitor
sm.done()     # this will 'update' the remainig units of m's work, i.e. main progress will now be 50%
```
### Context Managers and Decorators

To reduce the boilerplate in working with progress monitors, two context managers and a decorator are provided:

```{py}
@monitored(100)
def supertask(monitor):
    ...
    with monitor.submonitor(50) as sm:
        subtask(sm)

@monitored(10, name="My first subtask")
def subtask(monitor):
    monitor.update(5)  # this will update 5/10 * 50/100 = 25% of supertask's work
```
