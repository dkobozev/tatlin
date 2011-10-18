from __future__ import division

import pygtk
pygtk.require('2.0')
import gtk


class GcodePanel(gtk.VBox):
    supported_types = ['gcode']

    def __init__(self, app):
        gtk.VBox.__init__(self)

        self.app = app

        label_layers = gtk.Label('Layers')
        self.hscale_layers = gtk.HScale()
        self.hscale_layers.set_range(1, self.app.get_property('layers_range_max'))
        self.hscale_layers.set_value(self.app.get_property('layers_value'))
        self.hscale_layers.set_increments(1, 10)
        self.hscale_layers.set_digits(0)
        self.hscale_layers.set_size_request(200, 35)

        table_layers = gtk.Table(rows=2, columns=1)
        table_layers.set_border_width(5)
        table_layers.set_row_spacings(5)
        table_layers.attach(label_layers,       0, 1, 0, 1, yoptions=0)
        table_layers.attach(self.hscale_layers, 0, 1, 1, 2, yoptions=0)

        frame_layers = gtk.Frame()
        frame_layers.add(table_layers)

        self.pack_start(frame_layers)

        self.connect_handlers()

    def connect_handlers(self):
        self.hscale_layers.connect('value-changed', self.app.on_scale_value_changed)


class StlPanel(gtk.VBox):
    supported_types = ['stl']

    def __init__(self, app):
        gtk.VBox.__init__(self)

        self.app = app

        label_scale = gtk.Label('Factor')
        self.entry_scale = gtk.Entry()
        self.entry_scale.set_text('1.0')
        self.button_scale = gtk.Button('Scale')

        table_dimensions = gtk.Table(rows=1, columns=3)
        table_dimensions.set_border_width(5)
        table_dimensions.set_row_spacings(5)
        table_dimensions.attach(label_scale,       0, 1, 0, 1, yoptions=0)
        table_dimensions.attach(self.entry_scale,  1, 2, 0, 1, yoptions=0)
        table_dimensions.attach(self.button_scale, 2, 3, 0, 1, yoptions=0)

        frame_dimensions = gtk.Frame('Dimensions')
        frame_dimensions.add(table_dimensions)

        self.button_center = gtk.Button('Center model')

        self.pack_start(frame_dimensions)
        self.pack_start(self.button_center)

        self.connect_handlers()

    def connect_handlers(self):
        self.button_scale.connect('clicked', self.app.on_button_scale_clicked)
        self.button_center.connect('clicked', self.app.on_button_center_clicked)
