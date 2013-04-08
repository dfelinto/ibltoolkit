# TODO LIST
# - fix rectangle drawing code
# - set sun
# - Draw feedback (axes, reprojected square)

import bpy
from mathutils import Vector, Matrix, Euler
from math import (sin, cos, pi, acos, asin, atan2, radians, degrees, sqrt)

# ###############################
#  Property Update Routines
# ###############################

def update_reference(self, context):
    """"""
    movieclip = context.edit_movieclip
    settings = movieclip.ibl_settings

    if settings.reference == 'OBJECT':
        update_camera(self, context)

def update_width(self, context):
    """
    update height and camera according
    to width, and update draw
    """
    movieclip = context.edit_movieclip
    settings = movieclip.ibl_settings

    # hack to avoid recursiveness
    if settings.updating:
        settings.updating -= 1
        return

    v0 = sphere_to_3d(settings.vertex_0, settings.orientation, settings.camera_height)
    v1 = sphere_to_3d(settings.vertex_1, settings.orientation, settings.camera_height)

    distance = (v0-v1).length
    factor = settings.plane_width / distance

    settings.camera_height *= factor

def update_height(self, context):
    """
    update width and camera according
    to height, and update draw
    """
    movieclip = context.edit_movieclip
    settings = movieclip.ibl_settings

    # hack to avoid recursiveness
    if settings.updating:
        settings.updating -= 1
        return

    v1 = sphere_to_3d(settings.vertex_1, settings.orientation, settings.camera_height)
    v2 = sphere_to_3d(settings.vertex_2, settings.orientation, settings.camera_height)

    distance = (v1-v2).length
    factor = settings.plane_height / distance

    settings.camera_height *= factor

def update_camera(self, context):
    """
    update width and height according
    to camera height, and update draw
    """
    movieclip = context.edit_movieclip
    settings = movieclip.ibl_settings

    # hack to avoid recursiveness
    if settings.updating:
        settings.updating -= 1
        return
    else:
        settings.updating = 2

    v0 = sphere_to_3d(settings.vertex_0, settings.orientation, settings.camera_height)
    v1 = sphere_to_3d(settings.vertex_1, settings.orientation, settings.camera_height)
    v2 = sphere_to_3d(settings.vertex_2, settings.orientation, settings.camera_height)

    settings.plane_width = (v0-v1).length
    settings.plane_height = (v1-v2).length

    draw_3d_update(self, context)

def update_orientation(self, context):
    """
    update background and scale based on
    new calibration data
    """
    scene = context.scene
    movieclip = context.edit_movieclip
    settings = movieclip.ibl_settings

    if settings.use_auto_background:
        bpy.ops.clip.background_ibl()

    if settings.reference == 'CAMERA':
        update_camera(self, context)
    else:
        update_width(self, context)

def draw_3d_update(self, context):
    """update calibration object drawing (floor) + camera and light height"""
    scene = context.scene
    movieclip = context.edit_movieclip
    settings = movieclip.ibl_settings

    scene.camera.location = (0, 0, settings.camera_height)

    if scene.render.engine == 'LUXRENDER_RENDER':
        object=bpy.data.objects.get("IBL Light")
        if object: object.location = (0, 0, settings.camera_height)

    bpy.ops.clip.draw_ibl_markers()

# ###############################
#  Geometry Functions
# ###############################

def equirectangular_to_sphere(uv):
    """
    convert a 2d point to 3d
    uv : 0,0 (bottom left) 1,1 (top right)
    uv : +pi, -pi/2 (bottom left) -pi, +pi/2 (top right)
    """
    u,v = uv

    phi = (0.5 - u) * 2 * pi
    theta = (v - 0.5) * pi
    r = cos(theta)

    x = cos(phi) * r
    y = sin(phi) * r
    z = sin(theta)

    return Vector((x,y,z))

