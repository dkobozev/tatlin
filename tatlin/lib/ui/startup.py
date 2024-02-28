# -*- coding: utf-8 -*-
# Copyright (C) 2011 Denis Kobozev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

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
