import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper

from mathutils import Euler, Vector
from math import pi

from .calibrate import get_image, _3d_to_sphere, sphere_to_equirectangular

class PanoramaCamera(bpy.types.Operator):
    """"""
    bl_idname = "camera.panorama"
    bl_label = "Panorama Camera"
    bl_description = "Create/adjust a panorama camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context_clip(context)

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        # 1) creates a new camera if no camera is selected
        if context.object and context.object.type == 'CAMERA' and context.object.name == 'IBL Camera':
            camera = context.object
        else:
            camera = bpy.data.objects.new('IBL Camera', bpy.data.cameras.new('IBL Camera'))
            scene.objects.link(camera)

        render_engine  = scene.render.engine
        if render_engine  == 'CYCLES':
            camera.data.type = 'PANO'
            camera.data.cycles.panorama_type = 'EQUIRECTANGULAR'
        elif render_engine == 'LUXRENDER_RENDER':
            camera.data.type = 'PANO'
        elif render_engine == 'BLENDER_GAME':
            scene.game_settings.stereo = 'DOME'
            scene.game_settings.dome_mode = 'PANORAM_SPH'
            scene.game_settings.dome_tesselation = 6
        else:
            self.report({'WARNING'}, "The engine {} doesn't support panorama rendering.\n"\
            "You need to set the render mode manually".format(render_engine ))

        camera.location[2] = settings.camera_height
        camera.rotation_euler = (settings.orientation.to_matrix() * Euler((pi*0.5, 0, -pi*0.5)).to_matrix()).to_euler()
        scene.camera = camera

        return {'FINISHED'}


class OBJECT_OT_project_environment_uv(bpy.types.Operator):
    """"""
    bl_idname = "object.project_environment_uv"
    bl_label = "Project Environment UV"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        object = context.active_object
        return object and \
                    object.type == 'MESH' and \
                    object.mode != 'EDIT' and \
                    context_clip(context)

    def execute(self, context):
        import bmesh

        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        object = context.active_object
        mesh = object.data
   
        uv = mesh.uv_textures.active
        if not uv:  uv = mesh.uv_textures.new()

        # get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(mesh)

        uv_layer = bm.loops.layers.uv.active

        for face in bm.faces:
            for loop in face.loops:
                uv_loop = loop[uv_layer]
                vert = object.matrix_world * Vector(loop.vert.co[:])
                orientation =  settings.orientation
                uv_loop.uv = sphere_to_equirectangular( \
                    _3d_to_sphere(vert, \
                    orientation, settings.camera_height).normalized())

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(mesh)

        return {'FINISHED'}
        

class OBJECT_OT_save_position(bpy.types.Operator):
    """"""
    bl_idname = "object.save_position"
    bl_label = "Save Panorama Position"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        object = context.active_object
        return object and \
                    object.type == 'MESH' and \
                    object.mode != 'EDIT' and \
                    context_clip(context)

    def execute(self, context):
        import bmesh

        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        object = context.active_object
        mesh = object.data
   
        # get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(mesh)

        x=bm.loops.layers.float.new('X')
        y=bm.loops.layers.float.new('Y')
        z=bm.loops.layers.float.new('Z')
        
        for face in bm.faces:
            for loop in face.loops:
                vert = object.matrix_world * Vector(loop.vert.co[:])
                loop[x] = vert.x
                loop[y] = vert.y
                loop[z] = vert.z

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(mesh)

        return {'FINISHED'}

class OBJECT_OT_reset_position(bpy.types.Operator):
    """"""
    bl_idname = "object.reset_position"
    bl_label = "Reset Panorama Position"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        object = context.active_object
        return object and \
                    object.type == 'MESH' and \
                    object.mode != 'EDIT' and \
                    context_clip(context)

    def execute(self, context):
        import bmesh

        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        object = context.active_object
        mesh = object.data
   
        # get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(mesh)

        for i in ('X', 'Y', 'Z'):
            layer = bm.loops.layers.float.get(i)
            if layer:
                bm.loops.layers.float.remove(layer)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(mesh)

        return {'FINISHED'}

def is_object_visible(ob, scene):
    """"""
    if ob.hide: return False

    for i in range(len(scene.layers)):
        if scene.layers[i] and ob.layers[i]:
            return True

    return False

