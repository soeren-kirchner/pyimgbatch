from tqdm import tqdm
from time import time

from PIL import Image
from PIL import ImageCms

from os.path import basename, join, realpath, exists
from os import makedirs

import io, sys
import logging

from .constants import CONFKEY, ARGS
from .helper import *

class Size(object):
    def __init__(self, *args):
        if len(args) == 1 and type(args[0]) is tuple:
            # TODO: to_int_or_none for tuple also
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

        self.print(f"creating: {self.destination_filename_short}")
        logging.info(f"creating: {self.destination_filename_short}")

        with Image.open(self.source_filename) as image:

            if self.config_entry.mode != image.mode:
                self.convert(image)

            profile = self.get_image_profile(image)
            if profile is not None: 
                pass
                ##self.print(f"Color Profile: {ImageCms.getProfileName(profile).strip()}")

            ##self.print(image.mode)

            destination_size = Size(image.size).destination_size(self.config_entry.destination_size).size
            # self.print(f"source size: {image.size}")
            # self.print(f"dest size: {destination_size}")
            image = image.resize(destination_size, resample=Image.HAMMING) 

            if not exists(self.destination_folder):
                makedirs(self.destination_folder)
            
            image.save(self.destination_filename)



    def convert(self, image):
        ##self.print("mode differs")
        source_profile = self.get_image_profile(image)
        if source_profile is not None:
            ##self.print("apply transform")
            ##self.print(ImageCms.getProfileName(source_profile))
            transform = ImageCms.buildTransform(inputProfile=source_profile, 
                                                outputProfile=self.profile(), 
                                                inMode=image.mode, 
                                                outMode=self.config_entry.mode, 
                                                renderingIntent=ImageCms.INTENT_RELATIVE_COLORIMETRIC)
            ImageCms.applyTransform(image, transform)
        else:
            ##self.print("amply simple convert")
            image = image.convert(mode=self.config_entry.mode)
        return image


    def get_image_profile(self, image):
        try:
            return ImageCms.ImageCmsProfile(io.BytesIO(image.info.get('icc_profile')))
        except:
            return None

    def transform(self, image, source_profile):  
        dest_profile = self.profile()
        transform = ImageCms.buildTransform(source_profile, dest_profile, image.mode, "RGB", ImageCms.INTENT_RELATIVE_COLORIMETRIC)
        ImageCms.applyTransform(image, transform)
        return image

    def profile(self):
        if self.config_entry.color_profile is None:
            return ImageCms.createProfile("sRGB")
        



class ProgressBar(tqdm):

    def __init__(self, total, disable=True):
        # if not disable:
        super().__init__(total=total, disable=disable)
        self.disable = disable
        self._time = time  # fixes a tqdm bug that _time not exist on reset() when disabled

