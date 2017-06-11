#!/usr/bin/env python

"""derpbox_client.py: the slave process used to sync localhost against any specified master"""

import requests
import file_utils
import json
import base64
import os
import errno

__author__ = "Waris Boonyasiriwat"
__copyright__ = "Copyright 2017"

derpbox_root_dir = "C:\\Users\\Waris\\derpbox_sandbox_client\\"  # Make this an input later

class DerpboxClient:
    def __init__(self, root_dir, master_host, master_port=5000):
        """
        Client for synchronizing localhost with the master_host
        :param master_host: ip address of the master to sync to
        :param master_port: port of the master to sync to
        """

        self.master_host = master_host
        self.master_port = master_port
        self.root_dir = root_dir

    def sync(self):
        # Get own file list
        local_list = file_utils.get_paths_recursive(self.root_dir)

        # Get master file list
        request_url = "http://%s:%d/derpbox/api/files" % (self.master_host, self.master_port)
        response = requests.get(request_url)
        master_files = json.loads(response.text)

        # If master deleted, also delete local, then refresh local list
        self.__process_delete(local_list, master_files)
        local_list = file_utils.get_paths_recursive(self.root_dir)

        # If local file exists
        self.__process_files_added(local_list, master_files)
        local_list = file_utils.get_paths_recursive(self.root_dir)

        # Finally, create empty directories
        self.__process_dirs_added(local_list, master_files)

        print("Sync completed")

    def __find_file_in_master(self, path, master_files):
        for file_obj in master_files:
            if file_obj['path'] == path:
                return file_obj
        return None

    @staticmethod
    def __same_dir_exists_in_local(path, local_list):
        for file in local_list:
            if file == path:
                return True
        return False

    def __same_file_exists_in_local(self, path, md_hash, local_list):
        for local_f in local_list:
            if local_f == path and file_utils.md5(self.root_dir + local_f) == md_hash:
                # File exists and the hash is the same
                return True
        return False

    def __download_file(self, file_id):
        request_url = "http://%s:%d/derpbox/api/files/%d" % (self.master_host, self.master_port, file_id)
        response = requests.get(request_url)
        file_obj = json.loads(response.text)

        return base64.b64decode(file_obj['data'])

    def __process_delete(self, local_list, master_files_json):
        for f in local_list:
            if self.__find_file_in_master(f, master_files_json) is None:
                # Master deleted, local should delete too
                print("Removing file %s (master deleted)" % f)
                realpath = self.root_dir + f
                if os.path.isdir(realpath):
                    os.rmdir(realpath)
                else:
                    os.remove(realpath)

    def __process_dirs_added(self, local_list, master_files_json):
        for master_file in master_files_json:
            if master_file['isDirectory']:
                if not self.__same_dir_exists_in_local(master_file['path'], local_list):
                    # Directory exists in master but not local
                    thepath = master_file['path']
                    print("Creaing directory %s (master created)" % thepath)
                    os.makedirs(self.root_dir + thepath)

    @staticmethod
    def __open_file_recursive_makedirs(filename):
        # Make directory if it doesn't already exist
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        # Then finally open the file
        return open(filename, 'wb')

    def __process_files_added(self, local_list, master_files_json):
        for master_file in master_files_json:
                if not master_file['isDirectory']:
                    if not self.__same_file_exists_in_local(master_file['path'], master_file['hash'], local_list):
                        # File exists in master but not local, download

                        data = self.__download_file(master_file['id'])

                        real_path = self.root_dir + master_file['path']
                        print(
                            ("Adding file %s (master added)" if not os.path.exists(real_path) else
                            "Replacing file %s (master modified)") % master_file['path'])

                        f = self.__open_file_recursive_makedirs(real_path)
                        f.truncate()
                        f.write(data)
                        f.close()

if __name__ == '__main__':
    derpbox_client = DerpboxClient(derpbox_root_dir, "localhost")
    derpbox_client.sync()
