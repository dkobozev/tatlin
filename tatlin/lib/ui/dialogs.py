import wx
import wx.adv


class OpenDialog(wx.FileDialog):
    ftypes = (None, "gcode", "stl")

    def __init__(self, parent, directory=None):
        super(OpenDialog, self).__init__(
            parent,
            "Open",
            wildcard="G-code and STL files (*.gcode;*.nc;*.stl)|*.gcode;*.nc;*.stl|G-code files (*.*)|*.*|STL files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )

        if directory is not None:
            self.SetDirectory(directory)

    def get_path(self):
        if self.ShowModal() == wx.ID_CANCEL:
            return None
        return self.GetPath()

    def get_type(self):
        return self.ftypes[self.GetFilterIndex()]


class OpenErrorAlert(wx.MessageDialog):
    def __init__(self, fpath, error):
        msg = "Error opening file %s: %s" % (fpath, error)
        super(OpenErrorAlert, self).__init__(None, msg, "Error", wx.OK | wx.ICON_ERROR)

    def show(self):
        self.ShowModal()


class SaveDialog(wx.FileDialog):
    def __init__(self, parent, directory=None):
        super(SaveDialog, self).__init__(
            parent,
            "Save As",
            wildcard="STL files (*.stl)|*.stl",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        if directory is not None:
            self.SetDirectory(directory)

    def get_path(self):
        if self.ShowModal() == wx.ID_CANCEL:
            return None
        return self.GetPath()


class QuitDialog(wx.Dialog):
    RESPONSE_CANCEL = -1
    RESPONSE_DISCARD = 0
    RESPONSE_SAVE_AS = 1
    RESPONSE_SAVE = 2

    def __init__(self, parent):
        super(QuitDialog, self).__init__(parent, title="Save changes?")

        label = wx.StaticText(self, label="Save changes to the file before closing?")

        self.btn_discard = wx.Button(self, label="Discard")
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL)
        self.btn_save_as = wx.Button(self, wx.ID_SAVEAS)
        self.btn_save = wx.Button(self, wx.ID_SAVE)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.btn_discard, 0)
        hbox.Add(self.btn_cancel, 0, wx.LEFT, border=5)
        hbox.Add(self.btn_save_as, 0, wx.LEFT, border=5)
        hbox.Add(self.btn_save, 0, wx.LEFT, border=5)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, 0, wx.EXPAND | wx.ALL, border=5)
        vbox.Add(hbox, -1, wx.EXPAND | wx.RIGHT | wx.BOTTOM | wx.LEFT, border=5)

        self.SetSizer(vbox)
        self.SetSize((399, 90))

        self.btn_discard.Bind(wx.EVT_BUTTON, self.on_discard)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.btn_save_as.Bind(wx.EVT_BUTTON, self.on_save_as)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)

    def on_discard(self, event):
        self.EndModal(self.RESPONSE_DISCARD)

    def on_cancel(self, event):
        self.EndModal(self.RESPONSE_CANCEL)

    def on_save_as(self, event):
        self.EndModal(self.RESPONSE_SAVE_AS)

    def on_save(self, event):
        self.EndModal(self.RESPONSE_SAVE)

    def show(self):
        return self.ShowModal()


class ProgressDialog(wx.ProgressDialog):
    def __init__(self):
        super(ProgressDialog, self).__init__("Loading", "", 100)

        self.value = -1

    def stage(self, message):
        self.Show()
        self.Update(0, message)

    def step(self, count, limit):
        self.value = max(-1, min(int(count / limit * 100), 100))
        self.Update(self.value)

    def hide(self):
        self.Hide()

    def destroy(self):
        self.Destroy()


class AboutDialog(object):
    def __init__(self, version, icon, license):
        from datetime import datetime

        info = wx.adv.AboutDialogInfo()

        info.SetName("Tatlin")
        info.SetVersion("v%s" % version)
        info.SetIcon(icon)
        info.SetDescription("Gcode and STL viewer for 2D printing")
        info.SetCopyright(
            "(C) 2010-%s Denis Kobozev" % datetime.strftime(datetime.now(), "%Y")
        )
        info.SetWebSite("https://tatlin2d.com/")
        info.AddDeveloper("Denis Kobozev <d.v.kobozev@gmail.com>")
        info.SetLicence(license)

        dialog = wx.adv.AboutBox(info)
