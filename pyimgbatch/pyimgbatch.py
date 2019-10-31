import json
import os
import logging

from os.path import basename, join, exists
from glob import glob
from tqdm import tqdm

from pprint import pprint, pformat

from time import time

from PIL import Image
from PIL import ImageCms

# from os.path import basename, join, realpath, exists
from os import makedirs

import io


# from .core import CurrentImage, CONFKEY, ConfigEntry, ProgressBar
from .helper import to_int_or_none

WEBSETS = {'@2x': 2, '@3x': 3}
SUPPORTED_FILES = ['*.jpg', '*.jpeg', '*.png', '*.tif']

RESAMPLE_MODES = {'none': Image.NEAREST,
                  'bilinear': Image.BILINEAR,
                  'bicubic': Image.BICUBIC,
                  'hamming': Image.HAMMING,
                  'box': Image.BOX,
                  'antialias': Image.ANTIALIAS}


class CONFKEY:
    PREFIX, SUFFIX = 'prefix', 'suffix'
    WIDTH, HEIGHT = 'width', 'height'
    RESAMPLE = 'resample'
    FORMAT = 'format'
    SUBFOLDER = 'subfolder'
    WEBSET = 'webset'
    WEBSETADDON = 'websetaddon'
    MODE, COLORPROFILE = 'mode', 'colorprofile'


class Entries(object):

    def __init__(self, dict):
        self.dict = dict

    def _value(self, key, default, warning=False):
        if key not in self.dict:
            msg = "{self.__class__} {key} not set. Using default value: {default}"
            if warning:
                logging.warning(msg)
            else:
                logging.debug(msg)
        return self.dict.get(key, default)

    def properties(self):
        return {name: getattr(self, name) for name, value in vars(self.__class__).items() if isinstance(value, property)}


class Options(Entries):

    def __init__(self, options_dict):
        super().__init__(options_dict)
        # self.options_dict = options_dict

    @property
    def source(self):
        return self._value('source', 'source')

    @property
    def dest(self):
        return self._value('dest', 'dest')

    @property
    def configfile(self):
        return self._value('configfile', 'imagebatch.json')

    @property
    def override(self):
        return self._value('override', False)

    @property
    def no_progress(self):
        return self._value('no_progress', False)

    @property
    def debug(self):
        return self._value('debug', False)

    # def _value(self, key, default, warning=False):
    #     if key not in self.options_dict:
    #         msg = "Option {key} not set. Using default value: {default}"
    #         if warning:
    #             logging.warning(msg)
    #         else:
    #             logging.debug(msg)
    #     return self.options_dict.get(key, default)

    # def _properties_dict(self):
    #     return {name: getattr(self, name) for name, value in vars(self.__class__).items() if isinstance(value, property)}

    def __str__(self):
        return str(self.__dict__)


class ConfigEntry(object):

    def __init__(self, config_entry_dict):
        # super().__init__(config_entry_dict)
        self.config_entry_dict = config_entry_dict

    @property
    def prefix(self):
        return self.config_entry_dict.get(CONFKEY.PREFIX, '')

    @property
    def suffix(self):
        return self.config_entry_dict.get(CONFKEY.SUFFIX, '')

    @property
    def websetaddon(self):
        return self.config_entry_dict.get(CONFKEY.WEBSETADDON, '')

    @property
    def ext(self):
        return self.config_entry_dict.get(CONFKEY.FORMAT, 'jpg')

    @property
    def with_subfolder(self):
        return self.config_entry_dict.get(CONFKEY.WEBSETADDON, '')

    @property
    def destination_size(self):
        return Size(self.config_entry_dict.get(CONFKEY.WIDTH, None),
                    self.config_entry_dict.get(CONFKEY.HEIGHT, None))

    @property
    def mode(self):
        return self.config_entry_dict.get(CONFKEY.MODE, 'RGB')

    @property
    def color_profile(self):
        return self.config_entry_dict.get(CONFKEY.COLORPROFILE, None)

    @property
    def resample(self):
        resample = self.config_entry_dict.get(CONFKEY.RESAMPLE, 'antialias')
        if resample in RESAMPLE_MODES:
            return RESAMPLE_MODES.get(resample)
        else:
            return Image.ANTIALIAS

    @property
    def resample_name(self):
        return [key for key, value in RESAMPLE_MODES.items() if value == self.resample][0]

    def _properties_dict(self):
        return {name: getattr(self, name) for name, value in vars(self.__class__).items() if isinstance(value, property)}


