#!/usr/bin/env python

"""file_utils.py: convenient file operations used by derpbox"""

__author__ = "Waris Boonyasiriwat"
__copyright__ = "Copyright 2017"

import os
import hashlib


def md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_file_obj(id, root_path, path):
    file_obj = {
        'id': id,
        'path': path,
        'isDirectory': os.path.isdir(root_path + path),
    }
    if not file_obj['isDirectory']:
        file_obj['hash'] = md5(root_path + path)
    return file_obj


def get_paths_recursive(root_path):
    paths = []
    for root, dirs, files in os.walk(root_path):
        for f in files:
            path = os.path.relpath(os.path.join(root, f), root_path)
            paths.append(path.replace('\\', '/'))
        for d in dirs:
            path = os.path.relpath(os.path.join(root, d), root_path)
            paths.append(path.replace('\\', '/'))

    return paths
