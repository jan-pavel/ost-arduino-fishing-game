from time import ticks_diff, ticks_ms

class Timer:
    def __init__(self, duration_ms=None, one_shot=True):
        self._start_time = None
        self._duration_ms = duration_ms
        self._is_running = False
        self._one_shot = one_shot
        self._on_timer_end = None

    def start(self):
        self._start_time = ticks_ms()
        self._is_running = True

    def stop(self):
        self._is_running = False

    @property
    def duration_ms(self):
        return self._duration_ms
    
    @duration_ms.setter
    def duration_ms(self, value):
        if value is not None and value < 0:
            raise ValueError("Duration must be non-negative or None.")
        self._duration_ms = value

    @property
    def on_timer_end(self):
        return self._on_timer_end

    @on_timer_end.setter
    def on_timer_end(self, callback):
        if not callable(callback):
            raise ValueError("Callback must be callable.")
        self._on_timer_end = callback

    @property
    def elapsed_ms(self):
        if self._start_time is None:
            raise ValueError("Timer has not been started.")
        return ticks_diff(ticks_ms(), self._start_time)
    
    @property
    def has_ended(self):
        if self._duration_ms is None:
            return False
        return self.elapsed_ms >= self._duration_ms

    def update(self):
        if not self._is_running:
            return
        if self.has_ended:
            if callable(self._on_timer_end):
                self._on_timer_end()
            if self._one_shot:
                self.stop()
            else:
                self.start()