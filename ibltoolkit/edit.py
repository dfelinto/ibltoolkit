# - get camera  internal offset
# - calculate camera vector

import bpy
from bgl import *
from mathutils import Matrix, Euler

fragment_shader ="""
#version 120
uniform sampler2D color_buffer;
uniform sampler2D depth_buffer;
uniform sampler2D texture_buffer;

uniform mat4 projectionmodelviewinverse;

#define PI  3.14159265

vec3 glUnprojectGL(vec2 coords)
{
    float u = coords.s * 2.0 - 1.0;
    float v = coords.t * 2.0 - 1.0;

    vec4 view = vec4(u, v, 1.0, 1.0);
    vec4 world = projectionmodelviewinverse * vec4(view.x, view.y, -view.z, 1.0);

    return vec3(world[0] * world[3], world[1] *  world[3], world[2] * world[3]);
}

vec2 equirectangular(vec3 vert)
{
    float theta = asin(vert.z);
    float phi = atan(vert.x, vert.y);

    float u = 0.5 * (phi / PI) + 0.25;
    float v = 0.5 + theta/PI;

    return vec2(u,v);
}

void main(void)
{
    vec2 coords = gl_TexCoord[0].st;
    vec4 foreground = texture2D(color_buffer, coords);
    vec3 world = glUnprojectGL(coords);
    vec4 background = texture2D(texture_buffer, equirectangular(normalize(world)));

    float depth = texture2D(depth_buffer, coords).s;

    if (depth > 0.99995){
        foreground = background;
    }

    gl_FragColor = foreground;
}
"""

fragment_shader_wire ="""
#version 120
uniform sampler2D color_buffer;
uniform sampler2D texture_buffer;
uniform mat4 projectionmodelviewinverse;
uniform float alpha;

#define PI  3.14159265

vec3 glUnprojectGL(vec2 coords)
{
    float u = coords.s * 2.0 - 1.0;
    float v = coords.t * 2.0 - 1.0;

    vec4 view = vec4(u, v, 1.0, 1.0);
    vec4 world = projectionmodelviewinverse * vec4(view.x, view.y, -view.z, 1.0);

    return vec3(world[0] * world[3], world[1] *  world[3], world[2] * world[3]);
}

vec2 equirectangular(vec3 vert)
{
    float theta = asin(vert.z);
    float phi = atan(vert.x, vert.y);

    float u = 0.5 * (phi / PI) + 0.25;
    float v = 0.5 + theta/PI;

    return vec2(u,v);
}

void main(void)
{
    vec2 coords = gl_TexCoord[0].st;
    vec4 foreground = texture2D(color_buffer, coords);
    vec3 world = glUnprojectGL(coords);
    vec4 background = texture2D(texture_buffer, equirectangular(normalize(world)));

    gl_FragColor = mix(foreground, background, alpha);
}
"""

# ##################
# GLSL Debug
# ##################

def print_shader_errors(shader):
    """"""
    log = Buffer(GL_BYTE, len(fragment_shader))
    length = Buffer(GL_INT, 1)

    print('Shader Code:')
    glGetShaderSource(shader, len(log), length, log)

    line = 1
    msg = "  1 "

    for i in range(length[0]):
        if chr(log[i-1]) == '\n':
            line += 1
            msg += "%3d %s" %(line, chr(log[i]))
        else:
            msg += chr(log[i])

    print(msg)

    glGetShaderInfoLog(shader, len(log), length, log)
    print("Error in GLSL Shader:\n")
    msg = ""
    for i in range(length[0]):
        msg += chr(log[i])

    print (msg)

def print_program_errors(program):
    """"""
    log = Buffer(GL_BYTE, 1024)
    length = Buffer(GL_INT, 1)

    glGetProgramInfoLog(program, len(log), length, log)

    print("Error in GLSL Program:\n")

    msg = ""
    for i in range(length[0]):
        msg += chr(log[i])

    print (msg)

# ######################
# OpenGL Image Routines
# ######################

def resize(self, context):
    """we can run every frame or only when width/height change"""
    # remove old textures
    self.quit()

    self.width = context.region.width
    self.height = context.region.height

    self.buffer_width, self.buffer_height = calculate_image_size(self.width, self.height)

    # image to dump screen
    self.color_id = create_image(self.buffer_width, self.buffer_height, GL_RGBA)
    self.depth_id = create_image(self.buffer_width, self.buffer_height, GL_DEPTH_COMPONENT32)

def calculate_image_size(width, height):
    """get a power of 2 size"""
    buffer_width, buffer_height = 0,0

    i = 0
    while (1 << i) <= width:i+= 1
    buffer_width = 1 << i

    i = 0
    while (1 << i) <= height:i+= 1
    buffer_height = 1 << i

    return buffer_width, buffer_height

