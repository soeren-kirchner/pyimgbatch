import json
import os

from os.path import basename
from glob import glob
from tqdm import tqdm
from time import sleep
from PIL import Image
#from PIL import ImageCms

from constants import *
from helper import Size, ProgressBar


class PyImgBatch:

    def __init__(self, args):
        self.args = vars(args)
        self.config = []
        print(args)
        raw_config = self._readConfig()
        self._processConfig(raw_config)

    def __del__(self):
        self._image_progress_bar.close()
        self._main_progress_bar.close()

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

    def _create_files_array(self, supported_files=CONST.SUPPORTED_FILES):
        self.source_files_names = [os.path.abspath(file) for ext in supported_files for file in glob(
            os.path.join(self.args[ARGS.SOURCE], ext))]
        print(self.source_files_names)

    def get_destination_size(self, source_size, designated_size):
        print("source:", source_size)
        print("designated:", designated_size)
        if designated_size.width is not None and designated_size.height is not None:
            return designated_size
        elif designated_size.width is None and designated_size.height is not None:
            return Size(int(source_size.width/(source_size.height/designated_size.height)), designated_size.height)
        elif designated_size.width is not None and designated_size.height is None:
            return Size(designated_size.width, int(source_size.height/(source_size.width/designated_size.width)))
        else:
            raise Exception("Destination size not computable")

    def _process_files(self):
        # TODO: Format the progress bars more meanfully
        self._image_progress_bar = ProgressBar(
            len(self.config), disable=self.args.get(ARGS.NO_PROGRESS, False))
        self._main_progress_bar = ProgressBar(
            len(self.source_files_names), disable=self.args.get(ARGS.NO_PROGRESS, False))
        for source_file_name in self.source_files_names:
            self._process_file(source_file_name)
            self._main_progress_bar.update()

    def _process_file(self, source_file_name):
        self._image_progress_bar.reset()
        for entry in self.config:
            self._image_progress_bar.set_description(
                basename(source_file_name))
            self._process_file_for_config(source_file_name, entry)
            self._image_progress_bar.update()

    def _process_file_for_config(self, source_file_name, config_entry):
        self._print(self._destination_folder(source_file_name, config_entry))
        self._print(self._destination_file_name(
            source_file_name, config_entry))
        sleep(.2)

    def _destination_folder(self, source_file_name, config_entry):
        return source_file_name

    def _destination_file_name(self, source_file_name, config_entry):
        return source_file_name

    def _print(self, *args):
        if not self.args.get(ARGS.NO_PROGRESS, False):
            self._image_progress_bar.write(*args)
        else:
            print(*args)

    def exec(self):
        self._create_files_array()
        self._process_files()
