import time
from progressmonitor import ProgressMonitor, listener, monitored

# Setup a dummy supertask with subtask
@monitored(10)
def supertask(monitor):
    monitor.update(2, "Started supertask")
    time.sleep(0.5)
    my_subtask(monitor.submonitor(4))
    time.sleep(0.5)

@monitored(100)
def my_subtask(monitor):
    monitor.update(10)
    for _ in range(5):
        time.sleep(0.5)
        monitor.update(10, "Working on subtask!")

# Run supertask with click progress bar
print("\n\n#### With progress bar ####\n")
m = ProgressMonitor()
import click
bar = click.progressbar(length=100, bar_template='[%(bar)s] %(label)s')
m.add_listener(listener.click_progress_listener(bar))
supertask(m)

# Run supertask with logging
print("\n\n#### With progress via logging ####\n")
m = ProgressMonitor()
import logging
logging.basicConfig(level=logging.INFO)
m.add_listener(listener.log_listener())
supertask(m)
