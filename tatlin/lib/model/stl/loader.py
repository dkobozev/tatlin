# -*- coding: utf-8 -*-
# Copyright (C) 2024 Denis Kobozev
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

from tatlin.lib.gl.stlmodel import StlModel
from tatlin.lib.ui.stl import StlPanel

from ..baseloader import BaseModelLoader, ModelFileError
from .parser import StlParseError, StlParser


class STLModelLoader(BaseModelLoader):
    def load(self, config, scene, progress_dlg):
        with open(self.path, "rb") as stlfile:
            parser = StlParser(stlfile)
            parser.load(stlfile)
            try:
                progress_dlg.stage("Reading file...")
                data = parser.parse(progress_dlg.step)

                progress_dlg.stage("Loading model...")
                model = StlModel()
                model.load_data(data, progress_dlg.step)

                scene.add_model(model)
                scene.mode_2d = False

                return model, StlPanel
            except StlParseError as e:
                # rethrow as generic file error
                raise ModelFileError(f"Parsing error: {e}")
