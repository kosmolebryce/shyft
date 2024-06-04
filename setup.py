import setuptools
from setuptools import setup

APP = ['Shyft.py']
DATA_FILES = []
OPTIONS = {
    'iconfile': 'resources/icon.icns',
    'packages': ['tkinter'],
    'includes': ['tkinter']
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
