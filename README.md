# PyImgBatch

PyImgBatch is a batch image processor for python including a command line interface.


## Usage

    pyimgbatch -s source_folder -d destination_folder -c configfile

- *source_folder* -
    Folder containing the images to be processed (resized, color mode changed ...)

- *destination_folder* -
    Target for the converted Images.

- *config_file* -
    A simple json file containing the settings for the processed files


```json
[
    { "width": 1000, "suffix": ".w1000" },
    { "height": 1200, "suffix": ".h1200" }
]
```
For example:
```
pyimgbatch -s source -d dest -c config_samples/imagebatch_simple2.json
```
produces the following output:
```
progressing: french-bulldog-4530685.jpg
creating: french-bulldog-4530685.w1000.jpg
creating: french-bulldog-4530685.h1200.jpg
progressing: coast-4478424.jpg
creating: coast-4478424.w1000.jpg
creating: coast-4478424.h1200.jpg
...
pprogressing: beaded-2137080_1920-cmyk-iso-eci.tif
creating: beaded-2137080_1920-cmyk-iso-eci.w1000.jpg
creating: beaded-2137080_1920-cmyk-iso-eci.h1200.jpg
...
```
and creates two images per source images, resized to the specified width or height with suffix added to the original name. 