class CurrentImage(object):

    def __init__(self, options, source_filename, config_entry, output_method):
        self.options = options
        self.source_filename = source_filename
        self.config_entry = config_entry
        self.print = output_method

    @property
    def corename(self):
        return basename(self.source_filename).split('.')[0]

    @property
    def subfolder(self):
        return self.corename if self.config_entry.with_subfolder else ''

    @property
    def destination_basename(self):
        return f"{self.config_entry.prefix}{self.corename}{self.config_entry.suffix}{self.config_entry.websetaddon}.{self.config_entry.ext}"

    @property
    def destination_folder(self):
        return join(self.options.dest, self.subfolder)

    @property
    def destination_filename_short(self):
        return join(self.subfolder, self.destination_basename)

    @property
    def destination_filename(self):
        return join(self.destination_folder, self.destination_basename)

    def generate(self):
        if exists(self.destination_filename) and not self.options.override:
            self.print(f"ignore file: {self.destination_filename}")
            return
        else:
            self.print(f"creating: {self.destination_filename_short}")
            logging.info(f"creating: {self.destination_filename_short}")

        with Image.open(self.source_filename) as image:

            if self.config_entry.mode != image.mode:
                logging.debug(f"Source and destination mode differ. Source: {image.mode}, Destination: {self.config_entry.mode}")
                self.convert(image)

            profile = self.get_image_profile(image)
            if profile is not None:
                pass
                # TODO needs implementation: should checked and converted together with mode. lines above.

            destination_size = Size(image.size).destination_size(self.config_entry.destination_size).size
            resample = self.config_entry.resample
            logging.debug(f"Resizing Image. Source: {Size(image.size)}, Destination: {destination_size}, Resample: {self.config_entry.resample_name}")
            image = image.resize(destination_size, resample=resample)

            if not exists(self.destination_folder):
                makedirs(self.destination_folder)

            logging.debug(f"Writing {self.destination_filename}")
            image.save(self.destination_filename)

    def convert(self, image):
        source_profile = self.get_image_profile(image)
        if source_profile is not None:
            destination_profile = self.profile()
            logging.debug(f"Transforming color profiles. Source: {self.profile_name(source_profile)}, Destination: {self.profile_name(destination_profile)} ")
            transform = ImageCms.buildTransform(inputProfile=source_profile,
                                                outputProfile=destination_profile,
                                                inMode=image.mode,
                                                outMode=self.config_entry.mode,
                                                renderingIntent=ImageCms.INTENT_RELATIVE_COLORIMETRIC)
            ImageCms.applyTransform(image, transform)
        else:
            logging.debug(f"Converting color modes. Source: {image.mode}, Destination: {self.config_entry.mode}")
            image = image.convert(mode=self.config_entry.mode)
        return image

    def get_image_profile(self, image):
        try:
            return ImageCms.ImageCmsProfile(io.BytesIO(image.info.get('icc_profile')))
        except Exception as exeption:
            return None

    def profile_name(self, profile):
        return ImageCms.getProfileName(profile).strip()

    def profile(self):
        if self.config_entry.color_profile is None:
            return ImageCms.createProfile("sRGB")


class PyImgBatch:

    def __init__(self, args):
        self.options = Options(args)
        pprint("properties: ")
        pprint(self.options.properties())

        self.config = []

        raw_config = self._read_config()
        self._process_config(raw_config)

    def __del__(self):
        self._image_progress_bar.close()
        self._main_progress_bar.close()

    def _read_config(self):
        with open(self.options.configfile) as config_file:
            raw_config = json.load(config_file)
        return raw_config
        # TODO: read from stdin

    def _process_config(self, raw_config):
        for entry in raw_config:
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
        if webset_value in WEBSETS:
            for index in range(1, WEBSETS[webset_value] + 1):
                new_entry = entry.copy()
                new_entry.update({CONFKEY.WIDTH: to_int_or_none(entry.get(CONFKEY.WIDTH, None), multiplier=index)})
                new_entry.update({CONFKEY.HEIGHT: to_int_or_none(entry.get(CONFKEY.HEIGHT, None), multiplier=index)})
                new_entry.update({CONFKEY.WEBSETADDON: f"@{index}x"})
                self.config.append(new_entry)
        else:
            print("ERROR")

    def _create_files_array(self, supported_files=SUPPORTED_FILES):
        self.source_files_names = [os.path.abspath(file) for ext in supported_files for file in glob(
            os.path.join(self.options.source, ext))]
        print(self.source_files_names)

    def _process_files(self):
        # TODO: Format the progress bars more meanfully
        self._image_progress_bar = ProgressBar(len(self.config), disable=self.options.no_progress)
        self._main_progress_bar = ProgressBar(len(self.source_files_names), disable=self.options.no_progress)
        for source_file_name in self.source_files_names:
            self._process_file(source_file_name)
            self._main_progress_bar.update()

    def _process_file(self, source_filename):
        self._image_progress_bar.reset()
        self._print(f"progressing: {basename(source_filename)}")
        logging.info(f"progressing: {basename(source_filename)}")
        for entry in self.config:
            current_image = CurrentImage(self.options, source_filename, ConfigEntry(entry), self._print)
            current_image.generate()
            self._image_progress_bar.update()

    def _print(self, *args):
        if not self.options.no_progress:
            self._image_progress_bar.write(*args)
        else:
            print(*args)

    def exec(self):
        self._create_files_array()
        self._process_files()


class Size(object):
    def __init__(self, *args):
        if len(args) == 1 and type(args[0]) is tuple:
            # TODO: to_int_or_none for tuple too
            self._size = args[0]
        elif len(args) == 2:
            self._size = (to_int_or_none(args[0]), to_int_or_none(args[1]))
        else:
            raise Exception(
                "Invalid number of arguments or invalid type of the arguments")

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    @property
    def size(self):
        return self._size

    def destination_size(self, designated_size):
        if designated_size.width is not None and designated_size.height is not None:
            return designated_size
        elif designated_size.width is None and designated_size.height is not None:
            return Size(int(self.width / (self.height / designated_size.height)), designated_size.height)
        elif designated_size.width is not None and designated_size.height is None:
            return Size(designated_size.width, int(self.height / (self.width / designated_size.width)))
        else:
            raise Exception("Destination size not computable")

    def __call__(self):
        return self._size

    def __str__(self):
        return f"size({self.width},{self.height})"


class ProgressBar(tqdm):

    def __init__(self, total, disable=True):
        super().__init__(total=total, disable=disable)
        self.disable = disable
        self._time = time  # fixes a tqdm bug that _time not exist on reset() when disabled
