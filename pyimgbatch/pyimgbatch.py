import json
import logging
import io

from os import makedirs
from os.path import basename, join, exists, abspath
from glob import glob
from tqdm import tqdm

from pprint import pformat

from time import time

from PIL import Image
from PIL import ImageCms

# from .helper import to_int_or_none


WEBSETS = {'@2x': 2, '@3x': 3}
SUPPORTED_FILES = ['*.jpg', '*.jpeg', '*.png', '*.tif']

RESAMPLE_MODES = {'none': Image.NEAREST,
                  'bilinear': Image.BILINEAR,
                  'bicubic': Image.BICUBIC,
                  'hamming': Image.HAMMING,
                  'box': Image.BOX,
                  'antialias': Image.ANTIALIAS}


class CONSTANTS(type):
    pass

    # def available_options(cls):
    #     return [option for option_constant, option in cls.__dict__.items() if type(option).__name__ == 'str' and option_constant.isupper()]

    # def __contains__(cls, option):
    #     return option in cls.available_options()


class CONFKEY(metaclass=CONSTANTS):
    PREFIX, SUFFIX = 'prefix', 'suffix'
    WIDTH, HEIGHT = 'width', 'height'
    RESAMPLE = 'resample'
    FORMAT = 'format'
    SUBFOLDER = 'subfolder'
    WEBSET = 'webset'
    WEBSETADDON = 'websetaddon'
    MODE, COLORPROFILE = 'mode', 'colorprofile'


class OPTIONKEY(metaclass=CONSTANTS):
    SOURCE, DEST = 'source', 'dest'
    CONFIGFILE = 'configfile'
    OVERRIDE = 'override'
    NOPROGRESS = 'no_progress'
    DEBUG = 'debug'
    PROJECTS, CONFIGS = 'projects', 'configs'
    NAME = 'name'


class Entries(object):

    def __init__(self, dict, defaults=None):
        self.dict = dict
        self.defaults = defaults
        self.shown_messages = []

    def _value(self, key, default, warning=False):
        if key not in self.dict:
            msg = f"{self.__class__.__name__}: entry '{key}' not set. Using default value: {default}"
            if msg not in self.shown_messages:
                self.shown_messages.append(msg)
                if warning:
                    logging.warning(msg)
                else:
                    logging.debug(msg)
        if self.defaults is None:
            return self.dict.get(key, default)
        else:
            return self.dict.get(key, self.defaults._value(key, default))

    # def properties(self):
    #     return {name: getattr(self, name) for name, value in vars(self.__class__).items() if isinstance(value, property)}

    def __str__(self):
        return str(self.dict)

    @property
    def source(self):
        return self._value(OPTIONKEY.SOURCE, OPTIONKEY.SOURCE)

    @property
    def dest(self):
        return self._value(OPTIONKEY.DEST, OPTIONKEY.DEST)

    @property  # TODO: replace
    def configfile(self):
        return self._value(OPTIONKEY.CONFIGFILE, 'imagebatch.json')

    @property
    def project_file_name(self):
        return self._value('project', 'pyimgbatch.json')  # TODO: Constants

    @property
    def override(self):
        return self._value(OPTIONKEY.OVERRIDE, False)

    @property
    def no_progress(self):
        return self._value(OPTIONKEY.NOPROGRESS, False)

    @property
    def debug(self):
        return self._value(OPTIONKEY.DEBUG, False)

    @property
    def project_name(self):
        return self._value(OPTIONKEY.NAME, '')

    @property
    def prefix(self):
        return self._value(CONFKEY.PREFIX, '')

    @property
    def suffix(self):
        return self._value(CONFKEY.SUFFIX, '')

    @property
    def websetaddon(self):
        return self._value(CONFKEY.WEBSETADDON, '')

    @property
    def ext(self):
        return self._value(CONFKEY.FORMAT, 'jpg')

    @property
    def with_subfolder(self):
        return self._value(CONFKEY.SUBFOLDER, False)

    @property
    def destination_size(self):
        return Size(self._value(CONFKEY.WIDTH, None),
                    self._value(CONFKEY.HEIGHT, None))

    @property
    def mode(self):
        return self._value(CONFKEY.MODE, 'RGB')

    @property
    def color_profile(self):
        return self._value(CONFKEY.COLORPROFILE, None)

    @property
    def resample(self):
        resample = self._value(CONFKEY.RESAMPLE, 'antialias')
        if resample in RESAMPLE_MODES:
            return RESAMPLE_MODES.get(resample)
        else:
            return Image.ANTIALIAS

    @property
    def resample_name(self):
        return [key for key, value in RESAMPLE_MODES.items() if value == self.resample][0]


class Args(Entries):
    pass


class Options(Entries):

    def __init__(self, dict, defaults):
        if dict is not None:
            super().__init__(dict, defaults)
        else:
            if exists(defaults.project_file_name):
                self._init_from_file(dict, defaults)
            else:
                dict = {"projects": [{"configs": [{}]}]}
                super().__init__(dict, defaults=defaults)

    def _init_from_file(self, dict, defaults):
        with open(defaults.project_file_name) as project_file:
            dict = json.load(project_file)  # TODO: Error Handling
            if (type(dict).__name__ == "dict"):
                if "projects" in dict:
                    self.dict = dict
                elif "configs" in dict:
                    self.dict = {"projects": [dict]}
                else:
                    print("error")  # TODO: Error Handling
            elif (type(dict).__name__ == "list"):
                self.dict = {"projects": [{"configs": dict}]}
            else:
                print("error")  # TODO: Error Handling

            super().__init__(self.dict, defaults=defaults)

    def get_projects(self):
        return self._value(OPTIONKEY.PROJECTS, None)

    def exec(self):
        # TODO: Error if there is no project
        Out.init_image_bar(self.no_progress)
        Out.init_project_bar(self.no_progress)
        for project in self.get_projects():
            Project(project, defaults=self).exec()


