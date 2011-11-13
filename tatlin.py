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


from __future__ import division

import sys
import os
import logging

import pygtk
pygtk.require('2.0')
import gtk
from gtk.gtkgl.apputils import GLArea

from libtatlin.gcodeparser import GcodeParser
from libtatlin.stlparser import StlParser
from libtatlin.vector3 import Vector3
from libtatlin.actors import Platform, GcodeModel, StlModel
from libtatlin.scene import Scene
from libtatlin.ui import StlPanel, GcodePanel, MainWindow


def format_float(f):
    return "%.2f" % f


class ActionGroup(gtk.ActionGroup):
    def __init__(self, *args, **kwargs):
        gtk.ActionGroup.__init__(self, *args, **kwargs)

    def menu_item(self, action_name):
        item = self.get_action(action_name).create_menu_item()
        return item


class App(object):
    _axis_map = {
        'x': [1, 0, 0],
        'y': [0, 1, 0],
        'z': [0, 0, 1],
    }

    def __init__(self):
        # ---------------------------------------------------------------------
        # WINDOW SETUP
        # ---------------------------------------------------------------------

        self.window = MainWindow()

        self.actiongroup = self.set_up_actions()
        for menu_item in self.create_menu_items(self.actiongroup):
            self.window.append_menu_item(menu_item)

        self.window.connect('destroy',         self.on_quit)
        self.window.connect('key-press-event', self.on_keypress)
        self.window.connect('open-clicked',    self.on_open)

        # ---------------------------------------------------------------------
        # SCENE SETUP
        # ---------------------------------------------------------------------

        self.panel = None
        self.scene = None

        # dict of properties that other components can read from the app
        self._app_properties = {
            'layers_range_max': lambda: self.scene.get_property('max_layers'),
            'layers_value':     lambda: self.scene.get_property('max_layers'),
            'scaling-factor':   self.model_scaling_factor,
            'width':            self.model_width,
            'depth':            self.model_depth,
            'height':           self.model_height,
        }

    def show_window(self):
        self.window.show_all()

    # -------------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------------

    def set_up_actions(self):
        actiongroup = ActionGroup('main')
        actiongroup.add_action(gtk.Action('file', '_File', 'File', None))

        action_open = gtk.Action('open', 'Open', 'Open', gtk.STOCK_OPEN)
        action_open.connect('activate', self.on_open)
        actiongroup.add_action_with_accel(action_open, '<Control>o')

        save_as = gtk.Action('save-as', 'Save As...', 'Save As...', gtk.STOCK_SAVE_AS)
        save_as.connect('activate', self.on_save_as)
        actiongroup.add_action_with_accel(save_as, '<Control><Shift>s')

        action_quit = gtk.Action('quit', 'Quit', 'Quit', gtk.STOCK_QUIT)
        action_quit.connect('activate', self.on_quit)
        actiongroup.add_action(action_quit)

        accelgroup = gtk.AccelGroup()
        for action in actiongroup.list_actions():
            action.set_accel_group(accelgroup)

        self.window.add_accel_group(accelgroup)

        return actiongroup

    def create_menu_items(self, actiongroup):
        file_menu = gtk.Menu()
        file_menu.append(actiongroup.menu_item('open'))
        file_menu.append(actiongroup.menu_item('save-as'))
        file_menu.append(actiongroup.menu_item('quit'))

        item_file = actiongroup.menu_item('file')
        item_file.set_submenu(file_menu)

        return [item_file]

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    def get_property(self, name):
        """
        Return a property of the application.
        """
        return self._app_properties[name]()

    def model_scaling_factor(self):
        factor = self.scene.get_property('scaling-factor')
        return format_float(factor)

    def model_width(self):
        width = self.scene.get_property('width')
        return format_float(width)

    def model_depth(self):
        depth = self.scene.get_property('depth')
        return format_float(depth)

    def model_height(self):
        height = self.scene.get_property('height')
        return format_float(height)

    # -------------------------------------------------------------------------
    # EVENT HANDLERS
    # -------------------------------------------------------------------------

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.on_quit()

    def on_save_as(self, action):
        dialog = gtk.FileChooserDialog('Save As', None,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
        dialog.set_do_overwrite_confirmation(True)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            from libtatlin.stlparser import StlFile
            stl_file = StlFile(self.model)
            stl_file.write(dialog.get_filename())
            self.window.file_modified = False

        dialog.destroy()

    def on_open(self, action=None):
        dialog = gtk.FileChooserDialog('Open', None, gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            self.open_and_display_file(dialog.get_filename())

        dialog.destroy()

    def on_quit(self, action=None):
        gtk.main_quit()

    def scaling_factor_changed(self, factor):
        try:
            factor = float(factor)
            self.scene.scale_model(factor)
            self.scene.invalidate()
            # tell all the widgets that care about model size that it has changed
            self.panel.model_size_changed()
            self.window.file_modified = self.scene.model_modified
        except ValueError:
            pass # ignore invalid values

    def dimension_changed(self, dimension, value):
        try:
            value = float(value)
            self.scene.change_model_dimension(dimension, value)
            self.scene.invalidate()
            self.panel.model_size_changed()
            self.window.file_modified = self.scene.model_modified
        except ValueError:
            pass # ignore invalid values

    def on_scale_value_changed(self, widget):
        value = int(widget.get_value())
        self.model.num_layers_to_draw = value
        self.scene.invalidate()

    def rotation_changed(self, axis, angle):
        vector = self._axis_map[axis]
        try:
            self.scene.rotate_model(float(angle), vector)
            self.scene.invalidate()
            self.window.file_modified = self.scene.model_modified
        except ValueError:
            pass # ignore invalid values

    def on_button_center_clicked(self, widget):
        """
        Center model on platform.
        """
        self.scene.center_model()
        self.scene.invalidate()
        self.window.file_modified = self.scene.model_modified

    def on_arrows_toggled(self, widget):
        """
        Show/hide arrows on the Gcode model.
        """
        self.scene.show_arrows(widget.get_active())
        self.scene.invalidate()

    def on_reset_view(self, widget):
        """
        Restore the view of the model shown on startup.
        """
        self.scene.reset_view()
        self.scene.invalidate()

    def on_set_mode(self, widget):
        self.scene.mode_2d = not widget.get_active()
        self.scene.invalidate()

    # -------------------------------------------------------------------------
    # FILE OPERATIONS
    # -------------------------------------------------------------------------

    def open_and_display_file(self, fpath):
        ftype = self.determine_model_type(fpath)

        if ftype == 'gcode':
            model = self.load_gcode_model(fpath)
            Panel = GcodePanel
        elif ftype == 'stl':
            model = self.load_stl_model(fpath)
            Panel = StlPanel

        if self.scene is None:
            self.scene = Scene()
            self.glarea = GLArea(self.scene)

        self.add_model_to_scene(model)

        if self.panel is None or ftype not in self.panel.supported_types:
            self.panel = Panel(self)

        self.panel.set_initial_values() # update panel to reflect new model properties
        self.panel.connect_handlers()
        self.scene.reset_view(True)     # always start with the same view on the scene
        self.scene.mode_2d = False

        self.window.set_file_widgets(self.glarea, self.panel)
        self.window.filename = os.path.basename(fpath)

    def determine_model_type(self, fpath):
        fname = os.path.basename(fpath)
        extension = os.path.splitext(fname)[-1].lower()

        if extension not in ['.gcode', '.stl']:
            raise Exception('Unknown file extension: %s' % extension)

        return extension[1:]

    def load_gcode_model(self, fpath):
        start_location = Vector3(Platform.width / 2, -Platform.depth / 2, 10.0)
        parser = GcodeParser(fpath, start_location)
        model = GcodeModel(parser.parse())
        return model

    def load_stl_model(self, fpath):
        parser = StlParser(fpath)
        model = StlModel(parser.parse())
        return model

    def add_model_to_scene(self, model):
        self.model = model

        self.scene.clear()
        self.scene.set_model(model)
        self.scene.add_supporting_actor(Platform()) # platform needs to be added last to be translucent


if __name__ == '__main__':
    # configure logging
    logging.basicConfig(format='--- [%(levelname)s] %(message)s', level=logging.DEBUG)

    app = App()
    if len(sys.argv) > 1:
        app.open_and_display_file(sys.argv[1])
    app.show_window()
    gtk.main()

