#!/usr/bin/env python

"""derpbox_agent.py: module containing DerpBoxAgent and other related classes"""

__author__ = "Waris Boonyasiriwat"
__copyright__ = "Copyright 2017 by Waris Boonyasiriwat"

from flask import Flask, jsonify, abort
import os
import file_utils
import base64

derpbox_root_dir = "C:\\Users\\Waris\\derpbox_sandbox\\"  # Make this an input later

app = Flask(__name__)

@app.route('/')
def index():
    msg = """
        Welcome to DerpBox Agent
    """
    return msg


@app.route('/derpbox/api/files', methods=['GET'])
def get_all_files():
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