class RENDER_OT_depth(bpy.types.Operator, ExportHelper):
    """"""
    bl_idname = "render.depth"
    bl_label = "Render Depth"
    bl_description = "Render depth image"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".exr"
    filter_glob = StringProperty(default="*.exr", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context_clip(context)

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings
        
        # getting the image saved from the calibration operator
        imagepath = settings.hdr_file
        if imagepath == '': imagepath = movieclip.filepath
        image = get_image(imagepath, fake_user=False)

        if not image:
            self.report({'ERROR'}, "You need to first set the background from the Movie Clip Editor")
            return {'CANCELLED'}

        light=bpy.data.objects.get("IBL Light")
        if not light:
            self.report({'ERROR'}, "You need to first set the background from the Movie Clip Editor")
            return {'CANCELLED'}

        # 0) option to saveas
        hdr_filepath = bpy.path.abspath(bpy.path.ensure_ext(self.filepath, self.filename_ext))
  
        # 1) create a new scene
        render_scene = bpy.data.scenes.new(name='lux_render')
        render_scene.render.resolution_x = image.size[0]
        render_scene.render.resolution_y = image.size[1]
        render_scene.render.resolution_percentage = 100

        # 2) add all the support objects there
        for ob in bpy.context.scene.objects:
            if ob.type == 'MESH':
                if ob.data.luxrender_mesh.type != 'native' and is_object_visible(ob, scene):
                    render_scene.objects.link(ob)
  
        # 3) create a new camera (equirectangular)
        camera = bpy.data.objects.new('ibl_camera', bpy.data.cameras.new('ibl_camera'))
        camera.data.type = 'PANO'
        camera.location[2] = settings.camera_height
        camera.rotation_euler = (settings.orientation.to_matrix() * Euler((pi*0.5, 0, -pi*0.5)).to_matrix()).to_euler()
        render_scene.objects.link(camera)
        render_scene.camera = camera
  
        # 4) change engine to cycles
        render_scene.render.engine = 'CYCLES'
        camera.data.cycles.panorama_type = 'EQUIRECTANGULAR'

        # 5) set renderlayers - depth
        render_scene.render.layers[0].use_pass_combined = False
        
        # 6) create nodes
        render_scene.use_nodes = True
        nodetree = render_scene.node_tree
        
        zed = nodetree.nodes.get("Render Layers")
        color = nodetree.nodes.new('IMAGE')
        color.image = image

        # Linking - store depth as alpha
        composite = nodetree.nodes.get("Composite")
        nodetree.links.new(color.outputs[0], composite.inputs[0])
        nodetree.links.new(zed.outputs['Z'], composite.inputs[1])

        # 7) render + composite
        render_scene.render.filepath = self.filepath
        render_scene.render.image_settings.file_format = 'OPEN_EXR'
        render_scene.render.image_settings.color_mode = 'RGBA'
        render_scene.render.image_settings.color_depth = '16'
        render_scene.render.image_settings.exr_codec = 'ZIP'
        render_scene.cycles.samples = 1
        render_scene.cycles.max_bounces = 0
        render_scene.cycles.min_bounces = 0

        # 8) render
        context.screen.scene = render_scene
        bpy.ops.render.render()

        render = bpy.data.images['Render Result']
        render.save_render(hdr_filepath, scene=render_scene)

        light.data.luxrender_lamp.luxrender_lamp_hemi.infinite_map = hdr_filepath
        
        # 11) set and reset everything
        settings.hdr_file = hdr_filepath

        context.screen.scene = scene
        bpy.data.scenes.remove(render_scene)

        self.report({'INFO'}, "Image successfully created.\nHDR + Depth Map:{}".format(hdr_filepath))

        return {'FINISHED'}


class RENDER_OT_depth_field(bpy.types.Operator, ExportHelper):
    """"""
    bl_idname = "render.depth_field"
    bl_label = "Render Depth Field"
    bl_description = "Render attenuation map"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".exr"
    filter_glob = StringProperty(default="*.exr", options={'HIDDEN'})
    
    luxbinary = EnumProperty(name="Renderer", items= \
                        [("luxconsole",  'LuxConsole', ""), ("luxrender",  'LuxRender GUI', "")], \
                        default='luxconsole', description="")
    
    influence_haltspp=IntProperty(name="Samples", description="Limit of samples before halting the contribution map render", default=250, min=0, max=4000)

    resolution=IntProperty(name="Resolution", description="Size of the contribution map, make sure no object is missing", default = 50,  min=0, max=100, subtype='PERCENTAGE')

    @classmethod
    def poll(cls, context):
        return context_clip(context)

    def execute(self, context):
        scene = context.scene
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings
        
        # getting the image saved from the calibration operator
        imagepath = settings.hdr_file
        if imagepath == '': imagepath = movieclip.filepath
        image = get_image(imagepath, fake_user=False)

        if not image:
            self.report({'ERROR'}, "You need to first set the background from the Movie Clip Editor")
            return {'CANCELLED'}

        light=bpy.data.objects.get("IBL Light")
        if not light:
            self.report({'ERROR'}, "You need to first set the background from the Movie Clip Editor")
            return {'CANCELLED'}

        if light.data.luxrender_lamp.luxrender_lamp_hemi.infinite_map == '':
            self.report({'ERROR'}, "No HDR+D map set to the light. You need to render the depth first")
            return {'CANCELLED'}

        # 0) option to saveas
        factor_filepath = bpy.path.ensure_ext(self.filepath, self.filename_ext)
  
        # 1) create a new scene
        render_scene = bpy.data.scenes.new(name='lux_render')
        render_scene.render.resolution_x = image.size[0]
        render_scene.render.resolution_y = image.size[1]
        render_scene.render.resolution_percentage = self.resolution

        # 2) add all the support objects there
        for ob in bpy.context.scene.objects:
            if ob.type == 'MESH':
                if ob.data.luxrender_mesh.type != 'native' and is_object_visible(ob, scene):
                    render_scene.objects.link(ob)

        render_scene.objects.link(light)

         # 3) create a new camera (equirectangular)
        camera = bpy.data.objects.new('ibl_camera', bpy.data.cameras.new('ibl_camera'))
        camera.data.type = 'PANO'
        camera.location[2] = settings.camera_height

        camera.rotation_euler = (settings.orientation.to_matrix() * Euler((pi*0.5, 0, -pi*0.5)).to_matrix()).to_euler()
        render_scene.objects.link(camera)
        render_scene.camera = camera
  
        # 4) set lux settings
        #luxrender acts in context, so needs to define context first and foremost
        context.screen.scene = render_scene
        render_scene.render.engine = 'LUXRENDER_RENDER'
        render_scene.luxrender_halt.haltspp = self.influence_haltspp
        render_scene.luxrender_rendermode.rendermode = 'depthfield'
        render_scene.luxrender_engine.binary_name = self.luxbinary

        # 5) render + composite
        render_scene.render.filepath = self.filepath
        render_scene.render.image_settings.file_format = 'OPEN_EXR'
        render_scene.render.image_settings.color_mode = 'RGBA'
        render_scene.render.image_settings.color_depth = '16'
        render_scene.render.image_settings.exr_codec = 'ZIP'

        # 5.b) luxrender equivalent of the above settings
        camera.data.luxrender_camera.type = 'environment'
        camera.data.luxrender_camera.luxrender_film.output_alpha = True
        camera.data.luxrender_camera.luxrender_film.write_exr = True
        camera.data.luxrender_camera.luxrender_film.write_exr_applyimaging= False
        camera.data.luxrender_camera.luxrender_film.write_png = False

        # 6) render
        bpy.ops.render.render()

        render = bpy.data.images['Render Result']
        render.save_render(factor_filepath, scene=render_scene)
        
        # 7) set path to use with light
        factor_filepath = bpy.path.relpath(factor_filepath)
        light.data.luxrender_lamp.luxrender_lamp_hemi.contribution_map = factor_filepath
        settings.factor_file = factor_filepath

        # 8) reset everything
        context.screen.scene = scene
        bpy.data.scenes.remove(render_scene)

        self.report({'INFO'}, "Image successfully created.\nContribution Map: {}".format(factor_filepath))

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

def context_clip(context):
    if context.space_data.type != 'CLIP_EDITOR':
        return False

    if not context.space_data.clip or not context.edit_movieclip:
        return False

    return True

class IBLRenderPanel(IBLPanel, bpy.types.Panel):
    ''''''
    bl_label = "IBL Render"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        movieclip = context.edit_movieclip
        settings = movieclip.ibl_settings

        col = layout.column(align=True)
        col.operator("object.project_environment_uv", text="Project UV", icon="MOD_UVPROJECT")

        if context.scene.render.engine  == 'LUXRENDER_RENDER':
            col = layout.column(align=True)
            col.operator("object.save_position", text="Store Position")
            col.operator("object.reset_position", text="Clear Position")

        col.separator()

        col = layout.column()
        col.operator("camera.panorama", icon="CAMERA_DATA")
        
        if context.scene.render.engine  == 'LUXRENDER_RENDER':
            col.operator("render.depth")
            col.operator("render.depth_field")

# ###############################
#  Main / Register / Unregister
# ###############################

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == '__main__':
    register()
