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

from tatlin.lib.gl.model import Model
from tatlin.lib.util import format_float

from .view import ViewButtons


class StlPanel(wx.Panel):
    supported_types = ["stl"]

    def __init__(self, parent, scene, panel, app):
        super(StlPanel, self).__init__(parent)

        self._handlers_connected = False

        self.scene = scene
        self.panel = panel
        self.app = app

        # ----------------------------------------------------------------------
        # DIMENSIONS
        # ----------------------------------------------------------------------

        static_box_dimensions = wx.StaticBox(self, label="Dimensions")
        sizer_dimensions = wx.StaticBoxSizer(static_box_dimensions, wx.VERTICAL)

        label_x = wx.StaticText(self, label="X:")
        self.entry_x = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        label_x_units = wx.StaticText(self, label="mm")

        label_y = wx.StaticText(self, label="Y:")
        self.entry_y = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        label_y_units = wx.StaticText(self, label="mm")

        label_z = wx.StaticText(self, label="Z:")
        self.entry_z = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        label_z_units = wx.StaticText(self, label="mm")

        label_factor = wx.StaticText(self, label="Factor:")
        self.entry_factor = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)

        grid_dimensions = wx.FlexGridSizer(4, 3, 5, 5)
        grid_dimensions.Add(label_x, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(self.entry_x, 0, wx.EXPAND)
        grid_dimensions.Add(label_x_units, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_dimensions.Add(label_y, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(self.entry_y, 0, wx.EXPAND)
        grid_dimensions.Add(label_y_units, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_dimensions.Add(label_z, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(self.entry_z, 0, wx.EXPAND)
        grid_dimensions.Add(label_z_units, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_dimensions.Add(label_factor, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(self.entry_factor, 0, wx.EXPAND)
        grid_dimensions.AddGrowableCol(1)

        sizer_dimensions.Add(grid_dimensions, 0, wx.EXPAND | wx.ALL, border=5)

        # ----------------------------------------------------------------------
        # MOVE
        # ----------------------------------------------------------------------

        static_box_move = wx.StaticBox(self, label="Move")
        sizer_move = wx.StaticBoxSizer(static_box_move, wx.VERTICAL)

        self.btn_center = wx.Button(self, label="Center model")

        sizer_move.Add(self.btn_center, 0, wx.EXPAND | wx.ALL, border=5)

        # ----------------------------------------------------------------------
        # ROTATE
        # ----------------------------------------------------------------------

        static_box_rotate = wx.StaticBox(self, label="Rotate")
        sizer_rotate = wx.StaticBoxSizer(static_box_rotate, wx.VERTICAL)

        self.btn_x_90 = wx.Button(self, label="+90")
        label_rotate_x = wx.StaticText(self, label="X:")
        self.entry_rotate_x = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        sizer_entry_x = wx.BoxSizer(wx.HORIZONTAL)
        sizer_entry_x.Add(self.entry_rotate_x, 1, wx.ALIGN_CENTER_VERTICAL)

        self.btn_y_90 = wx.Button(self, label="+90")
        label_rotate_y = wx.StaticText(self, label="Y:")
        self.entry_rotate_y = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        sizer_entry_y = wx.BoxSizer(wx.HORIZONTAL)
        sizer_entry_y.Add(self.entry_rotate_y, 1, wx.ALIGN_CENTER_VERTICAL)

        self.btn_z_90 = wx.Button(self, label="+90")
        label_rotate_z = wx.StaticText(self, label="Z:")
        self.entry_rotate_z = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        sizer_entry_z = wx.BoxSizer(wx.HORIZONTAL)
        sizer_entry_z.Add(self.entry_rotate_z, 1, wx.ALIGN_CENTER_VERTICAL)

        grid_rotate = wx.FlexGridSizer(3, 3, 5, 5)
        grid_rotate.Add(self.btn_x_90, 0)
        grid_rotate.Add(label_rotate_x, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_rotate.Add(sizer_entry_x, 0, wx.EXPAND)
        grid_rotate.Add(self.btn_y_90, 0)
        grid_rotate.Add(label_rotate_y, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_rotate.Add(sizer_entry_y, 0, wx.EXPAND)
        grid_rotate.Add(self.btn_z_90, 0)
        grid_rotate.Add(label_rotate_z, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_rotate.Add(sizer_entry_z, 0, wx.EXPAND)
        grid_rotate.AddGrowableCol(2)

        sizer_rotate.Add(grid_rotate, 0, wx.EXPAND | wx.ALL, border=5)

        # ----------------------------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------------------------

        static_box_display = wx.StaticBox(self, label="Display")
        sizer_display = wx.StaticBoxSizer(static_box_display, wx.VERTICAL)

        view_buttons = ViewButtons(self, scene)
        self.check_ortho = wx.CheckBox(self, label="Orthographic projection")
        self.btn_reset_view = wx.Button(self, label="Reset view")

        box_display = wx.BoxSizer(wx.VERTICAL)
        box_display.Add(view_buttons, 0, wx.ALIGN_CENTER | wx.TOP, border=5)
        box_display.Add(self.check_ortho, 0, wx.EXPAND | wx.TOP, border=5)
        box_display.Add(self.btn_reset_view, 0, wx.EXPAND | wx.TOP, border=5)

        sizer_display.Add(box_display, 0, wx.EXPAND | wx.ALL, border=5)

        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(sizer_dimensions, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border=5)
        box.Add(sizer_move, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border=5)
        box.Add(sizer_rotate, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border=5)
        box.Add(sizer_display, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border=5)

        self.SetSizer(box)

    def connect_handlers(self):
        if self._handlers_connected:
            return

        # ----------------------------------------------------------------------
        # DIMENSIONS
        # ----------------------------------------------------------------------

        self.entry_x.Bind(wx.EVT_KILL_FOCUS, self.on_entry_x_focus_out)
        self.entry_x.Bind(wx.EVT_TEXT_ENTER, self.on_entry_x_focus_out)

        self.entry_y.Bind(wx.EVT_KILL_FOCUS, self.on_entry_y_focus_out)
        self.entry_y.Bind(wx.EVT_TEXT_ENTER, self.on_entry_y_focus_out)

        self.entry_z.Bind(wx.EVT_KILL_FOCUS, self.on_entry_z_focus_out)
        self.entry_z.Bind(wx.EVT_TEXT_ENTER, self.on_entry_z_focus_out)

        self.entry_factor.Bind(wx.EVT_KILL_FOCUS, self.on_entry_factor_focus_out)
        self.entry_factor.Bind(wx.EVT_TEXT_ENTER, self.on_entry_factor_focus_out)

        # ----------------------------------------------------------------------
        # ROTATE
        # ----------------------------------------------------------------------

        self.entry_rotate_x.Bind(wx.EVT_KILL_FOCUS, self.on_entry_rotate_x_focus_out)
        self.entry_rotate_x.Bind(wx.EVT_TEXT_ENTER, self.on_entry_rotate_x_focus_out)

        self.entry_rotate_y.Bind(wx.EVT_KILL_FOCUS, self.on_entry_rotate_y_focus_out)
        self.entry_rotate_y.Bind(wx.EVT_TEXT_ENTER, self.on_entry_rotate_y_focus_out)

        self.entry_rotate_z.Bind(wx.EVT_KILL_FOCUS, self.on_entry_rotate_z_focus_out)
        self.entry_rotate_z.Bind(wx.EVT_TEXT_ENTER, self.on_entry_rotate_z_focus_out)

        self.btn_x_90.Bind(wx.EVT_BUTTON, self.on_x_90_clicked)
        self.btn_y_90.Bind(wx.EVT_BUTTON, self.on_y_90_clicked)
        self.btn_z_90.Bind(wx.EVT_BUTTON, self.on_z_90_clicked)

        # ----------------------------------------------------------------------
        # MOVE
        # ----------------------------------------------------------------------

        self.btn_center.Bind(wx.EVT_BUTTON, self.on_center_clicked)

        # ----------------------------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------------------------

        self.check_ortho.Bind(wx.EVT_CHECKBOX, self.on_set_ortho)
        self.btn_reset_view.Bind(wx.EVT_BUTTON, self.on_reset_clicked)

        self._handlers_connected = True

    def scaling_factor_changed(self, factor):
        try:
            self.scene.scale_model(float(factor))
            self.scene.invalidate()
            # tell all the widgets that care about model size that it has changed
            self.panel.model_size_changed()
            self.GetParent().file_modified = self.scene.model_modified
        except ValueError:
            pass  # ignore invalid values

    def dimension_changed(self, dimension, value):
        try:
            self.scene.change_model_dimension(dimension, float(value))
            self.scene.invalidate()
            self.panel.model_size_changed()
            self.GetParent().file_modified = self.scene.model_modified
        except ValueError:
            pass  # ignore invalid values

    def rotation_changed(self, axis, angle):
        try:
            self.scene.model.rotate_abs(float(angle), axis)
            self.scene.model.init()
            self.scene.invalidate()

            self.GetParent().file_modified = self.scene.model_modified
        except ValueError:
            pass  # ignore invalid values

    def on_entry_x_focus_out(self, event):
        self.dimension_changed("width", self.entry_x.GetValue())
        event.Skip()

    def on_entry_y_focus_out(self, event):
        self.dimension_changed("depth", self.entry_y.GetValue())
        event.Skip()

    def on_entry_z_focus_out(self, event):
        self.dimension_changed("height", self.entry_z.GetValue())
        event.Skip()

    def on_entry_factor_focus_out(self, event):
        self.scaling_factor_changed(self.entry_factor.GetValue())
        event.Skip()

    def on_entry_rotate_x_focus_out(self, event):
        self.rotation_changed(Model.AXIS_X, self.entry_rotate_x.GetValue())
        self.model_angle_changed()
        event.Skip()

    def on_entry_rotate_y_focus_out(self, event):
        self.rotation_changed(Model.AXIS_Y, self.entry_rotate_y.GetValue())
        self.model_angle_changed()
        event.Skip()

    def on_entry_rotate_z_focus_out(self, event):
        self.rotation_changed(Model.AXIS_Z, self.entry_rotate_z.GetValue())
        self.model_angle_changed()
        event.Skip()

    def on_x_90_clicked(self, event):
        self.rotate_relative(Model.AXIS_X, 90)

    def on_y_90_clicked(self, event):
        self.rotate_relative(Model.AXIS_Y, 90)

    def on_z_90_clicked(self, event):
        self.rotate_relative(Model.AXIS_Z, 90)

    def rotate_relative(self, axis, angle):
        current_angle = self.scene.model.rotation_angle[axis]
        angle = current_angle + angle
        self.rotation_changed(axis, angle)
        self.model_angle_changed()

    def set_initial_values(self, layers_range_max, layers_value, width, height, depth):
        self._set_size_properties()
        self._set_rotation_properties()

    def _set_size_properties(self):
        self.entry_x.SetValue(format_float(self.scene.model.width))
        self.entry_y.SetValue(format_float(self.scene.model.depth))
        self.entry_z.SetValue(format_float(self.scene.model.height))
        self.entry_factor.SetValue(
            format_float(round(self.scene.model.scaling_factor, 2))
        )

    def _set_rotation_properties(self):
        self.entry_rotate_x.SetValue(
            format_float(self.scene.model.rotation_angle[Model.AXIS_X])
        )
        self.entry_rotate_y.SetValue(
            format_float(self.scene.model.rotation_angle[Model.AXIS_Y])
        )
        self.entry_rotate_z.SetValue(
            format_float(self.scene.model.rotation_angle[Model.AXIS_Z])
        )

    def model_size_changed(self):
        self._set_size_properties()

    def model_angle_changed(self):
        self._set_rotation_properties()

    def on_center_clicked(self, event):
        self.scene.center_model()
        self.scene.invalidate()
        self.GetParent().file_modified = self.scene.model_modified

    def on_reset_clicked(self, event):
        self.scene.reset_view()
        self.scene.invalidate()

    def on_set_ortho(self, event):
        self.scene.mode_ortho = event.GetEventObject().GetValue()
        self.scene.invalidate()
