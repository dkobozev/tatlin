# TATLIN

Overview
--------

Tatlin is an open-source 3D G-code and STL viewer for 3D printers. In addition
to viewing, Tatlin also supports rotation and scaling of STL files. The app
takes advantage of hardware acceleration for efficient rendering even for
complex models. The aim of the project is to provide a fast, portable and
intuitive way to view and examine models with a minimal learning curve.

Installation
------------

Prebuilt packages for Linux, Windows and MacOS are available on the [Releases
page](https://github.com/dkobozev/tatlin/releases).

### Arch Linux

Tatlin is also available in the [AUR](https://aur.archlinux.org/packages/tatlin/).

Running from Source
-------------------

For those wishing to forego the prebuilt packages (e.g. for development
purposes), the preferred way to run the application from source is by using
[venv](https://docs.python.org/3/library/venv.html),
[virtualenv](https://virtualenv.pypa.io/en/latest/),
[pipenv](https://pipenv.readthedocs.io/en/latest/) or similar. Once you have a
virtual environment set up and activated, install the dependencies:

    $ pip install -r requirements.txt

You can then run Tatlin with:

    $ python tatlin.py

Usage
-----

You can provide an optional filename to load:

    $ python tatlin.py filename.stl

Mouse navigation

- Left mouse button to rotate
- Mouse wheel to zoom
- Middle mouse button to offset the platform
- Right mouse button to pan

Build platform size can be customed by creating a configuration file called
`.tatlin` in your user's home directory and specifying the width and depth of
the platform in millimeters:

    [machine]
    platform_w = 300
    platform_d = 300

Feedback and Issues
-------------------

To request features or report bugs, please use the
[GitHub Issues page](https://github.com/dkobozev/tatlin/issues).

Keep in mind that it can be very challenging to troubleshoot issues without
being able to reproduce them, so please include the relevant g-code or STL files
and steps to reproduce the issue in your report.
