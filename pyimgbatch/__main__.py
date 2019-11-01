import argparse
import logging
# from pprint import pprint
from .pyimgbatch import PyImgBatch


def main():
    """simply main
    """
    logging.basicConfig(level=logging.DEBUG,
                        filename='pyimgbatch.log',
                        filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s')
    args = get_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.debug(args)
    pib = PyImgBatch(vars(args))
    pib.exec()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--configfile', type=str,
                        default='imagebatch.json', help='configuration file')
    parser.add_argument('-s', '--source', type=str,
                        default='source', help='source folder containing images for batch processing')
    parser.add_argument('-d', '--dest', type=str, default='dest',
                        help='destination folder for the processed images')
    parser.add_argument('-o', '--override', action='store_true',
                        default=False, help='overrides existing files')
    parser.add_argument('--no-progress', action='store_true',
                        default=False, help='disables the progress bars')
    parser.add_argument('--debug', action='store_true',
                        default=False, help='disables the progress bars')
    return parser.parse_args()


if __name__ == "__main__":
    main()
