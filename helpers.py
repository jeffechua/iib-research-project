from sys import stdout
import time

def write(str):
    print('\r' + str, end='')
    stdout.flush()

class Timer:

    def __init__(self, init_time = None):
        self.last = time.time() if init_time == None else init_time
        self._total = 0
        self._total_overflow = 0

    def current(self):
        return time.time() - self.last

    def current_total(self):
        return self.current() + self._total

    def total(self, dp = None):
        return self._total if dp == None else f'%.{dp}f' % self._total

    def start(self):
        self.last = time.time()
    
    def stop(self):
        self._total += time.time() - self.last

    def lap(self, dp = None):
        delta = time.time() - self.last
        self.stop()
        self.start()
        return delta if dp == None else f'%.{dp}f' % delta

