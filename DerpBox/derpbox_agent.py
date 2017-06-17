#!/usr/bin/env python

"""derpbox_agent.py: module containing DerpBoxAgent and other related classes"""

import argparse
import base64
import json
import os
import threading
from time import time as get_time, sleep

import requests
from flask import Flask, jsonify, abort, request
from watchdog.observers import Observer

import file_utils
from derpbox_synchronizer import DerpboxSynchronizer
from eventhandlers import MasterChangeHandler, DirChangeHandler

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

root_path = os.path.abspath(args.rootpath).replace('\\', '/')
derpbox_root_dir = root_path if root_path.endswith('/') else root_path + '/'
local_port = args.port
last_modified_time_path = "./.last_modified_time_" + local_port
synced = False

app = Flask(__name__)

lock = threading.Lock()

@app.route('/')
def index():
    msg = """
        Welcome to DerpBox Agent
    """
    return msg


@app.route('/derpbox/api/files', methods=['GET'])
def get_all_files():
    return __get_all_files()


def __get_all_files():
    file_list = []
    obj_id = 0
    paths = file_utils.get_paths_recursive(derpbox_root_dir)
    for p in paths:
        file_obj = file_utils.create_file_obj(obj_id, derpbox_root_dir, p)
        obj_id = obj_id + 1
        file_list.append(file_obj)
    return jsonify(file_list)


@app.route('/derpbox/api/files/<int:file_id>', methods=['GET'])
def get_file_data(file_id):
    paths =file_utils.get_paths_recursive(derpbox_root_dir)
    path = ""
    try:
        path = paths[file_id]
    except KeyError:
        abort(400, {'message': 'Specified file id %d not found' % file_id})
    if os.path.isdir(derpbox_root_dir + path):
        abort(500, {'message': 'Is a directory'})

    f = open(derpbox_root_dir + path, "rb")
    data = f.read()
    f.close()

    response = {
        'id': file_id,
        'path': path,
        'data': base64.b64encode(data)
    }

    return jsonify(response)

@app.route('/derpbox/api/sync_with_caller', methods=['PUT'])
def sync_with_caller():
    """
    Not very restful but reduces a lot of duplicate code
    
    Tell the agent to synchronize against the caller
    """

    # Act as a client against the master
    lock.acquire()

    try:
        remote_port = request.json['port']
    except KeyError:
        remote_port = 5000

    __sync_with(request.remote_addr, remote_port)

    lock.release()

    return __get_all_files()


def __sync_with(remote_host, remote_port):
    client = DerpboxSynchronizer(derpbox_root_dir, remote_host, local_port, remote_port)
    client.sync()

    update_sync_time_file()


def update_sync_time_file():
    f = open(last_modified_time_path, "w")
    f.truncate()
    f.write(str(get_time()))
    f.close()


@app.route('/derpbox/api/last_modified_time', methods=['GET'])
def get_last_modified():
    time = __get_last_modified_time()

    return jsonify({ 'lastModified': time })


def __get_last_modified_time():
    f = open(last_modified_time_path, "r")
    time = f.read()
    return time


def server_thread():
    app.run(host='0.0.0.0', port=local_port)


def __server_sync_time():
    response = requests.get("http://%s:%d/derpbox/api/last_modified_time" % (master_host, master_port))
    response_obj = json.loads(response.text)
    return float(response_obj['lastModified'])

def __push_to_master():
    lock.acquire()
    client = DerpboxSynchronizer(derpbox_root_dir, args.master_host, local_port, args.master_port)
    client.push()
    lock.release()

def __run_client_job():
    global master_host, master_port, event_handler, observer
    master_host = args.master_host
    master_port = args.master_port

    # Setup handler for file changes, for pushing changes
    event_handler = DirChangeHandler(__push_to_master)
    observer = Observer()
    observer.schedule(event_handler, path=derpbox_root_dir, recursive=True)
    observer.start()
    try:
        while (True):
            last_synctime = float(__get_last_modified_time())
            server_synctime = __server_sync_time()

            if server_synctime > last_synctime:
                print "Master is newer, syncing with master"
                lock.acquire()

                event_handler.enable(False)
                __sync_with(master_host, master_port)
                event_handler.enable(True)

                lock.release()

            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def __run_master_job():
    global event_handler, observer
    event_handler = MasterChangeHandler(update_sync_time_file)
    observer = Observer()
    observer.schedule(event_handler, path=derpbox_root_dir, recursive=True)
    observer.start()
    try:
        while (True):
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()


if __name__ == '__main__':
    print "Managed directory is: %s" % derpbox_root_dir

    # Do other things, start the sync job if not master
    if args.is_master:
        print "Starting as Master - waiting for requests"
    else:
        if args.master_port is None or args.master_host is None:
            print "master_port and master_host is required in slave mode"
            exit(1)

    t = threading.Thread( name="DerpboxServer", target=server_thread )
    t.start()

    if not args.is_master:
        print "Synchronizing with master on %s:%s" % (args.master_host, args.master_port)
        __run_client_job()
    else:
        # Setup handler for file changes, for pushing changes
        __run_master_job()

    t.join()

