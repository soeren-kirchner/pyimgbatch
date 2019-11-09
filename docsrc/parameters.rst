Parameters
==========

List of **pyimgbatch** project file parameters. The content of the square brackets shows the command line equivalent. 

:width [-\\-width]: **Width** of the destination image. If the **width** is not given, it calculateted on the height. 
    If neither the width nor the height are given, the width and the height of the source image will be used. 

:height [-\\-height]: **Height** of the destination image. If the **height** is not given, it calculateted on the height.
    If neither the width nor the height are given, the width and the height of the source image will be used.

:resample [-\\-resample]: defines the resample mode on resizing the image. Possible values are 
    "none", "bilinear", "bicubic", "hamming", "box" or "antialias". 
    If there is no resample mode is given or the given resample mode is unknown, it defaults to "antialias"
