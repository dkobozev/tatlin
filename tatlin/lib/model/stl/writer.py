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


class STLModelWriter(object):
    def __init__(self, path, filetype):
        self.path = path
        self.filetype = filetype

    def write(self, model: StlModel):
        assert self.filetype == "stl"

        vertices, normals = model.vertices, model.normals

        f = open(self.path, "w")
        print("solid", file=f)
        print(
            "".join(
                [
                    self._format_facet(vertices[i : i + 3], normals[i])
                    for i in range(0, len(vertices), 3)
                ]
            ),
            file=f,
        )
        print("endsolid", file=f)
        f.close()

        model.modified = False

    def _format_facet(self, vertices, normal):
        template = """facet normal %.6f %.6f %.6f
  outer loop
    %s
  endloop
endfacet
"""
        stl_facet = template % (
            normal[0],
            normal[1],
            normal[2],
            "\n".join(["vertex %.6f %.6f %.6f" % (v[0], v[1], v[2]) for v in vertices]),
        )
        return stl_facet
