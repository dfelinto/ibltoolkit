#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>
bl_info = {
    "name": "IBL Toolkit",
    "author": "Dalai Felinto and Aldo Zang",
    "version": (1, 0),
    "blender": (2, 6, 3),
    "location": "Movie Clip Editor > Tools Panel",
    "description": "Rock'n'Roll",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render"}

if "bpy" in locals():
    import imp
    imp.reload(calibrate)
    imp.reload(edit)
    imp.reload(render)

else:
    from . import calibrate
    from . import edit
    from . import render

from .calibrate import (
    update_orientation,
    update_reference,
    update_camera,
    update_width,
    update_height,
    _3d_to_sphere,
    )

from mathutils import Vector

import bpy
from bpy.props import (FloatProperty,
            FloatVectorProperty,
            PointerProperty,
            EnumProperty,
            BoolProperty,
            IntProperty,
            StringProperty,
            )

# ###############################
#  Properties Declaration
# ###############################

items=[("CAMERA",  'Camera', "Specify the camera height"), ("OBJECT",  'Object', "Specify the dimensions of the selected object")]

class IBLSettings(bpy.types.PropertyGroup):
    orientation= FloatVectorProperty(name="Orientation", description="Euler rotation", subtype='EULER', default=(0.0,0.0,0.0), update=update_orientation)
    reference = EnumProperty(name="Method", items=items, default='CAMERA', description="", update=update_reference)
    camera_height = FloatProperty(name="Camera Height", description="", default=1.0, min=0.01, max=50.0, update=update_camera)
    plane_width = FloatProperty(name="Width", description="", default=1.0, min=0.01, max=100.0, update=update_width)
    plane_height= FloatProperty(name="Height", description="", default=1.0, min=0.01, max=100.0, update=update_height)
    use_auto_background=BoolProperty(name="Background Live Update", description="")

    hdr_file=StringProperty(name="HDR File", description="Use another HDR file instead. For Luxrender you can store the depth in the alpha channel", subtype='FILE_PATH')
    factor_file=StringProperty(name="Use a Depth Factor File", description="Depth influence map - HDR factor, calculated with/for Luxrender", subtype='FILE_PATH')

    updating=IntProperty(name="Updating Flag", description="Hack flag to avoid recursiveness", default=0, min=0, max=2)

    vertex_0 = FloatVectorProperty(name="Vertex 0", subtype='XYZ', default=_3d_to_sphere( Vector((1.0, 1.0, 0.0)), (0,0,0), 1.0))
    vertex_1 = FloatVectorProperty(name="Vertex 1", subtype='XYZ', default=_3d_to_sphere( Vector((2.0, 1.0, 0.0)), (0,0,0), 1.0))
    vertex_2 = FloatVectorProperty(name="Vertex 2", subtype='XYZ', default=_3d_to_sphere( Vector((2.0, 2.0, 0.0)), (0,0,0), 1.0))
    vertex_3 = FloatVectorProperty(name="Vertex 3", subtype='XYZ', default=_3d_to_sphere( Vector((1.0, 2.0, 0.0)), (0,0,0), 1.0))


def register():
    bpy.utils.register_module(__name__)

    bpy.types.MovieClip.ibl_settings = PointerProperty(
            type=IBLSettings, name="IBL Settings", description="")

    bpy.types.Scene.orientation = FloatVectorProperty(subtype='EULER')
    bpy.types.Scene.ibl_image= StringProperty()

def unregister():
    bpy.utils.unregister_module(__name__)

    del bpy.types.MovieClip.ibl_settings
    del bpy.types.Scene.orientation
    del bpy.types.Scene.ibl_image

if __name__ == '__main__':
    register()
