import json
import os
import logging

from os.path import basename, join, realpath
from glob import glob
from tqdm import tqdm
from time import sleep


from pprint import pprint, pformat

from .constants import *
from .core import *
from .helper import *


class PyImgBatch:

    def __init__(self, args):
        self.args = vars(args)
        self.config = []
        print(args)

        self._no_progress_bar = self.args.get(ARGS.NO_PROGRESS, False)

        raw_config = self._read_config()
        self._process_config(raw_config)

    def __del__(self):
        self._image_progress_bar.close()
        self._main_progress_bar.close()

    def _read_config(self):
        with open(self.args[CONST.CONFIGFILE]) as config_file:
            raw_config = json.load(config_file)
        return raw_config
        # TODO: read from stdin

    def _process_config(self, raw_config):
        for entry in raw_config:
            pprint(entry)
            # resolve websets
            if CONFKEY.WEBSET in entry:
                self._create_webset_entries(entry)
            else:
                self.config.append(entry)
        logging.debug("raw config:")
        logging.debug(pformat(raw_config))
        logging.debug("solved config:")
        logging.debug(pformat(self.config))

    def _create_webset_entries(self, entry):
        webset_value = entry[CONFKEY.WEBSET]
        if webset_value in CONST.WEBSETS:
            for index in range(1, CONST.WEBSETS[webset_value]+1):
                new_entry = entry.copy()
                new_entry.update({CONFKEY.WIDTH: to_int_or_none(entry.get(CONFKEY.WIDTH, None), multiplier=index)})
                new_entry.update({CONFKEY.HEIGHT: to_int_or_none(entry.get(CONFKEY.HEIGHT, None), multiplier=index)})
                new_entry.update({CONFKEY.WEBSETADDON: f"@{index}x"})
                self.config.append(new_entry)
        else:
            print("ERROR")

    def _create_files_array(self, supported_files=CONST.SUPPORTED_FILES):
        self.source_files_names = [os.path.abspath(file) for ext in supported_files for file in glob(
            os.path.join(self.args[ARGS.SOURCE], ext))]
        print(self.source_files_names)

    def _process_files(self):
        # TODO: Format the progress bars more meanfully
        self._image_progress_bar = ProgressBar(len(self.config), disable=self._no_progress_bar)
        self._main_progress_bar = ProgressBar(len(self.source_files_names), disable=self._no_progress_bar)
        for source_file_name in self.source_files_names:
            self._process_file(source_file_name)
            self._main_progress_bar.update()

    def _process_file(self, source_filename):
        self._image_progress_bar.reset()
        self._print(f"progressing: {basename(source_filename)}")
        logging.info(f"progressing: {basename(source_filename)}")
        for entry in self.config:
            current_image = CurrentImage(self.args, source_filename, ConfigEntry(entry), self._print)            
            current_image.generate()
            self._image_progress_bar.update()

    def _print(self, *args):
        if not self._no_progress_bar:
            self._image_progress_bar.write(*args)
        else:
            print(*args)

    def exec(self):
        self._create_files_array()
        self._process_files()

