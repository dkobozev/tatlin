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

from libtatlin.actors import Platform
from libtatlin.scene import Scene, SceneArea
from libtatlin.ui import StlPanel, GcodePanel, MainWindow, \
SaveDialog, OpenDialog, OpenErrorAlert, QuitDialog, ProgressDialog
from libtatlin.storage import ModelFile, ModelFileError
from libtatlin.config import Config


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
        self.create_menu_items(self.actiongroup)
        for menu_item in self.menu_items:
            self.window.append_menu_item(menu_item)

        self.menu_enable_file_items(False)

        self.window.connect('destroy',      self.quit)
        self.window.connect('open-clicked', self.open_file_dialog)

        # ---------------------------------------------------------------------
        # APP SETUP
        # ---------------------------------------------------------------------

        self.init_config()

        window_w = self.config.read('ui.window_w', int)
        window_h = self.config.read('ui.window_h', int)
        self.window.set_default_size(window_w, window_h)

        self.init_scene()

    def init_config(self):
        fname = os.path.expanduser(os.path.join('~', '.tatlin'))
        self.config = Config(fname)

    def init_scene(self):
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
        action_open.connect('activate', self.open_file_dialog)
        actiongroup.add_action_with_accel(action_open, '<Control>o')

        action_save = gtk.Action('save', 'Save', 'Save file', gtk.STOCK_SAVE)
        action_save.connect('activate', self.save_file)
        actiongroup.add_action_with_accel(action_save, '<Control>s')

        save_as = gtk.Action('save-as', 'Save As...', 'Save As...', gtk.STOCK_SAVE_AS)
        save_as.connect('activate', self.save_file_as)
        actiongroup.add_action_with_accel(save_as, '<Control><Shift>s')

        action_quit = gtk.Action('quit', 'Quit', 'Quit', gtk.STOCK_QUIT)
        action_quit.connect('activate', self.quit)
        actiongroup.add_action_with_accel(action_quit, '<Control>q')

        accelgroup = gtk.AccelGroup()
        for action in actiongroup.list_actions():
            action.set_accel_group(accelgroup)

        self.window.add_accel_group(accelgroup)

        return actiongroup

    def create_menu_items(self, actiongroup):
        file_menu = gtk.Menu()
        file_menu.append(actiongroup.menu_item('open'))

        save_item = actiongroup.menu_item('save')
        file_menu.append(save_item)

        save_as_item = actiongroup.menu_item('save-as')
        file_menu.append(save_as_item)

        file_menu.append(actiongroup.menu_item('quit'))

        item_file = actiongroup.menu_item('file')
        item_file.set_submenu(file_menu)

        self.menu_items_file = [save_item, save_as_item]
        self.menu_items = [item_file]

    def menu_enable_file_items(self, enable=True):
        for menu_item in self.menu_items_file:
            menu_item.set_sensitive(enable)

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

    def command_line(self):
        if len(sys.argv) > 1:
            self.open_and_display_file(sys.argv[1])

    def save_file(self, action=None):
        """
        Save changes to the same file.
        """
        self.scene.export_to_file(self.model_file)
        self.window.file_modified = False

    def save_file_as(self, action=None):
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

    def open_file_dialog(self, action=None):
        if self.save_changes_dialog():
            dialog = OpenDialog(self.current_dir)
            show_again = True

            while show_again:
                if dialog.run() == gtk.RESPONSE_ACCEPT:
                    dialog.hide()
                    fname = dialog.get_filename()
                    show_again = not self.open_and_display_file(fname)
                else:
                    show_again = False

            dialog.destroy()

    def quit(self, action=None):
        """
        On quit, show a dialog proposing to save the changes if the scene has
        been modified.
        """
        if self.save_changes_dialog():
            gtk.main_quit()

    def save_changes_dialog(self):
        proceed = True
        if self.scene and self.scene.model_modified:
            dialog = QuitDialog(self.window)
            ask_again = True

            while ask_again:
                response = dialog.run()
                if response == QuitDialog.RESPONSE_SAVE:
                    self.save_file()
                    ask_again = False
                elif response == QuitDialog.RESPONSE_SAVE_AS:
                    self.save_file_as()
                    ask_again = self.scene.model_modified
                elif response in [QuitDialog.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
                    ask_again = False
                    proceed = False
                elif response == QuitDialog.RESPONSE_DISCARD:
                    ask_again = False

            dialog.destroy()

        return proceed

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

    def on_set_ortho(self, widget):
        self.scene.mode_ortho = widget.get_active()
        self.scene.invalidate()

    def on_view_front(self, widget):
        self.scene.rotate_view(0, 0)

    def on_view_back(self, widget):
        self.scene.rotate_view(180, 0)

    def on_view_left(self, widget):
        self.scene.rotate_view(90, 0)

    def on_view_right(self, widget):
        self.scene.rotate_view(-90, 0)

    def on_view_top(self, widget):
        self.scene.rotate_view(0, -90)

    def on_view_bottom(self, widget):
        self.scene.rotate_view(0, 90)

    # -------------------------------------------------------------------------
    # FILE OPERATIONS
    # -------------------------------------------------------------------------

    def open_and_display_file(self, fpath):
        progress_dialog = ProgressDialog('Loading', self.window)
        self.window.set_cursor(gtk.gdk.WATCH)
        success = True

        try:
            self.model_file = ModelFile(fpath)

            if self.scene is None:
                self.scene = Scene()
                self.glarea = SceneArea(self.scene)

            progress_dialog.set_text('Reading file...')
            progress_dialog.show()
            model, model_data = self.model_file.read(progress_dialog.step)

            progress_dialog.set_text('Loading model...')
            model.load_data(model_data, progress_dialog.step)

            self.scene.clear()
            self.scene.add_model(model)

            # platform needs to be added last to be translucent
            platform_w = self.config.read('machine.platform_w', int)
            platform_d = self.config.read('machine.platform_d', int)
            platform = Platform(platform_w, platform_d)
            self.scene.add_supporting_actor(platform)

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
            self.menu_enable_file_items(self.model_file.filetype != 'gcode')
        except IOError, e:
            self.window.window.set_cursor(None)
            progress_dialog.hide()
            error_dialog = OpenErrorAlert(self.window, fpath, e.strerror)
            error_dialog.run()
            error_dialog.destroy()
            success = False
        except ModelFileError, e:
            self.window.window.set_cursor(None)
            progress_dialog.hide()
            error_dialog = OpenErrorAlert(self.window, fpath, e.message)
            error_dialog.run()
            error_dialog.destroy()
            success = False
        finally:
            progress_dialog.destroy()
            self.window.window.set_cursor(None)

        return success

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
    app.show_window()
    app.command_line()
    gtk.main()

