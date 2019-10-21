from tqdm import tqdm
from time import time

class Size(object):
    def __init__(self, *args):
        if len(args) == 1 and type(args[0]) is tuple:
            self._size = args[0]
        elif len(args) == 2:
            self._size = (args[0], args[1])
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

    def __call__(self):
        return self._size

    def __str__(self):
        return "size({},{})".format(self.width, self.height)


class ProgressBar(tqdm):

    def __init__(self, total, disable=True):
        #if not disable:
        super().__init__(total=total, disable=disable)
        self.disable = disable
        self._time = time #fixes a tqdm bug that _time not exist on reset() when disabled

