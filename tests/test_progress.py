from nose.tools import assert_almost_equal, assert_equal

from progressmonitor import ProgressMonitor


def test_submonitors():
    monitor = ProgressMonitor()
    monitor.begin(100)
    monitor.update(20)
    assert_almost_equal(monitor.progress, .2)

    sm1 = monitor.submonitor(20)
    assert_almost_equal(sm1.progress, 0)
    sm1.begin(10)

    assert_almost_equal(monitor.progress, .2)
    assert_almost_equal(sm1.progress, 0)

    sm1.update(5)
    assert_almost_equal(sm1.progress, .5)
    assert_almost_equal(monitor.progress, .2 + .5*.2)

    sm1.done()
    assert_almost_equal(sm1.progress, 1)
    assert_almost_equal(monitor.progress, .2 + .2)

    # Recursive submonitors should work
    sm2 = monitor.submonitor(60)
    sm2.begin(10)

    subsub = sm2.submonitor(5)
    subsub.begin(2)
    subsub.update(1)

    assert_almost_equal(subsub.progress, .5)
    assert_almost_equal(sm2.progress, .5 * .5)
    assert_almost_equal(monitor.progress, .2 + .2 + .6*.5*.5)

    sm2.done()
    assert_almost_equal(subsub.progress, .5)
    assert_almost_equal(sm2.progress, 1)
    assert_almost_equal(monitor.progress, 1)

    # Updates over 100% should not work
    subsub.update()
    assert_almost_equal(subsub.progress, 1)
    assert_almost_equal(sm2.progress, 1)
    assert_almost_equal(monitor.progress, 1)

    sm2.update(10)
    monitor.update(10)
    assert_almost_equal(subsub.progress, 1)
    assert_almost_equal(sm2.progress, 1)
    assert_almost_equal(monitor.progress, 1)

def test_message():
    monitor = ProgressMonitor()
    monitor.begin(100, "Monitor", "First step")
    assert_equal(monitor.message, "First step")

    monitor.update(20, "Second step")
    assert_equal(monitor.message, "Second step")

    sm2 = monitor.submonitor(60)
    sm2.begin(10, "Submonitor", "Subtask")
    assert_equal(monitor.message, "Subtask")

    sm2.update(message="Subtask update")
    assert_equal(monitor.message, "Subtask update")

    sm2.done()
    assert_equal(monitor.message, "Submonitor done")