def sphere_to_equirectangular(vert):
    """
    convert a 3d point to uv
    """
    theta = asin(vert.z)
    phi = atan2(vert.y, vert.x)

    u = -0.5 * (phi / pi -1)
    v = 0.5 * (2 * theta / pi + 1)

    return u, v

def sphere_to_euler(vecx, vecy, vecz):
    """
    convert sphere orientation vectors to euler
    """
    M = Matrix((vecx, vecy, vecz))
    return M.to_euler()

def sphere_to_3d(vert, euler, radius):
    """
    given a point in the sphere and the euler inclination of the pole
    calculatest he projected point in the plane
    """
    M = euler.to_matrix()
    vert = M * vert
    vert *= radius

    origin = Vector((0,0,radius))
    vert +=  origin
    vector = vert - origin

#    t = (0 - origin[2]) / vector[2]
    t = - radius / (vert[2] - radius)

    floor = origin + t * vector
    return floor

def _3d_to_sphere(vert, euler, radius):
    """
    given a point in the sphere and the euler inclination of the pole
    calculatest he projected point in the plane
    """
    origin = Vector((0,0,radius))
    vert -= origin
    vert /= radius

    M = Euler(euler).to_matrix().inverted()
    vert = M * vert

    return vert

def intersect_lines(p0, v0, p1, v1):
    """
    returns the intersection between 2 vectors if they are not parallel
    """
    if  (p1 - p0).cross(v1).cross(v0.cross(v1)).length > 0.00000000000000001:
        return None

    if (p1 - p0).cross(v1).dot(v0.cross(v1)) > 0:
        t = (p1 - p0).cross(v1).length / (v0.cross(v1)).length
    else:
        t = - ((p1 - p0).cross(v1).length) / (v0.cross(v1)).length

    center = p0 + v0 * t

    return center

def distance_point_line(p0, p1, p2):
    """
    p0 = point
    p1, p2 = line
    """
    distance = ((p2-p1).cross(p1-p0)).length / (p2- p1).length
    return distance

# ###############################
#  Not Working Routines ;)
# ###############################

def convex_hull(verts):
    """XXX"""
    return(range(len(verts)))
    assert(len(verts) > 2)

    sort_verts = sorted(verts, key=lambda vert: vert.x)
    ids = [verts.index(sort_verts[0]), verts.index(sort_verts[1])]

    for i in range(1, len(verts) -1):
        id = 0
        angle = 10000

        v1 = verts[ids[-2]].xy - verts[ids[-1]].xy

        for j in range(len(verts)):
            if j in ids: continue

            new_angle = v1.angle(( verts[ids[-1]].xy - verts[j].xy ))
            if new_angle < angle:
                angle = new_angle
                id = j

        ids.append(id)

    return ids

# ###############################
#  Utility Functions
# ###############################
def selected_tracks(movieclip):
    """returns all the visible selected tracks of the active tracking object"""
    if not movieclip: return []

    tracking = movieclip.tracking.objects[movieclip.tracking.active_object_index]
    selected_tracks = []
    for track in tracking.tracks:
        if track.select and not track.hide:
            selected_tracks.append(track)

    return selected_tracks

def get_image(imagepath, fake_user=True):
    """get blender image for a given path, or load one"""
    image = None

    for img in bpy.data.images:
      if img.filepath == imagepath:
        image=img
        break

    if not image:
      image=bpy.data.images.load(imagepath)
      image.use_fake_user = fake_user

    return image

# ###############################
#  Reconstruction Operators
# ###############################

