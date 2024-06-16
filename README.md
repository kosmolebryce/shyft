# `README.md`

## Shyft
`v0.1`

*June, 2024*

----

### Introduction

`Shyft` is a shift-logging GUI utility designed to help data annotators more 
effectively track and manage their service and billing records. It uses the 
`tkinter` GUI framework, which, as of this writing, is part of Python's 
standard library.

### Quickstart Installation Guide
You can install `Shyft` via a number of methods, but the easiest, by far, are 
the pre-packaged `Shyft.dmg` (for macOS users) or `ShyftSetup.exe` 
(for Windows users).

#### macOS
If you're using macOS, you can install `Shyft` by downloading `Shyft.dmg`, 
opening it, and then dragging and dropping the `Shyft.app` file into the 
`Applications` folder.

#### Windows
If you're using Windows, you can install `Shyft` by downloading and running 
the `ShyftSetup.exe` file. The installation wizard will guide you through the 
setup process. Once it's complete, you can run the program from the Start 
menu.

#### Linux
Currently, there are no package installers available for Linux. Please see the instructions for building from source if you plan to use Shyft on a Linux system.

----

### Building `Shyft` from Source
If you'd like to build the program from source, follow these steps:

1.  Open your system's terminal.
> - **macOS**: Simultaneously press the command key and space bar to open the `Spotlight` search field. Type "terminal", and then select `Terminal.app`.
> - **Windows**: Simultaneously press the Windows and 'R' keys to open the `Run` dialog. Type "cmd", and then press enter to open `Command Prompt`.

2. Navigate to the directory to which you would like to clone the `Shyft` repository. For simplicity, we'll assume you're cloning it to your home directory, which is usually where most systems set users' locations upon initialization of the login shell.

3. Clone the GitHub repository to your local machine. From `Terminal` (on macOS) or `cmd` (on Windows), run the following command.

> ```bash
> git clone https://github.com/kosmolebryce/shyft.git
>```

3. After the repository has been cloned to your machine, navigate into the program's source code directory.

> ```bash
> cd shyft/src/shyft
> ```

4.  At this point, you have a few options:
> - If you'd like to run the program without installing it, you can invoke it directly with your Python interpreter by entering the following command.

> ```bash
> python shyft.py
> ```

> > This will initialize the GUI, streaming debugging/logging statements as output to the terminal while the program is in use.

> - If you'd like to build and install the program, there are lots of tools you can use. The most popular option for macOS is probably `py2app`, while the most popular options for Windows are probably `pyinstaller` and `cxfreeze`.


----

**NOTE**: This repository is under active development. Because `Shyft` is a 
decidedly new project, documentation is rather sparse at the moment. We're 
working hard to compile a robust corpus of helpful, high-quality resources for 
our users' reference, so we encourage you to check back with the project's 
[GitHub page](https://github.com/kosmolebryce/shyft) every now and then.

Thanks for your support!
