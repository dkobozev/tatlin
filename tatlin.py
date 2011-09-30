#!/usr/bin/env python2

from __future__ import division

import sys

import pygtk
pygtk.require('2.0')
import gtk
from gtk.gtkgl.apputils import GLArea

from libtatlin.gcodeparser import GcodeParser
from libtatlin.vector3 import Vector3
from libtatlin.actors import Platform, GcodeModel
from libtatlin.scene import Scene


class ViewerWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title('viewer')
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        start_location = Vector3(Platform.width / 2, -Platform.depth / 2, 10.0)
        gcode = GcodeParser(sys.argv[1], start_location)

        platform = Platform()
        self.model = GcodeModel(gcode.parse_layers())

        self.scene = Scene()
        self.scene.actors.append(self.model)
        # platform has to be added last to be translucent
        self.scene.actors.append(platform)
        self.glarea = GLArea(self.scene)

        label_layers = gtk.Label('Layers')
        self.scale_layers = gtk.HScale()
        self.scale_layers.set_range(1, self.model.max_layers)
        self.scale_layers.set_value(self.model.max_layers)
        self.scale_layers.set_increments(1, 10)
        self.scale_layers.set_digits(0)
        self.scale_layers.set_size_request(200, 35)
        self.scale_layers.connect('value-changed', self.on_scale_value_changed)

        table_layers = gtk.Table(rows=2, columns=1)
        table_layers.set_border_width(5)
        table_layers.set_row_spacings(5)
        table_layers.attach(label_layers,      0, 1, 0, 1, yoptions=0)
        table_layers.attach(self.scale_layers, 0, 1, 1, 2, yoptions=0)

        frame_layers = gtk.Frame()
        frame_layers.add(table_layers)

        vbox = gtk.VBox()
        vbox.pack_start(frame_layers)

        hbox = gtk.HBox()
        hbox.pack_start(self.glarea, expand=True,  fill=True)
        hbox.pack_start(vbox,        expand=False, fill=False)
        self.add(hbox)

        self.connect('destroy', lambda quit: gtk.main_quit())
        self.connect('key-press-event', self.on_keypress)

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            gtk.main_quit()

    def on_scale_value_changed(self, widget):
        value = int(widget.get_value())
        self.model.num_layers_to_draw = value
        self.scene.invalidate()


if __name__ == '__main__':
    window = ViewerWindow()
    window.show_all()
    gtk.main()
