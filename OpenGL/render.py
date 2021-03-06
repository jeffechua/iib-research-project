import numpy as np
from numpy import clip as clamp
from shapely.geometry import box
from math import fmod, sin, cos, pi
from geometrise import *
from osapi import *
import glm
import glfw
from OpenGL.GL import shaders
from OpenGL.GL import *


pointer_verts = np.array([0, .15, 0, 1, 1, 1,
                          5, .15, 0, 1, 0, 0,
                          0,   5, 0, 0, 1, 0,
                          0, .15, 5, 0, 0, 1], dtype='float32')
pointer_trigs = np.array([0, 1, 0, 2, 0, 3], dtype='uint32')

light_dir = glm.normalize(glm.vec3(-2.0, -1.0, -1.5))

print('Starting render...')

# glfw stuff

glfw.init()
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(800, 600, 'Render', None, None)
glfw.set_window_pos(window, 0, 0)
glfw.make_context_current(window)

mouse_x = 0
mouse_y = 0
mouse_left_down = False
mouse_right_down = False
mouse_just_down = False

mouse_worldpos = glm.vec3()
highlit_id = -1

pos_x = o.x
pos_z = o.y
angle_x = 0.0
angle_y = 0.0
matrix = glm.mat4()
height = 100.0  # y


def mouse_button_callback(window, button, action, mods):
    global mouse_left_down, mouse_right_down, mouse_just_down
    if action == glfw.PRESS:
        if button == glfw.MOUSE_BUTTON_LEFT:
            mouse_left_down = True
            mouse_right_down = False
            mouse_just_down = True
            if highlit_id != -1:
                toid = data.os_topo_toid[highlit_id]
                glfw.set_window_title(
                    window, f'TOID: {toid}(v{data.os_topo_version[highlit_id]}) UPRN: {", ".join(request_uprn(toid))}')
        if button == glfw.MOUSE_BUTTON_RIGHT:
            mouse_right_down = True
            mouse_left_down = False
            mouse_just_down = True
    if action == glfw.RELEASE:
        mouse_right_down = False  # this is technically a weird way to behave
        mouse_left_down = False  # if you operate mid and left mouse at the
        mouse_just_down = False  # same time, but why would you do that?


def mouse_move_callback(window, new_x, new_y):
    X_ROT_SENSITIVITY = 0.05
    Y_ROT_SENSITIVITY = 0.03
    global mouse_just_down, mouse_left_down, mouse_right_down, mouse_x, mouse_y, pos_x, pos_z, angle_x, angle_y, height, matrix, mouse_worldpos, highlit_id
    translation_factor = height/glfw.get_window_size(window)[1]
    dx = new_x - mouse_x
    dy = mouse_y - new_y  # window space is y-inverted compared to world
    if mouse_just_down:
        mouse_just_down = False
    else:
        if mouse_left_down:
            pos_x = pos_x - (dx*cos(angle_y)-dy * sin(angle_y)
                             / clamp(cos(angle_x), 0.01, 1))*translation_factor
            pos_z = pos_z - (dx*sin(angle_y)+dy * cos(angle_y)
                             / clamp(cos(angle_x), 0.01, 1))*translation_factor
        elif mouse_right_down:
            angle_y = fmod(angle_y - dx * Y_ROT_SENSITIVITY, 2*pi)
            angle_x = clamp(angle_x + dy * X_ROT_SENSITIVITY, 0, pi/2)
    mouse_x = new_x
    mouse_y = new_y


def mouse_scroll_callback(window, dx, dy):
    RADIUS_SENSITIVITY = 0.02
    global height
    height = clamp(height*(1+dy*RADIUS_SENSITIVITY), 10, 10000)


glfw.set_cursor_pos_callback(window, mouse_move_callback)
glfw.set_mouse_button_callback(window, mouse_button_callback)
glfw.set_scroll_callback(window, mouse_scroll_callback)

# gl stuff

# build shader
vertex_shader = shaders.compileShader("""
#version 330
uniform mat4 matrix;
uniform vec3 offset;
uniform vec3 lightDir;
uniform vec3 baseColor;
uniform int colorMode;
layout(location = 1) in vec3 position;
layout(location = 2) in vec3 normal;
flat out vec4 color;
void main() {
    gl_Position = matrix * vec4(position - offset, 1.0f);
    float attenuation = dot(normalize(normal), lightDir);
    attenuation *= attenuation < 0 ? -0.8 : -0.2;
    attenuation += 0.2f;
    color = vec4(colorMode == 0 ? (baseColor * attenuation) : normal, 1.0f);
}
""", GL_VERTEX_SHADER)
fragment_shader = shaders.compileShader("""
#version 330
flat in vec4 color;
out vec4 outputColor;
void main() {
    outputColor = color;
}
""", GL_FRAGMENT_SHADER)

# world VBO; this is not a VAO property and so must be managed separately
world_vertex_buffer = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, world_vertex_buffer)
glBufferData(GL_ARRAY_BUFFER, len(vertices)*4, vertices, usage=GL_STATIC_DRAW)

# world VAO; even though vertex attributes will eventually be read from the VBO,
# which is not VAO-associated, the information on how to read the VBO *is*
# VAO-associated and must be set for each VAO. But the access instructions still must
# be assigned while the relevant VBO is bound, which makes this all really stupid.
world_vao = glGenVertexArrays(1)
glBindVertexArray(world_vao)
world_triangle_buffer = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, world_triangle_buffer)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(triangles)
             * 4, triangles, usage=GL_STATIC_DRAW)
