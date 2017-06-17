#!/usr/bin/env python

"""foobar.py: description"""

from watchdog.events import FileSystemEventHandler

__author__ = "Waris Boonyasiriwat"
__copyright__ = "Copyright <year>"

class MasterChangeHandler(FileSystemEventHandler):
    def __init__(self, fn_updatesynctime):
        self.fn_updatesynctime = fn_updatesynctime

    def on_any_event(self, event):
        self.fn_updatesynctime()


class DirChangeHandler(FileSystemEventHandler):
    def __init__(self, fnpush):
        self.fnpush = fnpush
        self.enabled = True

    def enable(self, enabled):
        self.enabled = enabled

    def on_any_event(self, event):
        if not self.enabled:
            return
        self.fnpush()
