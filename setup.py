from setuptools import setup
import os

# Update to the correct relative path within subpackage
APP = ["src/shyft/__main__.py"]
DATA_FILES = []

# Define options for py2app
OPTIONS = {
    "iconfile": "src/shyft/resources/icon.icns",  # Ensure the path is correct
    "includes": ["tkinter", "multiprocessing"],
    "plist": {
        "CFBundleName": "Shyft",
        "CFBundleIdentifier": "com.enclaim.shyft",
        "CFBundleVersion": "0.0.1",
        "CFBundleShortVersionString": "0.1",
        "LSUIElement": True,
        "NSAppTransportSecurity": {"NSAllowsArbitraryLoads": True},
        "CFBundleEntitlementsFile": "src/shyft/resources/entitlements.plist",  # Ensure this path is correct
        "NSSupportsAutomaticGraphicsSwitching": True,
        "NSAppSleepDisabled": True,
        "NSHighResolutionCapable": True,
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
