from __future__ import division

import pygtk
pygtk.require('2.0')
import gtk


class GcodePanel(gtk.VBox):
    supported_types = ['gcode']

    def __init__(self, app):
        gtk.VBox.__init__(self)

        self.app = app

        # --------------------------------------------------------------------
        # DISPLAY
        # --------------------------------------------------------------------

        label_layers = gtk.Label('Layers')
        label_layers.set_alignment(-1, 0) # align text to the left
        self.hscale_layers = gtk.HScale()
        self.hscale_layers.set_range(1, self.app.get_property('layers_range_max'))
        self.hscale_layers.set_value(self.app.get_property('layers_value'))
        self.hscale_layers.set_increments(1, 10)
        self.hscale_layers.set_digits(0)
        self.hscale_layers.set_size_request(200, 35)

        self.check_arrows = gtk.CheckButton('Show arrows')
        self.check_2d = gtk.CheckButton('2D view')
        self.btn_reset_perspective = gtk.Button('Reset perspective')

        table_display = gtk.Table(rows=2, columns=1)
        table_display.set_border_width(5)
        table_display.set_row_spacings(5)
        table_display.attach(label_layers,               0, 1, 0, 1, yoptions=0)
        table_display.attach(self.hscale_layers,         0, 1, 1, 2, yoptions=0)
        table_display.attach(self.check_arrows,          0, 1, 2, 3, yoptions=0)
        table_display.attach(self.check_2d,              0, 1, 3, 4, yoptions=0)
        table_display.attach(self.btn_reset_perspective, 0, 1, 4, 5, yoptions=0)

        frame_display = gtk.Frame('Display')
        frame_display.add(table_display)
        frame_display.set_border_width(5)

        # --------------------------------------------------------------------
        # DIMENSIONS
        # --------------------------------------------------------------------

        label_width = gtk.Label('Width (x):')
        label_width.set_alignment(-1, 0)
        self.label_width_value = gtk.Label('43 mm')

        label_depth = gtk.Label('Depth (y):')
        label_depth.set_alignment(-1, 0)
        self.label_depth_value = gtk.Label('43 mm')

        label_height = gtk.Label('Height (z):')
        label_height.set_alignment(-1, 0)
        self.label_height_value = gtk.Label('43 mm')

        table_dimensions = gtk.Table(rows=3, columns=2)
        table_dimensions.set_border_width(5)
        table_dimensions.set_row_spacings(5)
        table_dimensions.attach(label_width,             0, 1, 0, 1, yoptions=0)
        table_dimensions.attach(self.label_width_value,  1, 2, 0, 1, yoptions=0)
        table_dimensions.attach(label_depth,             0, 1, 1, 2, yoptions=0)
        table_dimensions.attach(self.label_depth_value,  1, 2, 1, 2, yoptions=0)
        table_dimensions.attach(label_height,            0, 1, 2, 3, yoptions=0)
        table_dimensions.attach(self.label_height_value, 1, 2, 2, 3, yoptions=0)

        frame_dimensions = gtk.Frame('Dimensions')
        frame_dimensions.add(table_dimensions)
        frame_dimensions.set_border_width(5)

        self.pack_start(frame_display, False)
        self.pack_start(frame_dimensions, False)

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