def update_image(tex_id, viewport, target=GL_RGBA, texture=GL_TEXTURE0):
    """copy the current buffer to the image"""
    glActiveTexture(texture)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glCopyTexImage2D(GL_TEXTURE_2D, 0, target, viewport[0], viewport[1], viewport[2], viewport[3], 0)


def create_image(width, height, target=GL_RGBA):
    """create an empty image, dimensions pow2"""
    if target == GL_RGBA:
        target, internal_format, dimension  = GL_RGBA, GL_RGB, 3
    else:
        target, internal_format, dimension = GL_DEPTH_COMPONENT32, GL_DEPTH_COMPONENT, 1

    null_buffer = Buffer(GL_BYTE, [(width + 1) * (height + 1) * dimension])

    id_buf = Buffer(GL_INT, 1)
    glGenTextures(1, id_buf)

    tex_id = id_buf.to_list()[0]
    glBindTexture(GL_TEXTURE_2D, tex_id)

    glTexImage2D(GL_TEXTURE_2D, 0, target, width, height, 0, internal_format, GL_UNSIGNED_BYTE, null_buffer)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    if target == GL_DEPTH_COMPONENT32:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE)

    glCopyTexImage2D(GL_TEXTURE_2D, 0, target, 0, 0, width, height, 0)

    glBindTexture(GL_TEXTURE_2D, 0)

    del null_buffer

    return tex_id

def delete_image(tex_id):
    """clear created image"""
    id_buf = Buffer(GL_INT, 1)
    id_buf.to_list()[0] = tex_id

    if glIsTexture(tex_id):
        glDeleteTextures(1, id_buf)

# ##################
# GLSL Screen Shader
# ##################

def create_shader(source, program=None, type=GL_FRAGMENT_SHADER):
    """"""
    if program == None:
        program = glCreateProgram()

    shader = glCreateShader(type)
    glShaderSource(shader, source)
    glCompileShader(shader)

    success = Buffer(GL_INT, 1)
    glGetShaderiv(shader, GL_COMPILE_STATUS, success)

    if not success[0]:
        print_shader_errors(shader)
    glAttachShader(program, shader)
    glLinkProgram(program)

    return program

def setup_uniforms(program, color_id, depth_id, texture_id, projectionmodelviewinverse, alpha):

    uniform = glGetUniformLocation(program, "color_buffer")
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, color_id)
    if uniform != -1: glUniform1i(uniform, 0)

    uniform = glGetUniformLocation(program, "depth_buffer")
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D, depth_id)
    if uniform != -1: glUniform1i(uniform, 1)

    uniform = glGetUniformLocation(program, "texture_buffer")
    glActiveTexture(GL_TEXTURE2)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    if uniform != -1: glUniform1i(uniform, 2)

    uniform = glGetUniformLocation(program, "projectionmodelviewinverse")
    if uniform != -1: glUniformMatrix4fv(uniform, 1, 0, projectionmodelviewinverse)

    uniform = glGetUniformLocation(program, "alpha")
    if uniform != -1: glUniform1f(uniform, alpha)

def bindcode(image):
    '''load the image in the graphic card if necessary'''
    image.gl_touch(GL_NEAREST)
    return image.bindcode

# ##################
# Drawing Routines
# ##################
def view_setup():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glLoadIdentity()

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glOrtho(-1, 1, -1, 1, -20, 20)
    gluLookAt(0.0, 0.0, 1.0, 0.0,0.0,0.0, 0.0,1.0,0.0)

def view_reset(viewport):
    # Get texture info
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()

    glMatrixMode(GL_TEXTURE)
    glPopMatrix()

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    glViewport(viewport[0], viewport[1], viewport[2], viewport[3])

def draw_rectangle(zed=0.0):
    texco = [(1, 1), (0, 1), (0, 0), (1,0)]
    verco = [(1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), ( 1.0, -1.0)]

    glPolygonMode(GL_FRONT_AND_BACK , GL_FILL)

    glBegin(GL_QUADS)
    for i in range(4):
        glColor4f(1.0, 1.0, 1.0, 0.0)
        glTexCoord3f(texco[i][0], texco[i][1], zed)
        glVertex2f(verco[i][0], verco[i][1])
    glEnd()

