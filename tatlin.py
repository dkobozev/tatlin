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

from libtatlin.actors import Platform
from libtatlin.scene import Scene
from libtatlin.ui import load_icon, BaseApp, MainWindow, StlPanel, GcodePanel, \
        OpenDialog, OpenErrorAlert, ProgressDialog, SaveDialog, QuitDialog, AboutDialog
from libtatlin.storage import ModelFile, ModelFileError
from libtatlin.config import Config


def format_float(f):
    return "%.2f" % f


class App(BaseApp):

    TATLIN_VERSION = '0.2.3'
    TATLIN_LICENSE = """This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
    RECENT_FILE_LIMIT = 10

    def __init__(self):
        super(App, self).__init__()

        # ---------------------------------------------------------------------
        # WINDOW SETUP
        # ---------------------------------------------------------------------
        self.window = MainWindow()

        self.icon = load_icon('tatlin-logo.png')
        self.window.set_icon(self.icon)

        # ---------------------------------------------------------------------
        # APP SETUP
        # ---------------------------------------------------------------------

        self.init_config()

        recent_files = self.config.read('ui.recent_files')
        if recent_files:
            self.recent_files = [(os.path.basename(f), f) for f in recent_files.split(os.path.pathsep)
                                 if os.path.exists(f)][:self.RECENT_FILE_LIMIT]
        else:
            self.recent_files = []
        self.window.update_recent_files_menu(self.recent_files)

        window_w = self.config.read('ui.window_w', int)
        window_h = self.config.read('ui.window_h', int)
        self.window.set_size((window_w, window_h))

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
        elif len(self.recent_files) > 0:
            dur = os.path.dirname(self.recent_files[0][1])
        else:
            dur = os.getcwd()

        return dur

    def command_line(self):
        if len(sys.argv) > 1:
            self.open_and_display_file(sys.argv[1])

    # -------------------------------------------------------------------------
    # EVENT HANDLERS
    # -------------------------------------------------------------------------

    def on_file_open(self, event=None):
        if self.save_changes_dialog():
            show_again = True

            while show_again:
                dialog = OpenDialog(self.window, self.current_dir)
                fpath = dialog.get_path()
                if fpath:
                    show_again = not self.open_and_display_file(fpath)
                else:
                    show_again = False

    def on_file_save(self, event=None):
        """
        Save changes to the same file.
        """
        self.scene.export_to_file(self.model_file)
        self.window.file_modified = False

    def on_file_save_as(self, event=None):
        """
        Save changes to a new file.
        """
        dialog = SaveDialog(self.window, self.current_dir)
        fpath = dialog.get_path()
        if fpath:
            stl_file = ModelFile(fpath)
            self.scene.export_to_file(stl_file)
            self.model_file = stl_file
            self.window.filename = stl_file.basename
            self.window.file_modified = False

    def on_quit(self, event=None):
        """
        On quit, write config settings and show a dialog proposing to save the
        changes if the scene has been modified.
        """
        try:
            self.config.write('ui.recent_files', os.path.pathsep.join([f[1] for f in self.recent_files]))

            w, h = self.window.get_size()
            self.config.write('ui.window_w', w)
            self.config.write('ui.window_h', h)

            if self.scene:
                self.config.write('ui.gcode_2d', int(self.scene.mode_2d))

            self.config.commit()
        except IOError:
            logging.warning('Could not write settings to config file %s' % self.config.fname)

        if self.save_changes_dialog():
            self.window.quit()

    def save_changes_dialog(self):
        proceed = True
        if self.scene and self.scene.model_modified:
            ask_again = True

            while ask_again:
                dialog = QuitDialog(self.window)
                response = dialog.show()
                if response == QuitDialog.RESPONSE_SAVE:
                    self.on_file_save()
                    ask_again = False
                elif response == QuitDialog.RESPONSE_SAVE_AS:
                    self.on_file_save_as()
                    ask_again = self.scene.model_modified
                elif response == QuitDialog.RESPONSE_CANCEL:
                    ask_again = False
                    proceed = False
                elif response == QuitDialog.RESPONSE_DISCARD:
                    ask_again = False
                else:
                    raise Exception('Unknown dialog response: %s' % response)

        return proceed

    def on_about(self, event=None):
        AboutDialog()

    def scaling_factor_changed(self, factor):
        try:
            self.scene.scale_model(float(factor))
            self.scene.invalidate()
            # tell all the widgets that care about model size that it has changed
            self.panel.model_size_changed()
            self.window.file_modified = self.scene.model_modified
        except ValueError:
            pass # ignore invalid values

    def dimension_changed(self, dimension, value):
        try:
            self.scene.change_model_dimension(dimension, float(value))
            self.scene.invalidate()
            self.panel.model_size_changed()
            self.window.file_modified = self.scene.model_modified
        except ValueError:
            pass # ignore invalid values

    def on_layers_changed(self, layers):
        self.scene.change_num_layers(layers)
        self.scene.invalidate()

    def rotation_changed(self, axis, angle):
        try:
            self.scene.rotate_model(float(angle), axis)
            self.scene.invalidate()
            self.window.file_modified = self.scene.model_modified
        except ValueError:
            pass # ignore invalid values

    def on_center_model(self):
        """
        Center model on platform.
        """
        self.scene.center_model()
        self.scene.invalidate()
        self.window.file_modified = self.scene.model_modified

    def on_arrows_toggled(self, value):
        """
        Show/hide arrows on the Gcode model.
        """
        self.scene.show_arrows(value)
        self.scene.invalidate()

    def on_reset_view(self):
        """
        Restore the view of the model shown on startup.
        """
        self.scene.reset_view()
        self.scene.invalidate()

    def on_set_mode(self, value):
        self.scene.mode_2d = not value
        if self.scene.initialized:
            self.scene.invalidate()

    def on_set_ortho(self, value):
        self.scene.mode_ortho = value
        self.scene.invalidate()

    def on_view_front(self):
        self.scene.rotate_view(0, 0)

    def on_view_back(self):
        self.scene.rotate_view(180, 0)

    def on_view_left(self):
        self.scene.rotate_view(90, 0)

    def on_view_right(self):
        self.scene.rotate_view(-90, 0)

    def on_view_top(self):
        self.scene.rotate_view(0, -90)

    def on_view_bottom(self):
        self.scene.rotate_view(0, 90)

    # -------------------------------------------------------------------------
    # FILE OPERATIONS
    # -------------------------------------------------------------------------

    def update_recent_files(self, fpath):
        self.recent_files = [f for f in self.recent_files if f[1] != fpath]
        self.recent_files.insert(0, (os.path.basename(fpath), fpath))
        self.recent_files = self.recent_files[:self.RECENT_FILE_LIMIT]
        self.window.update_recent_files_menu(self.recent_files)

    def open_and_display_file(self, fpath):
        self.set_wait_cursor()
        progress_dialog = None
        success = True

        try:
            self.update_recent_files(fpath)
            self.model_file = ModelFile(fpath)

            self.scene = Scene(self.window)

            progress_dialog = ProgressDialog('Reading file...')
            model, model_data = self.model_file.read(progress_dialog.step)
            progress_dialog.destroy()

            progress_dialog = ProgressDialog('Loading model...')
            model.load_data(model_data, progress_dialog.step)

            self.scene.clear()
            model.offset_x = self.config.read('machine.platform_offset_x', int)
            model.offset_y = self.config.read('machine.platform_offset_y', int)
            model.offset_z = self.config.read('machine.platform_offset_z', int)
            self.scene.add_model(model)

            # platform needs to be added last to be translucent
            platform_w = self.config.read('machine.platform_w', int)
            platform_d = self.config.read('machine.platform_d', int)
            platform = Platform(platform_w, platform_d)
            self.scene.add_supporting_actor(platform)

            self.panel = self.create_panel()
            # update panel to reflect new model properties
            self.panel.set_initial_values()
            self.panel.connect_handlers()

            # always start with the same view on the scene
            self.scene.reset_view(True)
            if self.model_file.filetype == 'gcode':
                self.scene.mode_2d = bool(self.config.read('ui.gcode_2d', int))
            else:
                self.scene.mode_2d = False

            if hasattr(self.panel, 'set_3d_view'):
                self.panel.set_3d_view(not self.scene.mode_2d)

            self.window.set_file_widgets(self.scene, self.panel)
            self.window.filename = self.model_file.basename
            self.window.file_modified = False
            self.window.menu_enable_file_items(self.model_file.filetype != 'gcode')

            if self.model_file.size > 2**30:
                size = self.model_file.size / 2**30
                units = 'GB'
            elif self.model_file.size > 2**20:
                size = self.model_file.size / 2**20
                units = 'MB'
            elif self.model_file.size > 2**10:
                size = self.model_file.size / 2**10
                units = 'KB'
            else:
                size = self.model_file.size
                units = 'B'

            vertex_plural = 'vertex' if int(str(model.vertex_count)[-1]) == 1 else 'vertices'
            self.window.update_status(' %s (%.1f%s, %d %s)' % (
                self.model_file.basename, size, units, model.vertex_count, vertex_plural))
        except IOError, e:
            self.set_normal_cursor()
            error_dialog = OpenErrorAlert(fpath, e.strerror)
            error_dialog.show()
            success = False
        except ModelFileError, e:
            self.set_normal_cursor()
            error_dialog = OpenErrorAlert(fpath, e.message)
            error_dialog.show()
            success = False
        finally:
            if progress_dialog:
                progress_dialog.destroy()
            self.set_normal_cursor()

        return success

    def create_panel(self):
        if self.model_file.filetype == 'gcode':
            Panel = GcodePanel
        elif self.model_file.filetype == 'stl':
            Panel = StlPanel
        return Panel(self.window)

    def panel_matches_file(self):
        matches = (self.model_file.filetype in self.panel.supported_types)
        return matches


if __name__ == '__main__':
    # configure logging
    logging.basicConfig(format='--- [%(levelname)s] %(message)s', level=logging.DEBUG)

    app = App()
    app.show_window()
    app.command_line()
    app.run()