glEnableVertexAttribArray(1)
glEnableVertexAttribArray(2)
glVertexAttribPointer(1, 3, GL_FLOAT, False, 6*4, ctypes.c_void_p(0))
glVertexAttribPointer(2, 3, GL_FLOAT, False, 6*4, ctypes.c_void_p(3*4))

# pointer VBO; similar
pointer_vertex_buffer = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, pointer_vertex_buffer)
glBufferData(GL_ARRAY_BUFFER, len(pointer_verts) *
             4, pointer_verts, usage=GL_STATIC_DRAW)

# pointer VAO; similar
pointer_vao = glGenVertexArrays(1)
glBindVertexArray(pointer_vao)
pointer_triangle_buffer = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, pointer_triangle_buffer)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(pointer_trigs)
             * 4, pointer_trigs, usage=GL_STATIC_DRAW)
glEnableVertexAttribArray(1)
glEnableVertexAttribArray(2)
glVertexAttribPointer(1, 3, GL_FLOAT, False, 6*4, ctypes.c_void_p(0))
glVertexAttribPointer(2, 3, GL_FLOAT, False, 6*4, ctypes.c_void_p(3*4))

# set up shaders
shader = shaders.compileProgram(vertex_shader, fragment_shader)
shaders.glUseProgram(shader)
matrix_location = glGetUniformLocation(shader, 'matrix')
offset_location = glGetUniformLocation(shader, 'offset')
light_location = glGetUniformLocation(shader, 'lightDir')
color_location = glGetUniformLocation(shader, 'baseColor')
mode_location = glGetUniformLocation(shader, 'colorMode')

# activate depth testing
glEnable(GL_CULL_FACE)
glEnable(GL_DEPTH_TEST)
glDepthMask(GL_TRUE)
glDepthFunc(GL_LEQUAL)
glDepthRange(0.0, 1.0)

while not glfw.window_should_close(window):
    # mouseover detection
    window_size = glfw.get_window_size(window)
    aspect = window_size[0]/window_size[1]
    depth_read = glReadPixels(mouse_x, window_size[1] - mouse_y, 1, 1,
                              GL_DEPTH_COMPONENT, GL_FLOAT)[0][0]
    clip_coords = glm.vec4(mouse_x/window_size[0]*2-1, 1-mouse_y/window_size[1]*2,
                           depth_read*2-1, 1)  # inexplicably the matrix needs transposing??? probably some column-/row-major bullshit
    mouse_worldpos = glm.transpose(
        matrix) / clip_coords + glm.vec4(pos_x, 0, pos_z, 0)
    hits = data.sindex.query(box(mouse_worldpos.x-0.2, mouse_worldpos.z-0.05,
                                 mouse_worldpos.x+0.05, mouse_worldpos.z+0.05),
                             predicate='intersects')
    highlit_id = hits[0] if len(hits) > 0 else -1
    # figure out projection matrix and lighting
    matrix = glm.rotate(-angle_y, glm.vec3(0, 1, 0))
    matrix = glm.rotate(matrix, pi/2 - angle_x, glm.vec3(1, 0, 0))
    matrix = matrix * glm.ortho(-height*aspect/2, height*aspect/2,
                                -height/2, height/2,
                                height/2*10, -height/2*10)
    glUniform3f(light_location, light_dir[0], light_dir[1], light_dir[2])
    glUniformMatrix4fv(matrix_location, 1, False,
                       np.array(matrix, dtype='float32'))
    # print(matrix)
    # clear stuff
    glClearColor(0, 0, 0, 0)
    glClearDepth(1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # draw world
    glBindVertexArray(world_vao)
    glBindBuffer(GL_ARRAY_BUFFER, world_vertex_buffer)
    glUniform3f(offset_location, pos_x, 0, pos_z)
    glUniform3f(color_location, 1, 1, 1)
    glUniform1i(mode_location, 0)
    glDrawElements(GL_TRIANGLES, len(triangles),
                   GL_UNSIGNED_INT, ctypes.c_void_p(0))
    # draw highlight
    if highlit_id != -1:
        glUniform3f(color_location, 0, 1, 0)
        glDrawElements(GL_TRIANGLES, lookup[highlit_id, 3] - lookup[highlit_id, 2],
                       GL_UNSIGNED_INT, ctypes.c_void_p(int(lookup[highlit_id, 2]*4)))
    # draw pointer
    glDepthMask(GL_FALSE)
    glBindVertexArray(pointer_vao)
    glBindBuffer(GL_ARRAY_BUFFER, pointer_vertex_buffer)
    glUniform3f(offset_location, pos_x - mouse_worldpos.x, -
                mouse_worldpos.y, pos_z-mouse_worldpos.z)
    glUniform1i(mode_location, 1)
    glDrawElements(GL_LINES, len(pointer_trigs), GL_UNSIGNED_INT, None)
    glDepthMask(GL_TRUE)
    # swap buffers
    glfw.swap_buffers(window)
    glfw.poll_events()

#glDrawArrays(GL_TRIANGLES, 0, len(vertices)//3)

glfw.terminate()
