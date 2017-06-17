#!/usr/bin/env python

"""foobar.py: description"""
import base64
import os
import threading

from flask import Flask, jsonify, abort, request

import file_utils
from derpbox_synchronizer import DerpboxSynchronizer
from time import time as get_time

__author__ = "Waris Boonyasiriwat"
__copyright__ = "Copyright <year>"


class FlaskAppData:
    """
        @note Flask is not super Object-oriented but I want to at least prevent usage of global variables
        ... encapsulate all flask-related data in this object
    """

    def __init__(self, args):
        root_path_temp = os.path.abspath(args.rootpath).replace('\\', '/')
        self.root_dir = root_path_temp if root_path_temp.endswith('/') else root_path_temp + '/'
        self.local_port = args.port
        self.mod_time_path = "./.last_modified_time_" + self.local_port


app_data = None
app = Flask(__name__)

lock = threading.Lock()

def initialize(args_in):
    global app_data
    app_data = FlaskAppData(args_in)

    return app_data

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
    lock.acquire()

    file_list = []
    obj_id = 0
    paths = file_utils.get_paths_recursive(app_data.root_dir)
    for p in paths:
        file_obj = file_utils.create_file_obj(obj_id, app_data.root_dir, p)
        obj_id = obj_id + 1
        file_list.append(file_obj)

    lock.release()
    return jsonify(file_list)


@app.route('/derpbox/api/files/<int:file_id>', methods=['GET'])
def download_file(file_id):
    lock.acquire()

    paths = file_utils.get_paths_recursive(app_data.root_dir)
    path = ""
    try:
        path = paths[file_id]
    except KeyError:
        abort(400, {'message': 'Specified file id %d not found' % file_id})
    if os.path.isdir(app_data.root_dir + path):
        abort(500, {'message': 'Is a directory'})

    f = open(app_data.root_dir + path, "rb")
    data = f.read()
    f.close()

    response = {
        'id': file_id,
        'path': path,
        'data': base64.b64encode(data)
    }

    lock.release()

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

    sync_with(request.remote_addr, remote_port)

    lock.release()

    return __get_all_files()


def sync_with(remote_host, remote_port):
    client = DerpboxSynchronizer(
        app_data.root_dir,
        remote_host,
        app_data.local_port,
        remote_port)

    client.sync()

    update_sync_time_file()


def update_sync_time_file():
    f = open(app_data.mod_time_path, "w")
    f.truncate()
    f.write(str(get_time()))
    f.close()


@app.route('/derpbox/api/last_modified_time', methods=['GET'])
def get_last_modified():
    lock.acquire()

    time = get_last_modified_time()

    lock.release()

    return jsonify({'lastModified': time})


def get_last_modified_time():
    try:
        f = open(app_data.mod_time_path, "r")
        time = f.read()
        f.close()
    except (OSError, IOError):
        time = 0.0
        pass
    return float(time)