def draw_callback_px(self, context):
    """core function"""
    if not self._enabled: return

    act_tex = Buffer(GL_INT, 1)
    glGetIntegerv(GL_ACTIVE_TEXTURE, act_tex)

    glGetIntegerv(GL_VIEWPORT, self.viewport)

    # (1) dump buffer in texture
    update_image(self.color_id, self.viewport, GL_RGBA, GL_TEXTURE0)

    # (2) dump zed buffer in texture
    update_image(self.depth_id, self.viewport, GL_DEPTH_COMPONENT, GL_TEXTURE1)

    # (3) run screenshader
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)

    pjm = Buffer(GL_FLOAT, 16)
    mvm = Buffer(GL_FLOAT, 16)

    cam_pos = context.scene.camera.location.copy()
    glMatrixMode(GL_MODELVIEW)
    glTranslatef(cam_pos[0], cam_pos[1], cam_pos[2])

    glGetFloatv(GL_PROJECTION_MATRIX, pjm)
    glGetFloatv(GL_MODELVIEW_MATRIX, mvm)

    # set identity matrices
    view_setup()

    # calculate matrixes
    projection_matrix = Matrix((pjm[0:4], pjm[4:8], pjm[8:12], pjm[12:16])).transposed()
    modelview_matrix = Matrix((mvm[0:4], mvm[4:8], mvm[8:12], mvm[12:16])).transposed()

    # applied the  calibration matrix
    modelview_matrix =  modelview_matrix * self.orientation

    modelviewprojinv_matrix = (projection_matrix * modelview_matrix).inverted()
    modelviewprojinv_mat = Buffer(GL_FLOAT, (4,4), modelviewprojinv_matrix.transposed())

    glUseProgram(self.program)
    setup_uniforms(self.program, self.color_id, self.depth_id, bindcode(self.image), modelviewprojinv_mat, self.alpha)
    draw_rectangle()

    # (4) restore opengl defaults
    glUseProgram(0)
    glActiveTexture(act_tex[0])
    glBindTexture(GL_TEXTURE_2D, 0)
    view_reset(self.viewport)

    glMatrixMode(GL_MODELVIEW)
    glTranslatef(-cam_pos[0], -cam_pos[1], -cam_pos[2])

class VIEW_IBL_3DViewOperator(bpy.types.Operator):
    """"""
    bl_idname = "wm.ibl_edit_background"
    bl_label = "IBL in 3d View"
    bl_description = "Shows the panorama as background for the 3dview"

    _enabled = True
    _timer = None

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        if event.type == 'TIMER':

            # bug, waiting for fix: "[#31026] context.region broken after QuadView on + off"
            # http://projects.blender.org/tracker/index.php?func=detail&aid=31026&group_id=9&atid=498
            if not context.region or \
                not context.space_data or \
                context.space_data.type != 'VIEW_3D':
                return {'PASS_THROUGH'}

            viewport_shade = context.space_data.viewport_shade
            self._enabled = (viewport_shade != 'RENDERED')

            if viewport_shade in ('WIREFRAME', 'BOUNDBOX'):
                self.program= self.program_wire
            else:
                self.program = self.program_shader

            if (self.width != context.region.width) or (self.height != context.region.height):
                resize(self, context)

        return {'PASS_THROUGH'}

    def execute(self, context):
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(0.1, context.window)
        self._handle = context.region.callback_add(draw_callback_px, (self, context), 'POST_VIEW')

        scene = context.scene
        # getting the image saved from the calibration operator
        image = bpy.data.images.get(scene.ibl_image)

        if not image:
            self.report({'ERROR'}, "You need to first set the background from the Movie Clip Editor")
            return {'CANCELLED'}

        # store the image, gets the bindcode in the drawing routine
        self.image = image

        self.viewport = Buffer(GL_INT, 4)
        self.width = context.region.width
        self.height = context.region.height

        # power of two dimensions
        self.buffer_width, self.buffer_height = calculate_image_size(self.width, self.height)

        # images to dump the screen buffers
        self.color_id = create_image(self.buffer_width, self.buffer_height, GL_RGBA)
        self.depth_id = create_image(self.buffer_width, self.buffer_height, GL_DEPTH_COMPONENT32)

        # glsl shaders
        # wireframe mode has no DEPTH
        self.program_shader = create_shader(fragment_shader)
        self.program_wire = create_shader(fragment_shader_wire)
        self.program = self.program_shader

        self.orientation = scene.orientation.to_matrix().to_4x4()

        self.alpha = 0.5

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.region.callback_remove(self._handle)
        self.quit()
        return {'CANCELLED'}

    def quit(self):
        """garbage colect"""
        if self.color_id:
            delete_image(self.color_id)

        if self.depth_id:
            delete_image(self.depth_id)

class VIEW3D_PT_IBL_background(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI' 
    bl_label = "Panorama Background"
    bl_options = {'DEFAULT_CLOSED'}

#    def draw_header(self, context):
#        view = context.space_data
#        self.layout.prop(scene, "_enabled", text="")

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        self.layout.operator("wm.ibl_edit_background")

# ###############################
#  Main / Register / Unregister
# ###############################

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == '__main__':
    register()

