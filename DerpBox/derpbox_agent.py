#!/usr/bin/env python

"""derpbox_agent.py: module containing DerpBoxAgent and other related classes"""

import argparse
import json
import threading
from time import sleep, time as get_time
import requests
from watchdog.observers import Observer
from derpbox_synchronizer import DerpboxSynchronizer
from eventhandlers import MasterChangeHandler, DirChangeHandler
from derpbox_flask_app import \
    app, get_last_modified_time, update_sync_time_file, \
    sync_with, initialize as app_initialize
import Queue
import datetime

__author__ = "Waris Boonyasiriwat"
__copyright__ = "Copyright 2017 by Waris Boonyasiriwat"

parser = argparse.ArgumentParser(description='Derpbox Agent which '
                                             'provides necessary services '
                                             'for Derpbox Clients such as file list'
                                             'or file downloads')
parser.add_argument(
    'rootpath',
    help='File path with which the agent will be bound')
parser.add_argument(
    'port',
    help='Port to bind the agent to')
parser.add_argument(
    '--is-master', dest="is_master", action='store_true',
    help='Defined if this is the master')
parser.add_argument(
    '--master-host', dest="master_host", metavar='ip or hostname',
    help='Host of the master to periodically sync against')
parser.add_argument(
    '--master-port', dest="master_port", metavar='portnum', type=int,
    help='Port of the master to periodically sync against')

args = parser.parse_args()
app_data = app_initialize(args)
client_event_queue = Queue.Queue()
last_push_time = get_time()
lock = threading.Lock()


def server_thread():
    app.run(host='0.0.0.0', port=app_data.local_port)


def __master_change_handler():
    lock.acquire()

    update_sync_time_file()

    lock.release()


def __server_sync_time():
    response = requests.get("http://%s:%d/derpbox/api/last_modified_time" % (args.master_host, args.master_port))
    response_obj = json.loads(response.text)
    return float(response_obj['lastModified'])


def __client_change_handler():
    lock.acquire()

    change_time = get_time()
    client_event_queue.put(change_time)

    lock.release()


def __push_to_master():
    global last_push_time
    client = DerpboxSynchronizer(app_data.root_dir, args.master_host, app_data.local_port, args.master_port)

    # Sync file needs to be updated before sync, because it syncs to the
    # State at the time of call, not the time after
    last_push_time = get_time()
    client.push()
    update_sync_time_file()


def __timestamp_2str(change_time):
    return datetime.datetime.fromtimestamp(change_time).strftime('%Y-%m-%d %H:%M:%S')


def __handle_event_queue():
    try:
        while True:
            change_time = client_event_queue.get(block=False)

            if change_time > last_push_time:
                print "Pushing client change event at %s" % __timestamp_2str(change_time)
                __push_to_master()
    except Queue.Empty:
        pass
        # Queue is empty, regular case.  Do nothing


def __run_client_job():
    master_host = args.master_host
    master_port = args.master_port

    # Setup handler for file changes, for pushing changes
    event_handler = DirChangeHandler(__client_change_handler)
    observer = Observer()
    observer.schedule(event_handler, path=app_data.root_dir, recursive=True)
    observer.start()

    try:
        while True:
            lock.acquire()
            last_synctime = float(get_last_modified_time())
            server_synctime = __server_sync_time()

            if server_synctime > last_synctime:
                print "Master is newer, syncing with master"
                event_handler.enable(False)
                sync_with(master_host, master_port)
                event_handler.enable(True)
            else:
                __handle_event_queue()

            lock.release()
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def __run_master_job():
    event_handler = MasterChangeHandler(update_sync_time_file)
    observer = Observer()
    observer.schedule(event_handler, path=app_data.root_dir, recursive=True)
    observer.start()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()


if __name__ == '__main__':
    print "Managed directory is: %s" % app_data.root_dir

    # Do other things, start the sync job if not master
    if args.is_master:
        print "Starting as Master - waiting for requests"
    else:
        if args.master_port is None or args.master_host is None:
            print "master_port and master_host is required in slave mode"
            exit(1)

    t = threading.Thread(name="DerpboxServer", target=server_thread)
    t.start()

    if not args.is_master:
        print "Synchronizing with master on %s:%s" % (args.master_host, args.master_port)
        __run_client_job()
    else:
        # Setup handler for file changes, for pushing changes
        __run_master_job()

    t.join()
