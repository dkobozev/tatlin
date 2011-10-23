#!/usr/bin/env python2

from __future__ import division

import sys
import os

import pygtk
pygtk.require('2.0')
import gtk
from gtk.gtkgl.apputils import GLArea

from libtatlin.gcodeparser import GcodeParser
from libtatlin.stlparser import StlAsciiParser
from libtatlin.vector3 import Vector3
from libtatlin.actors import Platform, GcodeModel, StlModel
from libtatlin.scene import Scene
from libtatlin.ui import StlPanel, GcodePanel


def format_float(f):
    return "%.2f" % f


class ActionGroup(gtk.ActionGroup):
    def __init__(self, *args, **kwargs):
        gtk.ActionGroup.__init__(self, *args, **kwargs)

    def menu_item(self, action_name):
        item = self.get_action(action_name).create_menu_item()
        return item


class ViewerWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title('viewer')
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        self.actiongroup = self.set_up_actions()
        menu = self.create_menu(self.actiongroup)

        self.hbox_model = gtk.HBox()

        main_vbox = gtk.VBox()
        main_vbox.pack_start(menu, False)
        main_vbox.pack_start(self.hbox_model)

        self.add(main_vbox)

        self.connect('destroy', lambda: gtk.main_quit())
        self.connect('key-press-event', self.on_keypress)

        self.panel = None
        self.scene = None

        # dict of properties that other components can read from the app
        self._app_properties = {
            'layers_range_max': lambda: self.scene.get_property('max_layers'),
            'layers_value':     lambda: self.scene.get_property('max_layers'),
            'width':            self.model_width,
            'depth':            self.model_depth,
            'height':           self.model_height,
        }

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.on_quit()

    def on_scaling_factor_update(self, widget):
        try:
            factor = float(widget.get_text())
            self.model.scale(factor)
            self.model.init()
            self.scene.invalidate()
        except ValueError:
            pass # ignore invalid values

    def on_scale_value_changed(self, widget):
        value = int(widget.get_value())
        self.model.num_layers_to_draw = value
        self.scene.invalidate()

    def on_button_center_clicked(self, widget):
        """
        Center model on platform.
        """
        self.scene.center_model()
        self.scene.invalidate()

    def on_arrows_toggled(self, widget):
        """
        Show/hide arrows on the Gcode model.
        """
        self.scene.show_arrows(widget.get_active())
        self.scene.invalidate()

    def on_reset_perspective(self, widget):
        """
        Restore the view of the model shown on startup.
        """
        self.scene.reset_perspective()
        self.scene.invalidate()

    def open_and_display_file(self, fpath):
        ftype = self.determine_model_type(fpath)

        if ftype == 'gcode':
            model = self.gcode_model(fpath)
            Panel = GcodePanel
        elif ftype == 'stl':
            model = self.stl_model(fpath)
            Panel = StlPanel

        if self.scene is None:
            self.set_up_scene()
        self.add_model_to_scene(model)

        if self.panel is None or ftype not in self.panel.supported_types:
            self.panel = Panel(self)
            self.panel.show_all()

        self.panel.set_initial_values() # update panel to reflect new model properties
        self.panel.connect_handlers()
        self.scene.reset_perspective() # always start with the same view on the scene

        self.display_scene()

    def get_property(self, name):
        """
        Return a property of the application.
        """
        return self._app_properties[name]()

    def model_width(self):
        width = self.scene.get_property('width')
        return format_float(width)

    def model_depth(self):
        depth = self.scene.get_property('depth')
        return format_float(depth)

    def model_height(self):
        height = self.scene.get_property('height')
        return format_float(height)

    def set_up_scene(self):
        self.scene = Scene()
        self.glarea = GLArea(self.scene)

    def display_scene(self):
        # NOTE: Removing glarea from parent widget causes it to free previously
        # allocated resources. There doesn't seem to be anything about it in
        # the docs, should this be self-evident? It does save the trouble of
        # cleaning up, though.
        for child in self.hbox_model.children():
            self.hbox_model.remove(child)

        self.hbox_model.pack_start(self.glarea, expand=True,  fill=True)
        self.hbox_model.pack_start(self.panel,  expand=False, fill=False)

    def add_model_to_scene(self, model):
        self.model = model

        self.scene.clear()
        self.scene.set_model(model)
        self.scene.add_supporting_actor(Platform()) # platform needs to be added last to be translucent

    def determine_model_type(self, fpath):
        fname = os.path.basename(fpath)
        extension = os.path.splitext(fname)[-1].lower()

        if extension not in ['.gcode', '.stl']:
            raise Exception('Unknown file extension: %s' % extension)

        return extension[1:]

    def gcode_model(self, fpath):
        start_location = Vector3(Platform.width / 2, -Platform.depth / 2, 10.0)
        parser = GcodeParser(fpath, start_location)
        model = GcodeModel(parser.parse_layers())
        return model

    def stl_model(self, fpath):
        parser = StlAsciiParser(fpath)
        model = StlModel(parser.parse())
        return model

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

        self.add_accel_group(accelgroup)

        return actiongroup

    def create_menu(self, actiongroup):
        file_menu = gtk.Menu()
        file_menu.append(actiongroup.menu_item('open'))
        file_menu.append(actiongroup.menu_item('save-as'))
        file_menu.append(actiongroup.menu_item('quit'))

        menubar = gtk.MenuBar()
        item_file = actiongroup.menu_item('file')
        item_file.set_submenu(file_menu)
        menubar.append(item_file)

        return menubar

    def on_save_as(self, action):
        dialog = gtk.FileChooserDialog('Save As', None,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
        dialog.set_do_overwrite_confirmation(True)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            from libtatlin.stlparser import StlFile
            stl_file = StlFile(self.model)
            stl_file.write(dialog.get_filename())

        dialog.destroy()

    def on_open(self, action):
        dialog = gtk.FileChooserDialog('Open', None, gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            self.open_and_display_file(dialog.get_filename())

        dialog.destroy()

    def on_quit(self, action=None):
        gtk.main_quit()


if __name__ == '__main__':
    window = ViewerWindow()
    window.open_and_display_file(sys.argv[1])
    window.show_all()
    gtk.main()
