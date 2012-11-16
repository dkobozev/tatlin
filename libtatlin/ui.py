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

import pygtk
pygtk.require('2.0')
import gtk
import gobject


class ViewButtons(gtk.Table):
    def __init__(self, app):
        super(ViewButtons, self).__init__()

        self.app = app

        self.btn_front = gtk.Button('Front')
        self.btn_back  = gtk.Button('Back')
        self.btn_left  = gtk.Button('Left')
        self.btn_right = gtk.Button('Right')

        self.btn_top    = gtk.Button('Top')
        self.btn_bottom = gtk.Button('Bottom')

        vbox = gtk.VBox()
        vbox.pack_start(self.btn_top,    False)
        vbox.pack_start(self.btn_bottom, False)

        self.set_border_width(5)
        self.set_row_spacings(5)
        self.attach(self.btn_front,  1, 2, 2, 3, yoptions=0)
        self.attach(self.btn_back,   1, 2, 0, 1, yoptions=0)
        self.attach(self.btn_left,   0, 1, 1, 2)
        self.attach(self.btn_right,  2, 3, 1, 2)
        self.attach(vbox,            1, 2, 1, 2, yoptions=0)

        # connect handlers
        self.btn_front.connect( 'clicked', self.app.on_view_front)
        self.btn_back.connect(  'clicked', self.app.on_view_back)
        self.btn_left.connect(  'clicked', self.app.on_view_left)
        self.btn_right.connect( 'clicked', self.app.on_view_right)
        self.btn_top.connect(   'clicked', self.app.on_view_top)
        self.btn_bottom.connect('clicked', self.app.on_view_bottom)


class GcodePanel(gtk.VBox):
    supported_types = ['gcode']

    def __init__(self, app):
        gtk.VBox.__init__(self)

        self.app = app
        self._handlers_connected = False

        # --------------------------------------------------------------------
        # DIMENSIONS
        # --------------------------------------------------------------------

        label_width = gtk.Label('X:')
        self.label_width_value = gtk.Label()

        label_depth = gtk.Label('Y:')
        self.label_depth_value = gtk.Label()

        label_height = gtk.Label('Z:')
        self.label_height_value = gtk.Label()

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

        self.check_arrows   = gtk.CheckButton('Show arrows')
        self.check_3d       = gtk.CheckButton('3D view')
        view_buttons        = ViewButtons(self.app)
        self.check_ortho    = gtk.CheckButton('Orthographic projection')
        self.btn_reset_view = gtk.Button('Reset view')

        table_display = gtk.Table(rows=2, columns=1)
        table_display.set_border_width(5)
        table_display.set_row_spacings(5)
        table_display.attach(label_layers,        0, 1, 0, 1, yoptions=0)
        table_display.attach(self.hscale_layers,  0, 1, 1, 2, yoptions=0)
        table_display.attach(self.check_arrows,   0, 1, 2, 3, yoptions=0)
        table_display.attach(self.check_3d,       0, 1, 3, 4, yoptions=0)
        table_display.attach(view_buttons,        0, 1, 4, 5, yoptions=0)
        table_display.attach(self.check_ortho,    0, 1, 5, 6, yoptions=0)
        table_display.attach(self.btn_reset_view, 0, 1, 6, 7, yoptions=0)

        frame_display = gtk.Frame('Display')
        frame_display.add(table_display)
        frame_display.set_border_width(5)

        self.pack_start(frame_dimensions, False)
        self.pack_start(frame_display, False)

    def connect_handlers(self):
        if self._handlers_connected:
            return

        self.hscale_layers.connect( 'value-changed', self.app.on_scale_value_changed)
        self.check_arrows.connect(  'toggled',       self.app.on_arrows_toggled)
        self.btn_reset_view.connect('clicked',       self.app.on_reset_view)
        self.check_3d.connect(      'toggled',       self.on_set_mode)
        self.check_ortho.connect(   'toggled',       self.app.on_set_ortho)

        self._handlers_connected = True

    def set_initial_values(self):
        self.hscale_layers.set_range(1, self.app.get_property('layers_range_max'))
        self.hscale_layers.set_value(self.app.get_property('layers_value'))

        self.check_arrows.set_active(True) # check the box

        self.check_3d.set_active(True)

        self.label_width_value.set_text(self.app.get_property('width'))
        self.label_depth_value.set_text(self.app.get_property('depth'))
        self.label_height_value.set_text(self.app.get_property('height'))

    def on_set_mode(self, widget):
        """
        Make ortho checkbox insensitive when not in 3D mode.
        """
        self.check_ortho.set_sensitive(widget.get_active())
        self.app.on_set_mode(widget)

    def set_3d_view(self, value):
        self.check_3d.set_active(value)


