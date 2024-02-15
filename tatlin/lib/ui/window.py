import wx

from .startup import StartupPanel


class MainWindow(wx.Frame):
    def __init__(self, app):
        self._app_name = "Tatlin"
        self.app = app

        super(MainWindow, self).__init__(None, title=self._app_name)

        self._file_modified = False
        self._filename = None

        file_menu = wx.Menu()
        item_open = file_menu.Append(wx.ID_OPEN, "&Open", "Open file")
        self.recent_files_menu = wx.Menu()
        self.recent_files_item = file_menu.Append(
            wx.ID_ANY, "&Recent files", self.recent_files_menu
        )
        item_save = file_menu.Append(wx.ID_SAVE, "&Save", "Save changes")
        item_save.Enable(False)
        item_save_as = file_menu.Append(
            wx.ID_SAVEAS, "Save As...\tShift+Ctrl+S", "Save under a different filename"
        )
        item_save_as.Enable(False)
        item_quit = file_menu.Append(wx.ID_EXIT, "&Quit", "Quit %s" % self._app_name)

        self.menu_items_file = [item_save, item_save_as]

        help_menu = wx.Menu()
        item_about = help_menu.Append(wx.ID_ABOUT, "&About %s" % self._app_name)

        self.menubar = wx.MenuBar()
        self.menubar.Append(file_menu, "&File")
        self.menubar.Append(help_menu, "&Help")

        self.Bind(wx.EVT_MENU, app.on_file_open, item_open)
        self.Bind(wx.EVT_MENU, app.on_file_save, item_save)
        self.Bind(wx.EVT_MENU, app.on_file_save_as, item_save_as)
        self.Bind(wx.EVT_MENU, app.on_quit, item_quit)
        self.Bind(wx.EVT_MENU, app.on_about, item_about)

        self.box_scene = wx.BoxSizer(wx.HORIZONTAL)

        self.panel_startup = StartupPanel(self)
        self.panel_startup.btn_open.Bind(wx.EVT_BUTTON, app.on_file_open)

        self.box_main = wx.BoxSizer(wx.VERTICAL)
        self.box_main.Add(self.panel_startup, 1, wx.EXPAND)

        self.SetMenuBar(self.menubar)
        self.statusbar = self.CreateStatusBar()
        self.SetSizer(self.box_main)

        # Set minimum frame size so that the widgets contained within are not squashed.
        # I wish there was a reliable way to set the minimum size based on minimum
        # sizes of widgets contained in the frame, but wxPython ignores the dimensions
        # of window decorations (borders and titlebar) in addition to other minor quirks.
        # Hardcoding the minimum size seems no less portable and reliable, and also
        # much easier.
        self.SetSizeHints(400, 700, self.GetMaxWidth(), self.GetMaxHeight())
        self.Center()

        self.Bind(wx.EVT_CLOSE, app.on_quit)
        self.Bind(wx.EVT_ICONIZE, self.on_iconize)

    def set_icon(self, icon):
        self.SetIcon(icon)

    def quit(self):
        self.Destroy()

    def show_all(self):
        self.Show()

    def get_size(self):
        return self.GetSize()

    def set_size(self, size):
        self.SetSize(size)

    def set_file_widgets(self, scene, panel):
        # remove startup panel if present
        if self._filename is None:
            self.panel_startup.Destroy()
            self.box_main.Add(self.box_scene, 1, wx.EXPAND)
        # remove previous scene and panel, if any, destroying the widgets
        self.box_scene.Clear(True)
        self.box_scene.Add(scene, 1, wx.EXPAND)
        self.box_scene.Add(panel, 0, wx.EXPAND)
        self.box_scene.ShowItems(True)
        self.Layout()  # without this call, wxPython does not draw the new widgets until window resize

    def menu_enable_file_items(self, enable=True):
        for item in self.menu_items_file:
            item.Enable(enable)

    def update_recent_files_menu(self, recent_files):
        for menu_item in self.recent_files_menu.GetMenuItems():
            self.recent_files_menu.Delete(menu_item)

        for recent_file in recent_files:
            item = self.recent_files_menu.Append(wx.ID_ANY, recent_file[0])

            def callback(f, t):
                return lambda x: self.app.open_and_display_file(f, t)

            self.Bind(wx.EVT_MENU, callback(recent_file[1], recent_file[2]), item)

        self.recent_files_item.Enable(len(recent_files) > 0)

    def update_status(self, text):
        self.statusbar.SetStatusText(text)

    def on_iconize(self, event):
        if not self.IsIconized():
            # call Layout() when the frame is unminimized; otherwise the window
            # will be blank if the frame was minimized while the model was loading
            self.Layout()
        event.Skip()

    @property
    def file_modified(self):
        return self._file_modified

    @file_modified.setter
    def file_modified(self, value):
        self._file_modified = value
        self._title_changed()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value
        self._title_changed()

    def _title_changed(self):
        """Format and set title."""
        title = self._app_name
        if self._filename is not None:
            filename = self._filename
            if self._file_modified:
                filename = "*" + filename
            title = filename + " - " + title
        self.SetTitle(title)
