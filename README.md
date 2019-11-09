# PyImgBatch

PyImgBatch is a batch image processor for python including a command line interface.

## Installation
For installation open a terminal and type the following line into the command line.

```
pip install pyimgbatch
```

## Usage on command line

The simplest usage is to change to the folder containing the images with

```
cd /folder/wit/images
```
and type 

```
pyimgbatch --width 300
```
This will resize all supported image files in the current folder to a width of 300 pixels respecting the aspect ratio of the source file. The results will be written to a "dest" subfolder.

Alternatively, you can set a source folder with the images to be converted and/or a destination folder for the results as follow.

```
pyimgbatch --source source_folder --dest destination_folder --height 400
```
or shorter
```
pyimgbatch -s source_folder -d destination_folder --height 400
```
This will convert the images from the *source_folder* to a height of 400px and stores the results in the destination folder.  
*Note: For every source image a subfolder will be created inside the destination_folder. To avoid this behavior use the --nosubfolder argument.*

## Project Files
One of PyImgBatch features is to create multiple different versions from given image files. 

For this, you can use project files. Project files are JSON files containing the specifications for the image processing. 

### The very short one

Here an example of a very short one.

```json
[
    { "width": 1000, "suffix": ".w1000" },
    { "height": 1200, "suffix": ".h1200" }
]
```
For example (may the project named "myprj.json"):
```
pyimgbatch -c myprj.json
```
produces the following output:
```
processing: french-bulldog-4530685.jpg
creating: french-bulldog-4530685.w1000.jpg
creating: french-bulldog-4530685.h1200.jpg
processing: coast-4478424.jpg
creating: coast-4478424.w1000.jpg
creating: coast-4478424.h1200.jpg
...
processing: beaded-2137080_1920-cmyk-iso-eci.tif
creating: beaded-2137080_1920-cmyk-iso-eci.w1000.jpg
creating: beaded-2137080_1920-cmyk-iso-eci.h1200.jpg
...
```
and creates two images per source images, resized to the specified width or height with suffix added to the original name. 

### The short one

Imagine, you need to create different sizes for all your images for your web project. For instance, you need the images in widths 180px, 300px, 400px and one in a height of 800 and each 2x and 3x the size for higher pixel density display like in smartphones.
An example could look as follow.

```JSON
{
    "name": "web set",
    "comment": "some sample pictures",
    "source": "webset/source",
    "dest": "webset/dest",
    "prefix": "web.",
    "configs": [
        { "width": 180, "suffix": ".w180", "webset": "@3x" },
        { "width": 300, "suffix": ".w300", "webset": "@3x" },
        { "width": 400, "suffix": ".w400", "webset": "@3x" },
        { "height": 800, "prefix": "preview.", "webset": "@3x" }
    ]
}
```
This will create 12 destination images for each imput image. For a image "lama-4540160.jpg" you get:

```
...
creating: lama-4540160/web.lama-4540160.w180@1x.jpg
creating: lama-4540160/web.lama-4540160.w180@2x.jpg
creating: lama-4540160/web.lama-4540160.w180@3x.jpg
creating: lama-4540160/web.lama-4540160.w300@1x.jpg
creating: lama-4540160/web.lama-4540160.w300@2x.jpg
creating: lama-4540160/web.lama-4540160.w300@3x.jpg
creating: lama-4540160/web.lama-4540160.w400@1x.jpg
creating: lama-4540160/web.lama-4540160.w400@2x.jpg
creating: lama-4540160/web.lama-4540160.w400@3x.jpg
creating: lama-4540160/preview.lama-4540160@1x.jpg
creating: lama-4540160/preview.lama-4540160@2x.jpg
creating: lama-4540160/preview.lama-4540160@3x.jpg
...
```

As you see you can specify defaults, so you don't need to repeat yourself.
The more specific option is used instead of the more general one. So in this example, all images get the prefix "web." except the last, because the more specific prefix is here given as "preview."

*Hint: The file names are a little strange because I've downloaded the from the free image stock [pixabay](https://pixabay.com) and I haven't changed the Name so you can search for the pics or the photographer if you want.*

### Full image project file

looks as follow.

```JSON
{
    "comment": "pyImgBatch demo project",
    "debug": true,
    "no-progess": false,
    "projects": [
        {
            "name": "web set",
            "comment": "some sample pictures",
            "source": "webset/source",
            "dest": "webset/dest",
            "prefix": "web.",
            "configs": [
                { "width": 180, "suffix": ".w180", "webset": "@3x" },
                { "width": 300, "suffix": ".w300", "webset": "@3x" },
                { "width": 400, "suffix": ".w400", "webset": "@3x" },
                { "height": 800, "prefix": "preview.", "webset": "@3x" }
            ]
        },
        {
            "name": "images to thumbnails",
            "source": "to-thumbnails/originals",
            "dest": "to-thumbnails/thumbnails",
            "subfolder": false,
            "prefix": "thumb.",
            "configs": [
                {"height": 300}, 
                {"prefix": "smallthumb.", "height": 200}
            ]
        }
    ]
}
```

This project contains two projects. 