import os
import sys

def configure_backend():
    if sys.platform != 'linux':
        return

    # if we're running under Wayland, the chances are wxGTK was compiled with
    # --disable-glcanvasegl to support some software that does not yet work
    # under EGL, like PrusaSlicer (see: https://github.com/prusa3d/PrusaSlicer/issues/9774)
    # so we need to force wxGTK to use the X11 backend
    if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
        os.environ['GDK_BACKEND'] = 'x11'
        os.environ['PYOPENGL_PLATFORM'] = 'x11' # glx
    # otherwise EGL is the default unless already set
    elif 'PYOPENGL_PLATFORM' not in os.environ:
        os.environ['PYOPENGL_PLATFORM'] = 'egl'
