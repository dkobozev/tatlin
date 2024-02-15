import wx


class StartupPanel(wx.Panel):
    def __init__(self, parent):
        super(StartupPanel, self).__init__(parent)

        text = wx.StaticText(self, label="No files loaded")
        self.btn_open = wx.Button(self, wx.ID_OPEN)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add((0, 0), 1, wx.EXPAND)
        box.Add(text, 0, wx.ALIGN_CENTER | wx.ALL, border=5)
        box.Add(
            self.btn_open, 0, wx.ALIGN_CENTER | wx.RIGHT | wx.BOTTOM | wx.LEFT, border=5
        )
        box.Add((0, 0), 1, wx.EXPAND)

        self.SetSizer(box)
