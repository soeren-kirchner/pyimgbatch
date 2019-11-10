import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

# with open('requirements.txt') as req_file:
#     requirements = req_file.read().splitlines()

setuptools.setup(
    name="pyimgbatch",
    author="Sören Kirchner",
    author_email="sk@tologo.de",
    description="PyImgBatch is a batch image processor for python including a command line interface.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/soeren-kirchner/pyimgbatch",
    # packages=['pyimgbatch'],
    install_requires=[
        "Pillow>=6.2.1",
        "tqdm>=4.36.1"
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Other Audience",
        "Programming Language :: Python :: Implementation",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    python_requires='>=3.6',
    version="0.2.7",
    # version_config={
    #     "version_format": "{tag}.dev{sha}",
    #     "starting_version": "0.1.0"
    # },
    # setup_requires=['better-setuptools-git-version'],
    entry_points={
        'console_scripts': [
            'pyimgbatch = pyimgbatch.__main__:main'
        ]
    })
