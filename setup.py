import setuptools
setuptools.setup(
    name="pyimgbatch",
    packages=['pyimgbatch'],
    version_config={
        "version_format": "{tag}.dev{sha}",
        "starting_version": "0.1.0"
    },
    setup_requires=['better-setuptools-git-version'],
    entry_points={
        'console_scripts': [
            'pyimgbatch = pyimgbatch.__main__:main'
        ]
    })
