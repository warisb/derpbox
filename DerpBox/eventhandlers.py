#!/usr/bin/env python

"""foobar.py: description"""

from watchdog.events import FileSystemEventHandler

__author__ = "Waris Boonyasiriwat"
__copyright__ = "Copyright <year>"

class MasterChangeHandler(FileSystemEventHandler):
    def __init__(self, fn_updatesynctime):
        self.fn_updatesynctime = fn_updatesynctime

    def on_any_event(self, event):
        print "Detected changes, updating sync time"
        self.fn_updatesynctime()


class DirChangeHandler(FileSystemEventHandler):
    def __init__(self, fnpush):
        self.enabled = True
        self.fnpush = fnpush

    def enable(self, en):
        self.enabled = en

    def on_any_event(self, event):
        if not self.enabled:
            return

        print "Detected changes, pushing to server"
        self.fnpush()