class CLIP_OT_draw_polygon(bpy.types.Operator):
    """"""
    bl_idname = "clip.draw_polygon"
    bl_label = "Draw IBL Polygon"
    bl_description = "Draw polygon with selected markers"
    bl_options = {'REGISTER', 'UNDO'}

    _selected_tracks = []

    @classmethod
    def poll(cls, context):
        if not context.space_data.clip and context.edit_movieclip: return False
        cls._selected_tracks = selected_tracks(context.edit_movieclip)
        return len(cls._selected_tracks) > 2

    def execute(self, context):

        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # convert panorama points to sphere points
        # sphere points to 3d points
        verts = []
        for track in self._selected_tracks:
            vert2d = equirectangular_to_sphere(track.markers[0].co)
            verts.append(sphere_to_3d(vert2d, settings.orientation, settings.camera_height))

        # draw 3d mesh
        faces = [range(len(verts))]

        # draw 3d mesh
        mesh= bpy.data.meshes.new('IBL Polygon')

        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.validate()
        mesh.calc_normals()

        object = bpy.data.objects.new("IBL Polygon", mesh)
        scene.objects.link(object)

        return {'FINISHED'}

class CLIP_OT_draw_square(bpy.types.Operator):
    """"""
    bl_idname = "clip.draw_square"
    bl_label = "Draw IBL Square"
    bl_description = "Draw square with selected corners"
    bl_options = {'REGISTER', 'UNDO'}

    _selected_tracks = []

    @classmethod
    def poll(cls, context):
        if not context.space_data.clip and context.edit_movieclip: return False
        cls._selected_tracks = selected_tracks(context.edit_movieclip)
        return len(cls._selected_tracks) == 2

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # convert panorama points to sphere points to 3d points
        verts = []
        for track in self._selected_tracks:
            vert2d = equirectangular_to_sphere(track.markers[0].co)
            verts.append(sphere_to_3d(vert2d, settings.orientation, settings.camera_height))

        diagonal = verts[1] - verts[0]

        center = verts[0] + diagonal / 2
        angle = diagonal.angle(Vector((1.0,1.0,0.0)))
        scale = diagonal.length / sqrt(2)

        verts = [(0.5, 0.5, 0.0), (-0.5, 0.5, 0.0), (-0.5, -0.5, 0.0), (0.5, -0.5, 0.0)]

        faces = []
        for i in range(int(len(verts) / 4)):
            offset = i * 4
            faces.append(range(offset,offset + 4))

        # draw 3d mesh
        mesh= bpy.data.meshes.new('IBL Square')

        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.validate()
        mesh.calc_normals()

        object = bpy.data.objects.new("IBL Square", mesh)
        object.scale = scale,scale,scale
        object.location = center
        object.rotation_euler[2] = angle

        scene.objects.link(object)

        return {'FINISHED'}

class CLIP_OT_draw_circle(bpy.types.Operator):
    """"""
    bl_idname = "clip.draw_circle"
    bl_label = "Draw IBL Circle"
    bl_description = "Draw circle with selected 3 vertices"
    bl_options = {'REGISTER', 'UNDO'}

    _selected_tracks = []

    @classmethod
    def poll(cls, context):
        if not context.space_data.clip and context.edit_movieclip: return False
        cls._selected_tracks = selected_tracks(context.edit_movieclip)
        return len(cls._selected_tracks) == 3

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # convert panorama points to sphere points to 3d points
        verts = []
        for track in self._selected_tracks:
            vert2d = equirectangular_to_sphere(track.markers[0].co)
            verts.append(sphere_to_3d(vert2d, settings.orientation, settings.camera_height))

        # mediatrice = rotation of 90 degs of vertex
        p0  = (verts[0] + verts[1]) / 2
        v0 = Vector(( \
                            (verts[0].y - verts[1].y), \
                            (verts[1].x - verts[0].x), \
                            0.0)).normalized()

        # mediatrice = rotation of 90 degs of vertex
        p1  = (verts[1] + verts[2]) / 2
        v1 = Vector(( \
                            (verts[1].y - verts[2].y), \
                            (verts[2].x - verts[1].x), \
                            0.0)).normalized()

        center = intersect_lines(p0, v0, p1, v1)
        if not center:
            return {'CANCELLED'}

        scale = (verts[0] - center).length

        verts = (1,0,0, 0,1,0,-1,0,0, 0,-1,0)

        # draw 3d curve
        curve = bpy.data.curves.new("IBL Circle", 'CURVE')
        spline = curve.splines.new(type = 'BEZIER')
        spline.bezier_points.add(len(verts)/3 -1)
        spline.bezier_points.foreach_set('co', verts)
        spline.use_endpoint_u = True
        spline.use_cyclic_u = True

        for point in spline.bezier_points:
            point.handle_left_type = 'AUTO'
            point.handle_right_type = 'AUTO'

        object = bpy.data.objects.new("IBL Circle", curve)
        object.scale = scale,scale,1.0
        object.location = center

        scene.objects.link(object)

        return {'FINISHED'}

