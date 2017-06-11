#!/usr/bin/env python

"""derpbox_agent.py: module containing DerpBoxAgent and other related classes"""

from derpbox_client import DerpboxClient
from flask import Flask, jsonify, abort, request
import os
import file_utils
import base64

__author__ = "Waris Boonyasiriwat"
__copyright__ = "Copyright 2017 by Waris Boonyasiriwat"

import argparse

parser = argparse.ArgumentParser(description='Derpbox Agent which '
                                             'provides necessary services '
                                             'for Derpbox Clients such as file list'
                                             'or file downloads')
parser.add_argument(
    'root_path',
    help='File path with which the agent will be bound')
parser.add_argument(
    'port',
    help='Port to bind the agent to')
args = parser.parse_args()

root_path = os.path.abspath(args.root_path).replace('\\', '/')
derpbox_root_dir = root_path if root_path.endswith('/') else root_path + '/'
local_port = args.port

app = Flask(__name__)

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
    try:
        remote_port = request.json['port']
    except KeyError:
        remote_port = 5000

    client = DerpboxClient(derpbox_root_dir, request.remote_addr, remote_port)
    client.sync()

    return __get_all_files()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=local_port)
