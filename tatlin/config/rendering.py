import os
import sys
import logging

def configure_backend():
    """
    Configure the GLX/EGL backend for wxWidgets/PyOpenGL cooperation.
    """
    if sys.platform != 'linux':
        return

    conf = {}

    # Check for the existence of a system-wide config file written by a packaging script to help determine the correct
    # settings for the current environment. The conf resides in /etc/tatlin.conf, but a relative path must be used for this to work in an AppImage.
    base_dir = os.path.dirname(os.readlink('/proc/self/exe'))
    possible_paths = [
        '../../etc/tatlin.conf',
        '../../../etc/tatlin.conf'
    ]

    for possible_path in possible_paths:
        sys_conf_path = os.path.abspath(os.path.join(base_dir, possible_path))

        if os.path.exists(sys_conf_path):
            logging.info("Loading system-wide config from {}".format(sys_conf_path))

            with open(sys_conf_path) as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    key, value = line.strip().split('=')
                    conf[key] = value

            break

    # but the environment variables take precedence over the system-wide file
    if os.environ.get('GDK_BACKEND'):
        conf['GDK_BACKEND'] = os.environ['GDK_BACKEND']

    if os.environ.get('PYOPENGL_PLATFORM'):
        conf['PYOPENGL_PLATFORM'] = os.environ['PYOPENGL_PLATFORM']

    if conf.get('GDK_BACKEND'):
        os.environ['GDK_BACKEND'] = conf['GDK_BACKEND']
    elif os.environ.get('XDG_SESSION_TYPE') == 'wayland':
        # wxWidgets might be compiled with --disable-glcanvasegl due to Wayland issues like it is on Fedora 38
        # For example, see
        #     https://github.com/prusa3d/PrusaSlicer/issues/9774
        # The workaround is to instruct the underlying GTK to use X11 instead
        #     https://docs.gtk.org/gtk4/running.html#gdk_backend
        os.environ['GDK_BACKEND'] = 'x11'

    if conf.get('PYOPENGL_PLATFORM'):
        os.environ['PYOPENGL_PLATFORM'] = conf['PYOPENGL_PLATFORM']
    else:
        # PyOpenGL should match the backend wxWidgets are using, except there doesn't seem to be a straightforward way
        # to determine the backend at runtime
        os.environ['PYOPENGL_PLATFORM'] = 'x11'

    if conf.get('IGNORE_PLATFORM_CONTEXT'):
        # Which brings us to the worst case scenario that exists on Arch at the time of writing (Oct 2023): wxWidgets is
        # compiled with EGL support, but the version of PyOpenGL in the repo is 2.6, which does not yet support EGL,
        # resulting in PyOpenGL unable to obtain a GLX context. The best we can do under the circumstances it seems is
        # to ignore the fact a GLX context is not available and hope for the best.

        # IMPORTANT: PYOPENGL_PLATFORM must be set before importing OpenGL
        from OpenGL import platform, contextdata

        def getContext(context=None):
            if context is None:
                context = platform.GetCurrentContext()

            return context

        contextdata.getContext = getContext
