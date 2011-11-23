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

from libtatlin.stlparser import StlParser
from libtatlin.actors import Platform
from libtatlin.scene import Scene
from libtatlin.ui import StlPanel, GcodePanel, MainWindow, \
SaveDialog, OpenDialog, OpenErrorAlert, QuitDialog
from libtatlin.storage import ModelFile, ModelFileError


def format_float(f):
    return "%.2f" % f


class ActionGroup(gtk.ActionGroup):
    def __init__(self, *args, **kwargs):
        gtk.ActionGroup.__init__(self, *args, **kwargs)

    def menu_item(self, action_name):
        item = self.get_action(action_name).create_menu_item()
        return item


class App(object):

    def __init__(self):
        # ---------------------------------------------------------------------
        # WINDOW SETUP
        # ---------------------------------------------------------------------

        self.window = MainWindow()

        self.actiongroup = self.set_up_actions()
        for menu_item in self.create_menu_items(self.actiongroup):
            self.window.append_menu_item(menu_item)

        self.window.connect('destroy',         self.on_quit)
        self.window.connect('open-clicked',    self.on_open)

        # ---------------------------------------------------------------------
        # SCENE SETUP
        # ---------------------------------------------------------------------

        self.panel = None
        self.scene = None
        self.model_file = None

        # dict of properties that other components can read from the app
        self._app_properties = {
            'layers_range_max': lambda: self.scene.get_property('max_layers'),
            'layers_value':     lambda: self.scene.get_property('max_layers'),
            'scaling-factor':   self.model_scaling_factor,
            'width':            self.model_width,
            'depth':            self.model_depth,
            'height':           self.model_height,
            'rotation-x':       self.model_rotation_x,
            'rotation-y':       self.model_rotation_y,
            'rotation-z':       self.model_rotation_z,
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
        actiongroup.add_action_with_accel(action_quit, '<Control>q')

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

    def model_rotation_x(self):
        angle = self.scene.get_property('rotation-x')
        return format_float(angle)

    def model_rotation_y(self):
        angle = self.scene.get_property('rotation-y')
        return format_float(angle)

    def model_rotation_z(self):
        angle = self.scene.get_property('rotation-z')
        return format_float(angle)

    @property
    def current_dir(self):
        """
        Return path where a file should be saved to.
        """
        if self.model_file is not None:
            dur = self.model_file.dirname
        else:
            dur = os.getcwd()
        return dur

    # -------------------------------------------------------------------------
    # EVENT HANDLERS
    # -------------------------------------------------------------------------

    def on_save(self, action=None):
        """
        Save changes to the same file.
        """
        self.scene.export_to_file(self.model_file)
        self.window.file_modified = False

    def on_save_as(self, action=None):
        """
        Save changes to a new file.
        """
        dialog = SaveDialog(self.current_dir)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            stl_file = ModelFile(dialog.get_filename())
            self.scene.export_to_file(stl_file)
            self.model_file = stl_file
            self.window.filename = stl_file.basename
            self.window.file_modified = False

        dialog.destroy()

    def on_open(self, action=None):
        dialog = OpenDialog(self.current_dir)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            self.open_and_display_file(dialog.get_filename())

        dialog.destroy()

    def on_quit(self, action=None):
        """
        On quit, show a dialog proposing to save the changes if the scene has
        been modified.
        """
        do_quit = True

        if self.scene.model_modified:
            dialog = QuitDialog(self.window)

            discard_changes = False
            while do_quit and self.scene.model_modified and not discard_changes:
                response = dialog.run()

                if response == QuitDialog.RESPONSE_SAVE:
                    dialog.hide()
                    self.on_save()
                elif response == QuitDialog.RESPONSE_SAVE_AS:
                    dialog.hide()
                    self.on_save_as()
                elif response in [QuitDialog.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
                    do_quit = False
                elif response == QuitDialog.RESPONSE_DISCARD:
                    discard_changes = True

            dialog.destroy()

        if do_quit:
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
        self.scene.change_num_layers(value)
        self.scene.invalidate()

    def rotation_changed(self, axis, angle):
        try:
            self.scene.rotate_model(float(angle), axis)
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
        try:
            self.model_file = ModelFile(fpath)

            if self.scene is None:
                self.scene = Scene()
                self.glarea = GLArea(self.scene)

            self.add_file_to_scene(self.model_file)

            if self.panel is None or not self.panel_matches_file():
                self.panel = self.create_panel()

            # update panel to reflect new model properties
            self.panel.set_initial_values()
            self.panel.connect_handlers()
            # always start with the same view on the scene
            self.scene.reset_view(True)
            self.scene.mode_2d = False

            self.window.set_file_widgets(self.glarea, self.panel)
            self.window.filename = self.model_file.basename
        except IOError, e:
            dialog = OpenErrorAlert(self.window, fpath, e.strerror)
            dialog.run()
            dialog.destroy()
        except ModelFileError, e:
            dialog = OpenErrorAlert(self.window, fpath, e.message)
            dialog.run()
            dialog.destroy()


    def add_file_to_scene(self, f):
        self.scene.clear()
        self.scene.load_file(f)
        self.scene.add_supporting_actor(Platform()) # platform needs to be added last to be translucent

    def create_panel(self):
        if self.model_file.filetype == 'gcode':
            Panel = GcodePanel
        elif self.model_file.filetype == 'stl':
            Panel = StlPanel
        return Panel(self)

    def panel_matches_file(self):
        matches = (self.model_file.filetype in self.panel.supported_types)
        return matches


if __name__ == '__main__':
    # configure logging
    logging.basicConfig(format='--- [%(levelname)s] %(message)s', level=logging.DEBUG)

    app = App()
    if len(sys.argv) > 1:
        app.open_and_display_file(sys.argv[1])
    app.show_window()
    gtk.main()

