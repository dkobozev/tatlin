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
        # DIMENSIONS
        # --------------------------------------------------------------------

        label_width = gtk.Label('X:')
        self.label_width_value = gtk.Label('43 mm')

        label_depth = gtk.Label('Y:')
        self.label_depth_value = gtk.Label('43 mm')

        label_height = gtk.Label('Z:')
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

        # --------------------------------------------------------------------
        # DISPLAY
        # --------------------------------------------------------------------

        label_layers = gtk.Label('Layers')
        label_layers.set_alignment(-1, 0) # align text to the left
        self.hscale_layers = gtk.HScale()
        self.hscale_layers.set_increments(1, 10)
        self.hscale_layers.set_digits(0)
        self.hscale_layers.set_size_request(200, 35)

        self.check_arrows = gtk.CheckButton('Show arrows')
        self.check_3d = gtk.CheckButton('3D view')
        self.btn_reset_perspective = gtk.Button('Reset perspective')

        table_display = gtk.Table(rows=2, columns=1)
        table_display.set_border_width(5)
        table_display.set_row_spacings(5)
        table_display.attach(label_layers,               0, 1, 0, 1, yoptions=0)
        table_display.attach(self.hscale_layers,         0, 1, 1, 2, yoptions=0)
        table_display.attach(self.check_arrows,          0, 1, 2, 3, yoptions=0)
        table_display.attach(self.check_3d,              0, 1, 3, 4, yoptions=0)
        table_display.attach(self.btn_reset_perspective, 0, 1, 4, 5, yoptions=0)

        frame_display = gtk.Frame('Display')
        frame_display.add(table_display)
        frame_display.set_border_width(5)

        self.pack_start(frame_dimensions, False)
        self.pack_start(frame_display, False)

    def connect_handlers(self):
        self.hscale_layers.connect('value-changed', self.app.on_scale_value_changed)
        self.check_arrows.connect('toggled', self.app.on_arrows_toggled)
        self.btn_reset_perspective.connect('clicked', self.app.on_reset_perspective)

    def set_initial_values(self):
        self.hscale_layers.set_range(1, self.app.get_property('layers_range_max'))
        self.hscale_layers.set_value(self.app.get_property('layers_value'))

        self.check_arrows.set_active(True) # check the box

        self.check_3d.set_active(True) # check the box


class StlPanel(gtk.VBox):
    supported_types = ['stl']

    def __init__(self, app):
        gtk.VBox.__init__(self)

        self.app = app

        # --------------------------------------------------------------------
        # DIMENSIONS
        # --------------------------------------------------------------------

        label_x = gtk.Label('X:')
        self.entry_x = gtk.Entry()
        label_x_units = gtk.Label('mm')

        label_y = gtk.Label('Y:')
        self.entry_y = gtk.Entry()
        label_y_units = gtk.Label('mm')

        label_z = gtk.Label('Z:')
        self.entry_z = gtk.Entry()
        label_z_units = gtk.Label('mm')

        label_factor = gtk.Label('Factor:')
        self.entry_factor = gtk.Entry()
        self.entry_factor.set_text('1.0')

        table_dimensions = gtk.Table(rows=4, columns=3)
        table_dimensions.set_border_width(5)
        table_dimensions.set_row_spacings(5)

        table_dimensions.attach(label_x,       0, 1, 0, 1, yoptions=0)
        table_dimensions.attach(self.entry_x,  1, 2, 0, 1, yoptions=0)
        table_dimensions.attach(label_x_units, 2, 3, 0, 1, yoptions=0)

        table_dimensions.attach(label_y,       0, 1, 1, 2, yoptions=0)
        table_dimensions.attach(self.entry_y,  1, 2, 1, 2, yoptions=0)
        table_dimensions.attach(label_y_units, 2, 3, 1, 2, yoptions=0)

        table_dimensions.attach(label_z,       0, 1, 2, 3, yoptions=0)
        table_dimensions.attach(self.entry_z,  1, 2, 2, 3, yoptions=0)
        table_dimensions.attach(label_z_units, 2, 3, 2, 3, yoptions=0)

        table_dimensions.attach(label_factor,      0, 1, 3, 4, yoptions=0)
        table_dimensions.attach(self.entry_factor, 1, 2, 3, 4, yoptions=0)

        frame_dimensions = gtk.Frame('Dimensions')
        frame_dimensions.set_border_width(5)
        frame_dimensions.add(table_dimensions)

        # --------------------------------------------------------------------
        # MOVE
        # --------------------------------------------------------------------

        self.button_center = gtk.Button('Center model')

        frame_move = gtk.Frame('Move')
        frame_move.set_border_width(5)
        frame_move.add(self.button_center)

        # --------------------------------------------------------------------
        # ROTATE
        # --------------------------------------------------------------------

        self.btn_x_90 = gtk.Button('+90')
        label_rotate_x = gtk.Label('X:')
        self.entry_rotate_x = gtk.Entry()

        self.btn_y_90 = gtk.Button('+90')
        label_rotate_y = gtk.Label('Y:')
        self.entry_rotate_y = gtk.Entry()

        self.btn_z_90 = gtk.Button('+90')
        label_rotate_z = gtk.Label('Z:')
        self.entry_rotate_z = gtk.Entry()

        table_rotate = gtk.Table(rows=3, columns=3)
        table_rotate.set_border_width(5)
        table_rotate.set_row_spacings(5)

        table_rotate.attach(self.btn_x_90,       0, 1, 0, 1, yoptions=0)
        table_rotate.attach(label_rotate_x,      1, 2, 0, 1, yoptions=0)
        table_rotate.attach(self.entry_rotate_x, 2, 3, 0, 1, yoptions=0)

        table_rotate.attach(self.btn_y_90,       0, 1, 1, 2, yoptions=0)
        table_rotate.attach(label_rotate_y,      1, 2, 1, 2, yoptions=0)
        table_rotate.attach(self.entry_rotate_y, 2, 3, 1, 2, yoptions=0)

        table_rotate.attach(self.btn_z_90,       0, 1, 2, 3, yoptions=0)
        table_rotate.attach(label_rotate_z,      1, 2, 2, 3, yoptions=0)
        table_rotate.attach(self.entry_rotate_z, 2, 3, 2, 3, yoptions=0)

        frame_rotate = gtk.Frame('Rotate')
        frame_rotate.set_border_width(5)
        frame_rotate.add(table_rotate)

        # --------------------------------------------------------------------
        # DISPLAY
        # --------------------------------------------------------------------

        self.btn_reset_perspective = gtk.Button('Reset perspective')

        frame_display = gtk.Frame('Display')
        frame_display.set_border_width(5)
        frame_display.add(self.btn_reset_perspective)

        self.pack_start(frame_dimensions, False)
        self.pack_start(frame_move, False)
        self.pack_start(frame_rotate, False)
        self.pack_start(frame_display, False)

    def connect_handlers(self):
        self.button_center.connect('clicked', self.app.on_button_center_clicked)
        self.btn_reset_perspective.connect('clicked', self.app.on_reset_perspective)
        self.entry_factor.connect('focus-out-event', self.on_entry_factor_focus_out)

    def on_entry_factor_focus_out(self, widget, event):
        self.app.on_scaling_factor_update(widget)

    def set_initial_values(self):
        self.entry_x.set_text(str(self.app.get_property('width')))
        self.entry_y.set_text(str(self.app.get_property('depth')))
        self.entry_z.set_text(str(self.app.get_property('height')))