class CLIP_OT_draw_rectangle(bpy.types.Operator):
    """
    Get the base and the height of the rectangle to draw.
    """
    bl_idname = "clip.draw_rectangle"
    bl_label = "Draw IBL Rectangle"
    bl_description = "Draw rectangle with 2 selected corners and a 3rd point for the height"
    bl_options = {'REGISTER', 'UNDO'}

    _selected_tracks = []

    @classmethod
    def poll(cls, context):
        if not context.space_data.clip and context.edit_movieclip: return False
        cls._selected_tracks = selected_tracks(context.edit_movieclip)
        return len(cls._selected_tracks) == 3

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # convert panorama points to sphere points to 3d points
        verts = []
        for track in self._selected_tracks:
            vert2d = equirectangular_to_sphere(track.markers[0].co)
            verts.append(sphere_to_3d(vert2d, settings.orientation, settings.camera_height))

        side = verts[1] - verts[0]
        width = side.length
        height = distance_point_line(verts[2], verts[0], verts[1])

        # mediatrix = rotation of 90 degs of vertex
        p0  = (verts[0] + verts[1]) / 2
        v0 = Vector(( \
                            (verts[0].y - verts[1].y), \
                            (verts[1].x - verts[0].x), \
                            0.0)).normalized()

        center = p0 + v0 * height/2
#        angle = pi * 0.5 + (pi * 0.5 - side.angle(Vector((1.0,0.0,0.0))))
        angle = side.angle(Vector((1.0,0.0,0.0)))

        scale = (width, height, 1)
        verts = [(0.5, 0.5, 0.0), (-0.5, 0.5, 0.0), (-0.5, -0.5, 0.0), (0.5, -0.5, 0.0)]

        faces = [range(len(verts))]

        # draw 3d mesh
        mesh= bpy.data.meshes.new('IBL Rectangle')

        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.validate()
        mesh.calc_normals()

        object = bpy.data.objects.new("IBL Rectangle", mesh)
        object.location = center
        object.rotation_euler[2] = angle
        object.scale = scale

        scene.objects.link(object)

        return {'FINISHED'}

# ###############################
#  Calibration Operators
# ###############################

def context_clip(context):
    if context.space_data.type != 'CLIP_EDITOR':
        return False

    if not context.space_data.clip or not context.edit_movieclip:
        return False

    return True

class CLIP_OT_calibrate_ibl(bpy.types.Operator):
    """calculate theta and phi and draw the poles and horizon"""
    bl_idname = "clip.calibrate_ibl"
    bl_label = "Calibrate HDR Environment Image"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    _selected_tracks = []

    @classmethod
    def poll(cls, context):
        if not context_clip(context): return False

        movieclip = context.edit_movieclip
        tracking = movieclip.tracking.objects [movieclip.tracking.active_object_index]

        cls._selected_tracks = []
        for track in tracking.tracks:
            if track.select:
                cls._selected_tracks.append(track)

        return len(cls._selected_tracks) == 4

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # convert panorama points to sphere points
        verts = []
        for track in self._selected_tracks:
            verts.append(equirectangular_to_sphere(track.markers[0].co))

        # calculate the poles
        vec0 = verts[0].cross(verts[1])
        vec0.normalize()
        vec1 = verts[3].cross(verts[2])
        vec1.normalize()
        vec2 = verts[0].cross(verts[3])
        vec2.normalize()
        vec3 = verts[1].cross(verts[2])
        vec3.normalize()
        vecx = vec0.cross(vec1)
        vecx.normalize()
        vecy = vec3.cross(vec2)
        vecy.normalize()
        vecz = vecx.cross(vecy)
        vecz.normalize()

        nvecy = vecz.cross(vecx)
        nvecy.normalize()

        # store orientation
        settings.orientation = sphere_to_euler(vecx, nvecy, vecz)

        # store points to reuse later without the need to keep them selected
        settings.vertex_0= verts[0]
        settings.vertex_1= verts[1]
        settings.vertex_2= verts[2]
        settings.vertex_3= verts[3]

        update_orientation(self, context)

        return {'FINISHED'}


