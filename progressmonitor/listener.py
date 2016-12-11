import logging

def click_progress_listener(progressbar):
    def listen(m):
        progressbar.pos = m.progress * progressbar.length
        progressbar.label = m.message
        progressbar.update(0)
        if m.is_done:
            progressbar.render_finish()
    return listen


def log_listener(log:logging.Logger=None, level=logging.INFO):
    """Progress Monitor listener that logs all updates to the given logger"""
    if log is None:
        log = logging.getLogger("ProgressMonitor")
    def listen(monitor):
        name = "{}: ".format(monitor.name) if monitor.name is not None else ""
        perc = int(monitor.progress * 100)
        msg = "[{name}{perc:3d}%] {monitor.message}".format(**locals())
        log.log(level, msg)
    return listen