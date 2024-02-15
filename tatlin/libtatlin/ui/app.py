import wx


class BaseApp(wx.App):
    def __init__(self):
        super(BaseApp, self).__init__()

        global app
        app = self

    def run(self):
        self.MainLoop()

    def process_ui_events(self):
        self.Yield()

    def set_wait_cursor(self):
        wx.SetCursor(wx.Cursor(wx.CURSOR_WAIT))

    def set_normal_cursor(self):
        wx.SetCursor(wx.NullCursor)