class CLIP_OT_draw_ibl_markers(bpy.types.Operator):
    """"""
    bl_idname = "clip.draw_ibl_markers"
    bl_label = ""
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.edit_movieclip

    def execute(self, context):

        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # convert panorama points to sphere points
        verts = []
        for vertex in (settings.vertex_0, settings.vertex_1, settings.vertex_2, settings.vertex_3):
            verts.append(sphere_to_3d(vertex, settings.orientation, settings.camera_height))

        # make hull
        pass

        # draw 3d mesh
        edges = [(len(verts)-1, 0)]
        for i in range(len(verts) -1 ):
            edges.append((i,i+1))

        mesh= bpy.data.meshes.new('IBL Floor')

        mesh.from_pydata(verts, [], [range(len(verts))])
        mesh.update()
        mesh.validate()
        mesh.calc_normals()

        object = bpy.data.objects.get("IBL Floor")
        if not object:
            object = bpy.data.objects.new("IBL Floor", mesh)
            scene.objects.link(object)
        else:
            object.data = mesh


        return {'FINISHED'}

class CLIP_OT_background_ibl(bpy.types.Operator):
    """creates a node in cycles with the orientation gathered from the calibration system"""
    bl_idname = "clip.background_ibl"
    bl_label = "Set HDR Image as World Background"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context_clip(context): return False
        return context.scene.render.engine in ('CYCLES', 'LUXRENDER_RENDER')

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        settings.use_auto_background = True

        imagepath = settings.hdr_file
        if imagepath == '': imagepath = movieclip.filepath

        image = get_image(imagepath)

        # value to be used globally (e.g. edit operator)
        scene.orientation = settings.orientation
        scene.ibl_image = get_image(movieclip.filepath).name

        if scene.render.engine == 'CYCLES':
            if not scene.world:
                scene.world= bpy.data.worlds.new(name='IBL')

            world = scene.world
            world.use_nodes=True
            world.cycles.sample_as_light = True
            nodetree = world.node_tree

            tex_env=nodetree.nodes.get("IBL Environment Texture")
            if not tex_env:
                tex_env=nodetree.nodes.new('TEX_ENVIRONMENT')
                tex_env.name = "IBL Environment Texture"
                tex_env.location = (-200, 280)
            tex_env.image = image

            orientation = (-settings.orientation[0], -settings.orientation[1], -settings.orientation[2])
            tex_env.texture_mapping.rotation = orientation

            # Linking
            background = nodetree.nodes.get("Background")
            nodetree.links.new(tex_env.outputs[0], background.inputs[0])

        elif scene.render.engine == 'LUXRENDER_RENDER':
            # In Luxrender the lighting comes from an Hemi Lamp object
            lamp=bpy.data.lamps.get("IBL")
            if not lamp: lamp = bpy.data.lamps.new(name="IBL", type='HEMI')
            lamp.luxrender_lamp.luxrender_lamp_hemi.infinite_map = imagepath
        
            try:
                lamp.luxrender_lamp.AR_enabled = True
                lamp.luxrender_lamp.luxrender_lamp_hemi.type = 'environment'
                lamp.luxrender_lamp.luxrender_lamp_hemi.contribution_map = settings.factor_file
            except: # lux,  not arlux
                pass

            object=bpy.data.objects.get("IBL Light")
            if not object:
                object=bpy.data.objects.new(name="IBL Light", object_data=lamp)
                scene.objects.link(object)

            # Blender to LuxRender orientation convertion
            object.data=lamp
            orientation = settings.orientation
            object.rotation_euler = orientation[0] + pi, orientation[1], orientation[2]
            object.scale = ( 1,-1,-1)
            object.location = (0, 0, settings.camera_height)

        else:
            assert(False)


        return {'FINISHED'}

