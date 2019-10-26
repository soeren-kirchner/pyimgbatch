from tqdm import tqdm
from time import time

from PIL import Image
from PIL import ImageCms

from os.path import basename, join, realpath, exists
from os import makedirs

import io, sys
import logging

from .constants import ARGS
from .helper import *

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
            return Size(int(self.width/(self.height/designated_size.height)), designated_size.height)
        elif designated_size.width is not None and designated_size.height is None:
            return Size(designated_size.width, int(self.height/(self.width/designated_size.width)))
        else:
            raise Exception("Destination size not computable")

    def __call__(self):
        return self._size

    def __str__(self):
        return f"size({self.width},{self.height})"


class ConfigEntry(object):

    def __init__(self, config_entry_dict):
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
        resample = self.config_entry_dict.get(CONFKEY.RESAMPLE, 'antialias')
        if resample in RESAMPLE_MODES:
            return resample
        else:
            return 'antialias'


class CurrentImage(object):

    def __init__(self, args, source_filename, config_entry, output_method):
        self.args = args
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
        return join(self.args[ARGS.DEST], self.subfolder)

    @property
    def destination_filename_short(self):
        return join(self.subfolder, self.destination_basename)

    @property
    def destination_filename(self):
        return join(self.destination_folder, self.destination_basename)

    def generate(self):
        if exists(self.destination_filename) and not self.args[ARGS.OVERRIDE]: 
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


class ProgressBar(tqdm):

    def __init__(self, total, disable=True):
        super().__init__(total=total, disable=disable)
        self.disable = disable
        self._time = time  # fixes a tqdm bug that _time not exist on reset() when disabled

