import wx
from wx import glcanvas
from wx.glcanvas import WX_GL_DEPTH_SIZE


class BaseScene(glcanvas.GLCanvas):
    def __init__(self, parent):
        try:  # the new way
            super(BaseScene, self).__init__(parent, self._get_display_attributes())
        except AttributeError:  # the old way
            super(BaseScene, self).__init__(parent, attribList=self._get_attrib_list())

        self.Hide()

        self.initialized = False
        self.context = glcanvas.GLContext(self)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self._on_erase_background)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_mouse_down)
        self.Bind(wx.EVT_MOTION, self._on_mouse_motion)

        # make it unnecessary for the scene to be in focus to respond to the
        # mouse wheel by binding the mouse wheel event to the parent; if we
        # bound the event to the scene itself, the user would have to click on
        # the scene before scrolling each time the scene loses focus (users who
        # have the fortune of being able to use a window manager that has a
        # setting for focus-follows-mouse wouldn't care either way, since their
        # wm would handle it for them)
        parent.Bind(wx.EVT_MOUSEWHEEL, self._on_mouse_wheel)

        methods = [
            "init",
            "display",
            "reshape",
            "button_press",
            "button_motion",
            "wheel_scroll",
        ]
        for method in methods:
            if not hasattr(self, method):
                raise Exception("Method %s() is not implemented" % method)

    @staticmethod
    def _get_display_attributes():
        """Get the display attributes when using wxPython 4.1 or later."""
        for depth in [32, 24, 16, 8]:
            dispAttrs = glcanvas.GLAttributes()
            dispAttrs.PlatformDefaults().DoubleBuffer().Depth(depth).EndList()

            if glcanvas.GLCanvas.IsDisplaySupported(dispAttrs):
                return dispAttrs
        else:
            raise Exception("No suitable depth buffer value found")

    @staticmethod
    def _get_attrib_list():
        """Get the display attributes when using wxPython 4.0 or earlier."""
        for depth in [32, 24, 16, 8]:
            attrib_list = [
                glcanvas.WX_GL_RGBA,
                glcanvas.WX_GL_DOUBLEBUFFER,
                glcanvas.WX_GL_DEPTH_SIZE,
                depth,
                0,
            ]

            if glcanvas.GLCanvas.IsDisplaySupported(attrib_list):
                return attrib_list
        else:
            raise Exception("No suitable depth buffer value found")

    def invalidate(self):
        self.Refresh(False)

    def _on_erase_background(self, event):
        pass  # Do nothing, to avoid flashing on MSW. Doesn't seem to be working, though :(

    def _on_size(self, event):
        wx.CallAfter(self._set_viewport)
        event.Skip()

    def _set_viewport(self):
        self.SetCurrent(self.context)
        size = self.GetClientSize()
        self.reshape(size.width, size.height)

    def _on_paint(self, event):
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)
        if not self.initialized:
            self.init()
            self.initialized = True
        size = self.GetClientSize()
        self.display(size.width, size.height)
        self.SwapBuffers()

    def _on_mouse_down(self, event):
        self.SetFocus()
        x, y = event.GetPosition()
        self.button_press(x, y)

    def _on_mouse_motion(self, event):
        x, y = event.GetPosition()
        left = event.LeftIsDown()
        middle = event.MiddleIsDown()
        right = event.RightIsDown()
        self.button_motion(x, y, left, middle, right)

    def _on_mouse_wheel(self, event):
        self.wheel_scroll(event.GetWheelRotation())