# ###############################
#  Interface
# ###############################
class IBLPanel:
    @classmethod
    def poll(cls, context):
        sc = context.space_data
        clip = sc.clip

        return clip and sc.view == 'CLIP'

class IBLCalibrationPanel(IBLPanel, bpy.types.Panel):
    ''''''
    bl_label = "IBL Calibration"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings
        scene = context.scene

        col = layout.column()
        subcol = col.column(align=True)
        subcol.operator("clip.calibrate_ibl", text="Calibrate IBL Orientation")
        row=subcol.row()
        row.prop(settings, "orientation", text="")

        col.separator()
        col.prop(settings, "use_auto_background")
        sub=col.column()
        sub.active= not settings.use_auto_background
        sub.operator("clip.background_ibl", text="Set IBL as Background")

        row = col.row(align=True)
        row.prop(settings, "hdr_file", text="")

        if scene.render.engine == 'LUXRENDER_RENDER':
            row.prop(settings, "factor_file", text="")

        col.separator()
        col.prop(settings, "reference", text="Reference")
        row=col.row(align=True)
        if settings.reference == 'CAMERA':
            row.label(icon='CAMERA_DATA')
            row.prop(settings, "camera_height", text="Height")
        else:
            row.label(icon='OBJECT_DATA')
            row.prop(settings, "plane_width", text="Width")
            row.prop(settings, "plane_height", text="Height")


class IBLReconstructionPanel(IBLPanel, bpy.types.Panel):
    ''''''
    bl_label = "IBL Reconstruction"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout

        layout.operator("clip.draw_polygon", text="Draw Polygon", icon='OUTLINER_DATA_LATTICE')
        layout.operator("clip.draw_square", text="Draw Square", icon='MOD_BEVEL')
        layout.operator("clip.draw_circle", text="Draw Circle", icon='CURVE_NCIRCLE')
        layout.operator("clip.draw_rectangle", text="Draw Rectangle", icon='MOD_ARRAY')

#    draw_x = BoolProperty(name="Axis X", description="", update=draw_update)
#    draw_y = BoolProperty(name="Axis Y", description="", update=draw_update)
#    draw_z = BoolProperty(name="Axis Z", description="", update=draw_update)


class IBLRenderPanel(IBLPanel, bpy.types.Panel):
    ''''''
    bl_label = "IBL Render"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        col = layout.column()
        col.operator("clip.background_ibl", text="Render Depth MapSet IBL as Background")
        col.prop(settings, "hdr_file", text="")
        col.separator()

# ###############################
#  Main / Register / Unregister
# ###############################

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == '__main__':
    register()

# ###############################
#  Not Using Code
# ###############################

