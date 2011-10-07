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


class ActionGroup(gtk.ActionGroup):
    def __init__(self, *args, **kwargs):
        gtk.ActionGroup.__init__(self, *args, **kwargs)

    def menu_item(self, action_name):
        item = self.get_action(action_name).create_menu_item()
        return item


class Panel(gtk.VBox):
    supported_types = ['stl', 'gcode']

    def __init__(self, model):
        gtk.VBox.__init__(self)

        label_layers = gtk.Label('Layers')
        self.scale_layers = gtk.HScale()
        self.scale_layers.set_range(1, model.max_layers)
        self.scale_layers.set_value(model.max_layers)
        self.scale_layers.set_increments(1, 10)
        self.scale_layers.set_digits(0)
        self.scale_layers.set_size_request(200, 35)

        table_layers = gtk.Table(rows=2, columns=1)
        table_layers.set_border_width(5)
        table_layers.set_row_spacings(5)
        table_layers.attach(label_layers,      0, 1, 0, 1, yoptions=0)
        table_layers.attach(self.scale_layers, 0, 1, 1, 2, yoptions=0)

        frame_layers = gtk.Frame()
        frame_layers.add(table_layers)

        label_scale = gtk.Label('Factor')
        self.entry_scale = gtk.Entry()
        self.entry_scale.set_text('1.0')
        self.button_scale = gtk.Button('Scale')

        table_dimensions = gtk.Table(rows=1, columns=3)
        table_dimensions.set_border_width(5)
        table_dimensions.set_row_spacings(5)
        table_dimensions.attach(label_scale,      0, 1, 0, 1, yoptions=0)
        table_dimensions.attach(self.entry_scale, 1, 2, 0, 1, yoptions=0)
        table_dimensions.attach(self.button_scale, 2, 3, 0, 1, yoptions=0)

        frame_dimensions = gtk.Frame('Dimensions')
        frame_dimensions.add(table_dimensions)

        self.pack_start(frame_layers)
        self.pack_start(frame_dimensions)


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

        self.connect('destroy', lambda quit: gtk.main_quit())
        self.connect('key-press-event', self.on_keypress)

        self.panel = None
        self.scene = None

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.on_quit()

    def on_scale_value_changed(self, widget):
        value = int(widget.get_value())
        self.model.num_layers_to_draw = value
        self.scene.invalidate()

    def on_button_scale_clicked(self, widget):
        factor = float(self.panel.entry_scale.get_text())
        self.model.scale(factor)
        self.model.init()
        self.scene.invalidate()

    def open_and_display_file(self, fpath):
        ftype = self.determine_model_type(fpath)

        if ftype == 'gcode':
            model = self.gcode_model(fpath)
            #Panel = GcodePanel
        elif ftype == 'stl':
            model = self.stl_model(fpath)
            #Panel = StlPanel

        if self.panel is None or ftype not in self.panel.supported_types:
            self.panel = Panel(model)
            self.panel.scale_layers.connect('value-changed', self.on_scale_value_changed)
            self.panel.button_scale.connect('clicked', self.on_button_scale_clicked)

        if self.scene is None:
            self.init_scene()

        self.display_scene()
        self.add_model_to_scene(model)

    def init_scene(self):
        self.platform = Platform()
        self.scene = Scene()
        self.scene.actors.append(self.platform)
        self.glarea = GLArea(self.scene)

    def display_scene(self):
        for child in self.hbox_model.children():
            self.hbox_model.remove(child)

        self.hbox_model.pack_start(self.glarea, expand=True,  fill=True)
        self.hbox_model.pack_start(self.panel,  expand=False, fill=False)

    def add_model_to_scene(self, model):
        self.model = model
        self.scene.actors = []
        self.scene.actors.append(self.model)
        self.scene.actors.append(self.platform) # platform needs to be added last to be translucent

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
            stl_file = StlFile(self.model.transformed_facets())
            stl_file.write(dialog.get_filename())

        dialog.destroy()

    def on_open(self, action):
        print '+++ open'

    def on_quit(self, action=None):
        gtk.main_quit()


if __name__ == '__main__':
    window = ViewerWindow()
    window.open_and_display_file(sys.argv[1])
    window.show_all()
    gtk.main()
