import os
import sys

from OpenGL import platform

def __patched_get_context(context=None):
    """getContext() replacement for monkey-patching until this is fixed in PyOpenGL."""
    if context is None:
        context = platform.GetCurrentContext()
        if context is None: # fixed: 0 is a valid context-id
            from OpenGL import error
            raise error.Error(
                """Attempt to retrieve context when no valid context"""
            )
    return context

def configure_backend():
    if sys.platform != 'linux':
        return

    # if we're running under Wayland, the chances are wxGTK was compiled with
    # --disable-glcanvasegl to support some software that does not yet work
    # under EGL, like PrusaSlicer (see: https://github.com/prusa3d/PrusaSlicer/issues/9774)
    # so we need to force wxGTK to use the X11 backend
    if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
        os.environ['GDK_BACKEND'] = 'x11'

    if 'PYOPENGL_PLATFORM' not in os.environ:
        # use GLX as the default backend as wxWidgets does not support EGL under
        # X11 on Ubuntu and EGL GLUT support was only added to PyOpenGL in 3.1.7
        # see: https://github.com/mcfletch/pyopengl/commit/2d2457b4d565bce1c58b76b427e1f9027e8b4bcc
        os.environ['PYOPENGL_PLATFORM'] = 'glx'

    # monkey-patch PyOpenGL's context retrieval - needed as of 3.1.7
    from OpenGL import contextdata
    contextdata.getContext = __patched_get_context