"""

        # 2) Draw the estimate correction
        poles= movieclip.tracking.objects.get("Poles")
        if poles: movieclip.tracking.objects.remove(poles)
        poles = movieclip.tracking.objects.new(name="Poles")

        # Poles:
        for vec in vecy, nvecy, vecz, -vecz, vecx:
            u,v = sphere_to_equirectangular(vec)
            bpy.ops.clip.add_marker(location=(u, v))

        for i in range(360):
#            if i %20 != 0 : continue
            angle = radians(i)

            if settings.draw_z:
                vert = Matrix.Rotation(angle, 3, vecz) * vecx
                u,v = sphere_to_equirectangular(vert)
                bpy.ops.clip.add_marker(location=(u, v))

            if settings.draw_x:
                vert = Matrix.Rotation(angle, 3, vecx) * vecz
                u,v = sphere_to_equirectangular(vert)
                bpy.ops.clip.add_marker(location=(u, v))

            if settings.draw_y:
                vert = Matrix.Rotation(angle, 3, vecy) * vecz
                u,v = sphere_to_equirectangular(vert)
                bpy.ops.clip.add_marker(location=(u, v))

        return {'FINISHED'}
"""
"""
class CLIP_OT_draw_sphere_rectangle(bpy.types.Operator):
    """"""
    bl_idname = "clip.draw_square_rectangle"
    bl_label = "Draw Rectangle Projection"
    bl_description = "Draw rectangle projection in the panorama"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.edit_movieclip.tracking.tracks) > 3

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # convert panorama points to sphere points
        verts = []
        for track in movieclip.tracking.tracks:
            verts.append(equirectangular_to_sphere(track.markers[0].co))

        draw_line(verts[0], verts[1])
        draw_line(verts[1], verts[2])
        draw_line(verts[2], verts[3])
        draw_line(verts[3], verts[0])

        return {'FINISHED'}
"""
"""
        col.separator()
        row=col.row()
        subcol=row.column(0.8)
        subcol.label(text="Drawing Axes:")
        subcol=row.column()
        row=subcol.row()
        row.prop(settings, "draw_x", text="X")
        row.prop(settings, "draw_y", text="Y")
        row.prop(settings, "draw_z", text="Z")
"""
"""
# ###############################
#  Drawing Routines
# ###############################

def draw_line (v0, v1, points=10, angle=None, vec=None):
    if not vec: vec = v0.cross(v1).normalized()
    if not angle: angle = acos(v1.dot(v0))

    for i in range(points + 1):
        rot = angle * i / points
        vert = Matrix.Rotation(rot, 3, vec) * v0
        u,v = sphere_to_equirectangular(vert)
        bpy.ops.clip.add_marker(location=(u, v))
"""
"""
#        verts[1] = verts[0] + Matrix.Rotation( pi * 0.25, 3, 'Z') * (verts[2] - verts[0]) * 1 / sqrt(2.)
#        verts[3] = verts[0] + Matrix.Rotation(-pi * 0.25, 3, 'Z') * (verts[2] - verts[0]) * 1 / sqrt(2.)

"""
"""
        edges = [(len(verts)-1, 0)]
        for i in range(len(verts) -1 ):
            edges.append((i,i+1))
"""
"""
class CLIP_OT_draw_rectangles(bpy.types.Operator):
    """"""
    bl_idname = "clip.draw_rectangles"
    bl_label = "Draw Convex Hull of selected verts in the 3d view"
    bl_description = "Draw rectangles with selected vertices"
    bl_options = {'REGISTER', 'UNDO'}

    _selected_tracks = []

    @classmethod
    def poll(cls, context):
        cls._selected_tracks = selected_tracks(context.edit_movieclip)
        return len(cls._selected_tracks) > 3 and len(cls._selected_tracks) % 4 == 0

    def execute(self, context):

        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # convert panorama points to sphere points
        verts = []
        for track in self._selected_tracks:
            vert2d = equirectangular_to_sphere(track.markers[0].co)
            verts.append(sphere_to_3d(vert2d, settings.orientation, settings.camera_height))

        faces = []
        for i in range(int(len(verts) / 4)):
            offset = i * 4
#            faces.append(convex_hull((verts[offset:offset + 4])))
            faces.append(range(offset,offset + 4))

        # draw 3d mesh
        mesh= bpy.data.meshes.new('IBL Rectangles')

        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.validate()
        mesh.calc_normals()

        object = bpy.data.objects.new("IBL Rectangles", mesh)
        scene.objects.link(object)

        return {'FINISHED'}
"""