class StlPanel(gtk.VBox):
    supported_types = ['stl']

    def __init__(self, app):
        gtk.VBox.__init__(self)

        self.app = app
        self._handlers_connected = False

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

        view_buttons = ViewButtons(self.app)

        self.check_ortho    = gtk.CheckButton('Orthographic projection')
        self.btn_reset_view = gtk.Button('Reset view')

        table_display = gtk.Table(rows=2, columns=1)
        table_display.set_border_width(5)
        table_display.set_row_spacings(5)
        table_display.attach(view_buttons,        0, 1, 0, 1, yoptions=0)
        table_display.attach(self.check_ortho,    0, 1, 1, 2, yoptions=0)
        table_display.attach(self.btn_reset_view, 0, 1, 2, 3, yoptions=0)

        frame_display = gtk.Frame('Display')
        frame_display.set_border_width(5)
        frame_display.add(table_display)

        self.pack_start(frame_dimensions, False)
        self.pack_start(frame_move, False)
        self.pack_start(frame_rotate, False)
        self.pack_start(frame_display, False)

    def connect_handlers(self):
        if self._handlers_connected:
            return

        # dimensions
        self.entry_x.connect('focus-out-event', self.on_entry_x_focus_out)
        self.entry_x.connect('key-press-event', self.on_key_press)

        self.entry_y.connect('focus-out-event', self.on_entry_y_focus_out)
        self.entry_y.connect('key-press-event', self.on_key_press)

        self.entry_z.connect('focus-out-event', self.on_entry_z_focus_out)
        self.entry_z.connect('key-press-event', self.on_key_press)

        self.entry_factor.connect('focus-out-event', self.on_entry_factor_focus_out)
        self.entry_factor.connect('key-press-event', self.on_key_press)

        # ---------------------------------------------------------------------
        # ROTATION
        # ---------------------------------------------------------------------

        self.entry_rotate_x.connect('focus-out-event', self.on_abs_angle_changed, 'x')
        self.entry_rotate_x.connect('key-press-event', self.on_key_press)

        self.entry_rotate_y.connect('focus-out-event', self.on_abs_angle_changed, 'y')
        self.entry_rotate_y.connect('key-press-event', self.on_key_press)

        self.entry_rotate_z.connect('focus-out-event', self.on_abs_angle_changed, 'z')
        self.entry_rotate_z.connect('key-press-event', self.on_key_press)

        self.btn_x_90.connect('clicked', self.on_rel_angle_changed, 'x', 90)
        self.btn_y_90.connect('clicked', self.on_rel_angle_changed, 'y', 90)
        self.btn_z_90.connect('clicked', self.on_rel_angle_changed, 'z', 90)

        # ---------------------------------------------------------------------
        # MOVE
        # ---------------------------------------------------------------------

        self.button_center.connect('clicked', self.app.on_button_center_clicked)

        # ---------------------------------------------------------------------
        # DISPLAY
        # ---------------------------------------------------------------------

        self.btn_reset_view.connect('clicked', self.app.on_reset_view)
        self.check_ortho.connect('toggled', self.app.on_set_ortho)

        self._handlers_connected = True

    def on_key_press(self, widget, event):
        """
        Make enter have the same effect as focusing out of an entry.
        """
        if event.keyval == gtk.keysyms.Return:
            widget.emit('focus-out-event', event)
            return True # stop processing the event

    def on_entry_factor_focus_out(self, widget, event):
        self.app.scaling_factor_changed(widget.get_text())

    def on_entry_x_focus_out(self, widget, event):
        width = widget.get_text()
        self.app.dimension_changed('width', width)

    def on_entry_y_focus_out(self, widget, event):
        depth = widget.get_text()
        self.app.dimension_changed('depth', depth)

    def on_entry_z_focus_out(self, widget, event):
        height = widget.get_text()
        self.app.dimension_changed('height', height)

    def on_rel_angle_changed(self, widget, axis, angle):
        current_angle = float(self.app.get_property('rotation-' + axis))
        angle = current_angle + angle
        self.app.rotation_changed(axis, angle)
        self.model_angle_changed()

    def on_abs_angle_changed(self, widget, event, axis):
        self.app.rotation_changed(axis, widget.get_text())
        self.model_angle_changed()

    def set_initial_values(self):
        self._set_size_properties()
        self._set_rotation_properties()

    def _set_size_properties(self):
        self.entry_factor.set_text(self.app.get_property('scaling-factor'))

        self.entry_x.set_text(self.app.get_property('width'))
        self.entry_y.set_text(self.app.get_property('depth'))
        self.entry_z.set_text(self.app.get_property('height'))

    def _set_rotation_properties(self):
        self.entry_rotate_x.set_text(self.app.get_property('rotation-x'))
        self.entry_rotate_y.set_text(self.app.get_property('rotation-y'))
        self.entry_rotate_z.set_text(self.app.get_property('rotation-z'))

    def model_size_changed(self):
        self._set_size_properties()

    def model_angle_changed(self):
        self._set_rotation_properties()


