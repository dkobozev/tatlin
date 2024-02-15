import wx


class ViewButtons(wx.FlexGridSizer):
    def __init__(self, parent, scene):
        super(ViewButtons, self).__init__(rows=3, cols=3, vgap=0, hgap=0)

        self.scene = scene

        self.btn_front = wx.Button(parent, label="Front")
        self.btn_back = wx.Button(parent, label="Back")
        self.btn_left = wx.Button(parent, label="Left")
        self.btn_right = wx.Button(parent, label="Right")

        self.btn_top = wx.Button(parent, label="Top")
        self.btn_bottom = wx.Button(parent, label="Bottom")

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.btn_top, 0, wx.EXPAND)
        vbox.Add(self.btn_bottom, 0, wx.EXPAND)

        self.Add((0, 0), 0, wx.EXPAND)
        self.Add(self.btn_back, 0, wx.EXPAND)
        self.Add((0, 0), 0, wx.EXPAND)
        self.Add(self.btn_left, 0, wx.EXPAND)
        self.Add(vbox, 0, wx.EXPAND)
        self.Add(self.btn_right, 0, wx.EXPAND)
        self.Add((0, 0), 0, wx.EXPAND)
        self.Add(self.btn_front, 0, wx.EXPAND)
        self.Add((0, 0), 0, wx.EXPAND)

        # connect handlers
        self.btn_front.Bind(wx.EVT_BUTTON, self.on_view_front)
        self.btn_back.Bind(wx.EVT_BUTTON, self.on_view_back)
        self.btn_left.Bind(wx.EVT_BUTTON, self.on_view_left)
        self.btn_right.Bind(wx.EVT_BUTTON, self.on_view_right)
        self.btn_top.Bind(wx.EVT_BUTTON, self.on_view_top)
        self.btn_bottom.Bind(wx.EVT_BUTTON, self.on_view_bottom)

    def on_view_front(self, event):
        self.scene.rotate_view(0, 0)

    def on_view_back(self, event):
        self.scene.rotate_view(180, 0)

    def on_view_left(self, event):
        self.scene.rotate_view(90, 0)

    def on_view_right(self, event):
        self.scene.rotate_view(-90, 0)

    def on_view_top(self, event):
        self.scene.rotate_view(0, -90)

    def on_view_bottom(self, event):
        self.scene.rotate_view(0, 90)
