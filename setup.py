import setuptools
setuptools.setup(
    name="pyimgbatch",
    packages=['pyimgbatch'],
    entry_points={
        'console_scripts': [
            'pyimgbatch = pyimgbatch.__main__:main'
        ]
    })
