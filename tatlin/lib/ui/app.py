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