class Project(Entries):

    def exec(self):
        configs = self._process_configs(self._get_configs())
        filenames = self._file_names()
        Out.project_bar.reset(total=len(filenames))

        Out.out(f"Processing project '{self.project_name}':")

        for filename in filenames:
            # TODO: Error if there is no config entry
            Out.image_bar.reset(total=len(configs))
            for config in configs:
                CurrentImage(filename, ConfigEntry(config, defaults=self)).generate()
                Out.image_bar.update()
            Out.project_bar.update()

    def _get_configs(self):
        return self._value(OPTIONKEY.CONFIGS, None)

    def _process_configs(self, raw_config):
        configs = []
        for entry in raw_config:
            # resolve websets
            if CONFKEY.WEBSET in entry:
                configs.extend(self._create_webset_entries(entry))
            else:
                configs.append(entry)
        logging.debug("raw config:")
        logging.debug(pformat(raw_config))
        logging.debug("solved config:")
        logging.debug(pformat(configs))
        return configs

    def _create_webset_entries(self, entry):
        configs = []
        webset_value = entry[CONFKEY.WEBSET]
        if webset_value in WEBSETS:
            for index in range(1, WEBSETS[webset_value] + 1):
                new_entry = entry.copy()
                new_entry.update({CONFKEY.WIDTH: to_int_or_none(entry.get(CONFKEY.WIDTH, None), multiplier=index)})
                new_entry.update({CONFKEY.HEIGHT: to_int_or_none(entry.get(CONFKEY.HEIGHT, None), multiplier=index)})
                new_entry.update({CONFKEY.WEBSETADDON: f"@{index}x"})
                configs.append(new_entry)
        else:
            print("ERROR")
        return configs

    def _file_names(self, supported_files=SUPPORTED_FILES):
        return [abspath(file) for ext in supported_files for file in glob(join(self.source, ext))]


class ConfigEntry(Entries):
    pass


class CurrentImage(object):

    def __init__(self, source_filename, config_entry):
        self.source_filename = source_filename
        self.config_entry = config_entry

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
        return join(self.config_entry.dest, self.subfolder)

    @property
    def destination_filename_short(self):
        return join(self.subfolder, self.destination_basename)

    @property
    def destination_filename(self):
        return join(self.destination_folder, self.destination_basename)

    def generate(self):
        self.print = Out.out  # TODO: refactor
        if exists(self.destination_filename) and not self.config_entry.override:
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
        except:
            return None

    def profile_name(self, profile):
        return ImageCms.getProfileName(profile).strip()

    def profile(self):
        if self.config_entry.color_profile is None:
            return ImageCms.createProfile("sRGB")


class PyImgBatch:

    def __init__(self, args_dict, options_dict=None):
        self.args = Args(args_dict)
        self.options = Options(options_dict, defaults=self.args)

    def exec(self):
        self.options.exec()


class Size(object):
    """[summary]

    :param object: [description]
    :type object: [type]
    :raises Exception: [description]
    :return: [description]
    :rtype: [type]
    """
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
        # print(designated_size)
        if designated_size.width is not None and designated_size.height is not None:
            return designated_size
        elif designated_size.width is None and designated_size.height is not None:
            return Size(int(self.width / (self.height / designated_size.height)), designated_size.height)
        elif designated_size.width is not None and designated_size.height is None:
            return Size(designated_size.width, int(self.height / (self.width / designated_size.width)))
        else:
            logging.info("No 'width' or 'height' were given. Using 'width' and 'height' of the source file")
            return Size(self.size)

    def __call__(self):
        return self._size

    def __str__(self):
        return f"size({self.width},{self.height})"


class ProgressBar(tqdm):

    def __init__(self, total, disable=True):
        super().__init__(total=total, disable=disable)
        self.disable = disable
        self._time = time  # fixes a tqdm bug that _time not exist on reset() when disabled


class Out:
    """Class description
    """

    outfunction = print
    project_bar = None
    image_bar = None

    @classmethod
    def out(cls, *args):
        cls.outfunction(*args)

    # @classmethod
    # def __call__(cls, *args):
    #     cls.out(*args)

    @classmethod
    def init_project_bar(cls, disable=True):
        cls.project_bar = ProgressBar(1, disable=disable)
        if disable:
            cls.outfunction = print
        else:
            cls.outfunction = cls.project_bar.write

    @classmethod
    def init_image_bar(cls, disable=True):
        cls.image_bar = ProgressBar(1, disable=disable)

    @classmethod
    def __del__(cls):
        cls.image_bar.close()
        cls.project_bar.close()


def to_int_or_none(value, multiplier=1):
    """[summary]

    :param value: [description]
    :type value: [type]
    :param multiplier: [description], defaults to 1
    :type multiplier: int, optional
    :return: [description]
    :rtype: [type]
    """
    try:
        value = int(value) * multiplier
        return value
    except:
        return None
