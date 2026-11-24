from tester.StateManager import StateManagerMixin


class FakeTimer:
    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback
        self.daemon = False
        self.started = False

    def start(self):
        self.started = True


def test_update_timer_does_not_keep_process_alive(monkeypatch):
    manager = StateManagerMixin()
    manager.running = True
    manager._update_tester = lambda: None
    timers = []

    def make_timer(interval, callback):
        timer = FakeTimer(interval, callback)
        timers.append(timer)
        return timer

    monkeypatch.setattr("tester.StateManager.threading.Timer", make_timer)

    manager._timer_update()

    assert len(timers) == 1
    assert timers[0].daemon is True
    assert timers[0].started is True
