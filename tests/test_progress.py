from nose.tools import assert_almost_equal, assert_equal, assert_true, assert_false

from progressmonitor import ProgressMonitor, monitored


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
    assert_false(monitor.is_done)
    assert_true(sm1.is_done)

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

    assert_true(monitor.is_done)
    assert_true(sm2.is_done)

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


def test_contextmanager():
    monitor = ProgressMonitor()
    with monitor.task(10, "Taak"):
        assert_equal(monitor.message, "Taak")
        assert_equal(monitor.progress, 0)

        monitor.update(5)
        assert_equal(monitor.progress, .5)
    assert_equal(monitor.progress, 1)


def test_subtask():
    main_monitor = ProgressMonitor()

    def my_subtask(monitor):
        with monitor.task(2, "Subtask"):
            monitor.update()
            assert_equal(monitor.progress, .5)
            assert_equal(main_monitor.progress, .5 * .5)

    with main_monitor.task(10, "Main"):
        with main_monitor.subtask(5) as sm:
            my_subtask(sm)
        assert_equal(main_monitor.progress, .5)  # subtask is forced 'done'


def test_decorator():
    @monitored(10)
    def mysubtask(monitor):
        monitor.update(5)
        assert_equal(monitor.name, "mysubtask")
        assert_equal(monitor.progress, .5)
        assert_equal(m.progress, .375)

    m = ProgressMonitor()
    with m.task(20):
        m.update(5)
        with m.subtask(5) as sub:
            mysubtask(sub)
            assert_equal(m.progress, .5)
        assert_equal(m.message, "mysubtask done")
    assert_equal(m.progress, 1)

    # test robustness against subtask never calling begin
    m = ProgressMonitor()
    with m.task(10):
        with m.subtask(5) as sub:
            pass
        assert_equal(m.progress, .5)