class StartupPanel(gtk.VBox):
    """
    Panel shown on app startup when nothing has been loaded yet.
    """
    __gsignals__ = {
        'open-clicked': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gtk.VBox.__init__(self)

        label = gtk.Label('No files loaded')
        self.btn_open = gtk.Button(stock=gtk.STOCK_OPEN)
        self.btn_open.connect('clicked', self.on_open_clicked)

        container = gtk.VBox()
        container.pack_start(label, False)

        btn_open_align = gtk.Alignment()
        btn_open_align.set(0.5, 0.5, 0.0, 1.0)
        btn_open_align.add(self.btn_open)
        container.pack_start(btn_open_align, False)

        self.pack_start(container, expand=True, fill=False)

    def on_open_clicked(self, widget):
        self.emit('open-clicked')


class MainWindow(gtk.Window):
    __gsignals__ = {
        'open-clicked': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gtk.Window.__init__(self)

        self._app_name = 'Tatlin'
        self._file_modified = False
        self._filename = None
        self._title_changed()

        self.set_position(gtk.WIN_POS_CENTER)
        self.set_default_size(640, 480)

        self.menubar = gtk.MenuBar()

        self.box_scene = gtk.HBox()
        self.panel_startup = StartupPanel()
        self.panel_startup.connect('open-clicked', self.on_startup_open_clicked)

        self.box_main = gtk.VBox()
        self.box_main.pack_start(self.menubar, False)
        self.box_main.pack_start(self.panel_startup)

        self.add(self.box_main)

    def append_menu_item(self, item):
        self.menubar.append(item)

    def set_file_widgets(self, glarea, panel_file):
        # remove startup panel if present
        if self.box_scene.parent is None:
            self.box_main.remove(self.panel_startup)
            self.box_main.pack_start(self.box_scene)

        # NOTE: Removing glarea from parent widget causes it to free previously
        # allocated resources. There doesn't seem to be anything about it in
        # the docs, should this be self-evident? It does save the trouble of
        # cleaning up, though.
        for child in self.box_scene.children():
            self.box_scene.remove(child)

        self.box_scene.pack_start(glarea, expand=True,  fill=True)
        self.box_scene.pack_start(panel_file,  expand=False, fill=False)
        self.box_scene.show_all()

    def on_startup_open_clicked(self, widget):
        self.emit('open-clicked')

    @property
    def file_modified(self):
        return self._file_modified

    @file_modified.setter
    def file_modified(self, value):
        self._file_modified = value
        self._title_changed()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value
        self._title_changed()

    def _title_changed(self):
        """
        Format and set title.
        """
        title = self._app_name
        if self._filename is not None:
            filename = self._filename
            if self._file_modified:
                filename = '*' + filename
            title = filename + ' - ' + title

        self.set_title(title)

    def set_cursor(self, cursor):
        if cursor:
            self.window.set_cursor(gtk.gdk.Cursor(cursor))
        else:
            self.window.set_cursor(cursor)


class SaveDialog(gtk.FileChooserDialog):
    """
    Dialog for saving a file.
    """
    def __init__(self, directory=None):
        gtk.FileChooserDialog.__init__(self, 'Save As', None,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))

        self.set_do_overwrite_confirmation(True)
        if directory is not None:
            self.set_current_folder(directory)


class OpenDialog(gtk.FileChooserDialog):
    """
    Dialog for opening a file.
    """
    def __init__(self, directory=None):
        gtk.FileChooserDialog.__init__(self, 'Open', None,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))

        self.set_keep_above(True)

        if directory is not None:
            self.set_current_folder(directory)


class OpenErrorAlert(gtk.MessageDialog):
    def __init__(self, parent, fpath, error):
        msg = "Error opening file %s: %s" % (fpath, error)
        gtk.MessageDialog.__init__(self, parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)

        self.set_keep_above(True)


class QuitDialog(gtk.Dialog):
    RESPONSE_CANCEL  = gtk.RESPONSE_CANCEL
    RESPONSE_DISCARD = 1
    RESPONSE_SAVE_AS = 2
    RESPONSE_SAVE    = 3

    def __init__(self, parent=None):
        super(QuitDialog, self).__init__(None, parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (
                gtk.STOCK_DISCARD, self.RESPONSE_DISCARD,
                gtk.STOCK_CANCEL,  self.RESPONSE_CANCEL,
                gtk.STOCK_SAVE_AS, self.RESPONSE_SAVE_AS,
                gtk.STOCK_SAVE,    self.RESPONSE_SAVE,
            ))
        label = gtk.Label('Save changes to file before closing?')
        self.vbox.pack_start(label)
        label.show()


class ProgressDialog(gtk.Dialog):
    def __init__(self, title=None, parent=None):
        super(ProgressDialog, self).__init__(title, parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        self.label = gtk.Label()
        self.progressbar = gtk.ProgressBar()
        self.progressbar.set_fraction(0)

        self.vbox.pack_start(self.label)
        self.vbox.pack_start(self.progressbar)
        self.show_all()

    def set_text(self, text):
        self.label.set_text(text)

    def step(self, count, limit):
        self.progressbar.set_fraction(max(0, min(count / limit, 1)))

        while gtk.events_pending():
            gtk.main_iteration()
