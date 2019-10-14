import json
import os
from glob import glob

from constants import *


class PyImgBatch:

    def __init__(self, args):
        self.args = vars(args)
        self.config = []
        print(args)
        raw_config = self._readConfig()
        self._processConfig(raw_config)

    def _readConfig(self):
        with open(self.args[CONST.CONFIGFILE]) as config_file:
            raw_config = json.load(config_file)
        return raw_config

    def _processConfig(self, raw_config):
        for entry in raw_config:
            print(entry)

            # resolve websets
            if CONFKEYS.WEBSET in entry:
                webset_value = entry[CONFKEYS.WEBSET]
                if webset_value in CONST.WEBSETS:
                    for index in range(1, CONST.WEBSETS[webset_value]+1):
                        print(index)
                else:
                    print("ERROR")
                print(entry['webset'])

            else:
                self.config.append(entry)
        print(raw_config)
        print(self.config)

    def _createFilesArray(self, supported_files=CONST.SUPPORTED_FILES): 
        self.img_files_names = [os.path.abspath(file) for ext in supported_files for file in glob(os.path.join(self.args[ARGS.SOURCE], ext))]
        print(self.img_files_names)

    def _processFiles(self):
        for img_file_name in self.img_files_names:
            print(img_file_name)

    def exec(self):
        self._createFilesArray()
        self._processFiles()