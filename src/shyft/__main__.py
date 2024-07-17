import os
import sys
from PyQt6.QtCore import QLibraryInfo, PYQT_VERSION_STR, QT_VERSION_STR
from PyQt6.QtWidgets import QApplication
from shyft.gui.main_window import MainWindow

def main():
    # Print Python version and path
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")

    # Print PyQt and Qt versions
    print(f"PyQt version: {PYQT_VERSION_STR}")
    print(f"Qt version: {QT_VERSION_STR}")

    # Set and print the Qt plugins path
    plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path
    print(f"Qt Plugins Path: {plugins_path}")

    # Print all Qt-related environment variables
    for key, value in os.environ.items():
        if 'QT' in key or 'PYQT' in key:
            print(f"{key}: {value}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
