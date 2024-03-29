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


import sys
import os
import os.path
import logging
from typing import Any

from tatlin.conf.rendering import configure_backend

configure_backend()

import wx

# prevent blurriness on MSW, see: https://bugs.python.org/msg317775
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)  # type: ignore
except:
    pass

from tatlin.lib.model import ModelFileError, ModelLoader
from tatlin.lib.model.stl.writer import STLModelWriter

from tatlin.lib.gl.platform import Platform
from tatlin.lib.gl.scene import Scene

from tatlin.lib.ui.app import BaseApp
from tatlin.lib.ui.window import MainWindow
from tatlin.lib.ui.dialogs import (
    OpenDialog,
    SaveDialog,
    QuitDialog,
    AboutDialog,
    ProgressDialog,
    OpenErrorAlert,
)

from tatlin.lib.util import format_status, get_recent_files, resolve_path
from tatlin.lib.constants import RECENT_FILE_LIMIT, TATLIN_LICENSE, TATLIN_VERSION
from tatlin.conf.config import Config


class App(BaseApp):

    def __init__(self):
        super(App, self).__init__()

        self.window = MainWindow(self)
        self.icon = wx.Icon(resolve_path("tatlin.png"), wx.BITMAP_TYPE_PNG)
        self.window.set_icon(self.icon)

        # ---------------------------------------------------------------------
        # APP SETUP
        # ---------------------------------------------------------------------

        self.init_config()

        self.recent_files = get_recent_files(self.config)
        self.window.update_recent_files_menu(self.recent_files)

        window_w = self.config.read("ui.window_w", int)
        window_h = self.config.read("ui.window_h", int)
        self.window.set_size((window_w, window_h))
        self.init_scene()

    def init_config(self):
        fname = os.path.expanduser(os.path.join("~", ".tatlin"))
        self.config = Config(fname)

    def init_scene(self):
        self.panel: Any = None
        self.scene: Any = None
        self.model_loader: Any = None

    def show_window(self):
        self.window.show_all()

    @property
    def current_dir(self):
        """
        Return path where a file should be saved to.
        """
        if self.model_loader is not None:
            dur = self.model_loader.dirname
        elif len(self.recent_files) > 0:
            dur = os.path.dirname(self.recent_files[0][1])
        else:
            dur = os.getcwd()
        return dur

    def command_line(self):
        if len(sys.argv) > 1:
            self.open_and_display_file(os.path.abspath(sys.argv[1]))

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
                    show_again = not self.open_and_display_file(
                        fpath, dialog.get_type()
                    )
                else:
                    show_again = False

    def on_file_save(self, event=None):
        """
        Save changes to the same file.
        """
        writer = STLModelWriter(self.model_loader.path, self.model_loader.filetype)
        writer.write(self.scene.model)
        self.window.file_modified = False

    def on_file_save_as(self, event=None):
        """
        Save changes to a new file.
        """
        dialog = SaveDialog(self.window, self.current_dir)
        fpath = dialog.get_path()
        if fpath:
            self.model_loader = ModelLoader(fpath)

            writer = STLModelWriter(fpath, self.model_loader.filetype)
            writer.write(self.scene.model)

            self.window.filename = self.model_loader.basename
            self.window.file_modified = False

    def on_quit(self, event=None):
        """
        On quit, write config settings and show a dialog proposing to save the
        changes if the scene has been modified.
        """
        try:
            self.config.write(
                "ui.recent_files",
                os.path.pathsep.join(
                    [
                        f[1] + str(OpenDialog.ftypes.index(f[2]))
                        for f in self.recent_files
                    ]
                ),
            )
            w, h = self.window.get_size()
            self.config.write("ui.window_w", w)
            self.config.write("ui.window_h", h)
            if self.scene:
                self.config.write("ui.gcode_2d", int(self.scene.mode_2d))
            self.config.commit()
        except IOError:
            logging.warning(
                "Could not write settings to config file %s" % self.config.fname
            )

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
                    logging.warning("Unknown dialog response: %s" % response)
                    ask_again = False
                    proceed = False
        return proceed

    def on_about(self, event=None):
        AboutDialog(TATLIN_VERSION, self.icon, TATLIN_LICENSE)

    # -------------------------------------------------------------------------
    # FILE OPERATIONS
    # -------------------------------------------------------------------------

    def update_recent_files(self, fpath, ftype=None):
        self.recent_files = [f for f in self.recent_files if f[1] != fpath]
        self.recent_files.insert(0, (os.path.basename(fpath), fpath, ftype))
        self.recent_files = self.recent_files[:RECENT_FILE_LIMIT]
        self.window.update_recent_files_menu(self.recent_files)

    def open_and_display_file(self, fpath, ftype=None):
        self.set_wait_cursor()
        progress_dialog = ProgressDialog()
        success = True

        try:
            self.update_recent_files(fpath, ftype)
            self.scene = Scene(self.window)
            self.scene.clear()

            self.model_loader = ModelLoader(fpath)

            model, Panel = self.model_loader.load(
                self.config, self.scene, progress_dialog
            )

            # platform needs to be added last to be translucent
            platform_w = self.config.read("machine.platform_w", float)
            platform_d = self.config.read("machine.platform_d", float)
            platform = Platform(platform_w, platform_d)
            self.scene.add_supporting_actor(platform)

            # update panel to reflect new model properties
            self.panel = Panel(self.window, self.scene)
            self.panel.set_initial_values(
                getattr(model, "max_layers", 0),
                getattr(model, "max_layers", 0),
                model.width,
                model.height,
                model.depth,
            )
            self.panel.connect_handlers()

            if hasattr(self.panel, "set_3d_view"):
                self.panel.set_3d_view(not self.scene.mode_2d)  # type:ignore

            # always start with the same view on the scene
            self.scene.reset_view(True)

            self.window.set_file_widgets(self.scene, self.panel)
            self.window.filename = self.model_loader.basename
            self.window.file_modified = False
            self.window.menu_enable_file_items(self.model_loader.filetype != "gcode")

            self.window.update_status(
                format_status(
                    self.model_loader.basename,
                    self.model_loader.size,
                    model.vertex_count,
                )
            )
        except (IOError, ModelFileError) as e:
            self.set_normal_cursor()
            error_dialog = OpenErrorAlert(fpath, e)
            error_dialog.show()
            success = False
        finally:
            progress_dialog.destroy()
            self.set_normal_cursor()
        return success


def run():
    logging.basicConfig(
        format="--- [%(levelname)s] %(message)s",
        level=logging.DEBUG,
        # From the docs: "This function does nothing if the root logger already
        # has handlers configured, unless the keyword argument force is set to
        # True." This has the unfortunate side effect that if any of the
        # dependencies configure the logger first, we lose control over logging.
        # @see https://docs.python.org/3/howto/logging.html
        force=True,
    )

    app = App()
    app.show_window()
    app.command_line()
    app.run()


if __name__ == "__main__":
    run()
