import sys, os
import argparse
import logging
# from pprint import pprint
from .pyimgbatch import PyImgBatch


def main():
    """simply main
    """
    args = get_args()
    logging_level = logging.DEBUG if not args.nolog else logging.ERROR
    logging.basicConfig(level=logging_level,
                        filename=args.logfile,
                        filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s')
    if args.debug:
        logging.getLogger().setLevel(logging_level)
    logging.debug(args)
    if args.silent:
        sys.stdout = open(os.devnull, 'w')
    pib = PyImgBatch(prepare_arguments(args))
    pib.exec()


def prepare_arguments(args):
    args_prep = vars(args)
    args_prep['subfolder'] = not args_prep['nosubfolder']
    return args_prep


def get_args():
    parser = argparse.ArgumentParser()

    file_handling_group = parser.add_argument_group('file handling')
    file_handling_group.add_argument('-c', '--configfile', type=str,
                                     default='imagebatch.json', help='configuration file')  # TODO: remove
    file_handling_group.add_argument('-p', '--project', type=str,
                                     default='pyimagebatch.json', help='configuration file')
    file_handling_group.add_argument('-s', '--source', type=str,
                                     default='.', help='source folder containing images for batch processing')
    file_handling_group.add_argument('-d', '--dest', type=str, default='dest',
                                     help='destination folder for the processed images')
    file_handling_group.add_argument('-o', '--override', action='store_true',
                                     default=False, help='overrides existing files')
    file_handling_group.add_argument('--nosubfolder', action='store_true',
                                     default=False, help='overrides existing files')

    output_group = parser.add_argument_group('output / user interaction')
    output_group.add_argument('--no-progress', action='store_true',
                              default=False, help='disables the progress bars')
    output_group.add_argument('--debug', action='store_true',
                              default=False, help='enables debugging level.')
    output_group.add_argument('--logfile', type=str,
                              default='pyimgbatch.log', help='log destination file.')
    output_group.add_argument('--nolog', action='store_true',
                              default=False, help='enables log saved in file.')
    output_group.add_argument('--silent', action='store_true',
                              default=True, help='silent execution with no output so stdout.')

    image_manipulation_group = parser.add_argument_group('image manipulation')
    image_manipulation_group.add_argument('--width', type=int,
                                          default=None, help='width of the destination image.')
    image_manipulation_group.add_argument('--height', type=int,
                                          default=None, help='height of the destination image.')
    image_manipulation_group.add_argument('--resample', type=str, choices=["none", "bilinear", "bicubic", "hamming", "box", "antialias"],
                                          default="antialias", help='resample arlgorithm used for resizing, defaults to "antialias"')

    return parser.parse_args()


if __name__ == "__main__":
    main()
