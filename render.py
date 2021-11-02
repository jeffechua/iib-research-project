import numpy as np
from numpy import clip as clamp
from math import fmod, sin, cos, pi
from geometrise import *
import glm
import glfw
from OpenGL.GL import shaders
from OpenGL.GL import *


# vertices = np.array([-0.5, -0.5, 0.0, 1.0, 0.0, 0.0,
#             0.5, -0.5, 0.0, 1.0, 1.0, 0.0,
#             0.0,  0.5, 0.0,  1.0, 0.0, 1.0], dtype='float32')
# triangles = np.array([0,1,2], dtype='uint32')

pointer_verts = np.array([1, 1, 0, 0, 1, 0,
                          -1, 1, 0, 0, 1, 0,
                          0, 0, 0, 0, 1, 0,
                          0, 1, 1, 0, 1, 0,
                          0, 1, -1, 0, 1, 0,
                          0, 0, 0, 0, 1, 0,
                          1, 1, 0, 0, 1, 0,
                          0, 1, 1, 0, 1, 0,
                          -1, 1, 0, 0, 1, 0,
                          -1, 1, 0, 0, 1, 0,
                          0, 1, -1, 0, 1, 0,
                          1, 1, 0, 0, 1, 0], dtype='float32')
pointer_trigs = np.array(
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], dtype='uint32')

light_dir = glm.normalize(glm.vec3(2.0, -1.0, 1.5))

print('Trigs imported.')

# glfw stuff

SCREEN_RADIUS = 300
glfw.init()
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(
    SCREEN_RADIUS*2, SCREEN_RADIUS*2, 'Render', None, None)
glfw.set_window_pos(window, 0, 0)
glfw.make_context_current(window)

mouse_x = 0
mouse_y = 0
mouse_worldpos = glm.vec3()
mouse_left_down = False
mouse_right_down = False
mouse_just_down = False

pos_x = o.x
pos_z = o.y
angle_x = 0.0
angle_y = 0.0
matrix = glm.mat4()
radius = 100.0


def mouse_button_callback(window, button, action, mods):
    global mouse_left_down, mouse_right_down, mouse_just_down
    if action == glfw.PRESS:
        if button == glfw.MOUSE_BUTTON_LEFT:
            mouse_left_down = True
            mouse_right_down = False
            mouse_just_down = True
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
    global mouse_just_down, mouse_left_down, mouse_right_down, mouse_x, mouse_y, pos_x, pos_z, angle_x, angle_y, radius, matrix, mouse_worldpos
    translation_factor = radius/SCREEN_RADIUS
    dx = new_x - mouse_x
    dy = new_y - mouse_y
    if mouse_just_down:
        mouse_just_down = False
    else:
        if mouse_left_down:
            pos_x = pos_x - (dx*cos(angle_y)-dy * sin(angle_y)
                             / clamp(cos(angle_x), 0.01, 1))*translation_factor
            pos_z = pos_z - (dx*sin(angle_y)+dy * cos(angle_y)
                             / clamp(cos(angle_x), 0.01, 1))*translation_factor
        elif mouse_right_down:
            angle_y = fmod(angle_y + dx * Y_ROT_SENSITIVITY, 2*pi)
            angle_x = clamp(angle_x - dy * X_ROT_SENSITIVITY, 0, pi/2)
    mouse_x = new_x
    mouse_y = new_y
    depth_read = glReadPixels(mouse_x, SCREEN_RADIUS*2 - mouse_y, 1, 1,
                              GL_DEPTH_COMPONENT, GL_FLOAT)[0][0]
    clip_coords = glm.vec4(mouse_x/SCREEN_RADIUS-1,
                           1-mouse_y/SCREEN_RADIUS, depth_read*2-1, 1)
    # inexplicably the matrix needs transposing??? probably some column-/row-major bullshit
    mouse_worldpos = glm.transpose(
        matrix) / clip_coords + glm.vec4(pos_x, 0, pos_z, 0)


def mouse_scroll_callback(window, dx, dy):
    RADIUS_SENSITIVITY = 0.02
    global radius
    radius = clamp(radius*(1+dy*RADIUS_SENSITIVITY), 10, 10000)


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
layout(location = 1) in vec3 position;
layout(location = 2) in vec3 normal;
flat out vec4 color;
void main() {
    gl_Position = matrix * vec4(position - offset, 1.0f);
    float attenuation = dot(normalize(normal), lightDir);
    attenuation *= attenuation < 0 ? -0.8 : -0.2;
    attenuation += 0.2f;
    color = vec4(baseColor * attenuation, 1.0f);
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

# activate depth testing
glEnable(GL_DEPTH_TEST)
glDepthMask(GL_TRUE)
glDepthFunc(GL_LEQUAL)
glDepthRange(0.0, 1.0)

while not glfw.window_should_close(window):
    # figure out projection matrix and lighting
    matrix = glm.rotate(-angle_y, glm.vec3(0, 1, 0))
    matrix = glm.rotate(matrix, angle_x - pi/2, glm.vec3(1, 0, 0))
    matrix = matrix * glm.ortho(-radius, radius, -
                                radius, radius, -radius*10, radius*10)
    glUniform3f(light_location, light_dir[0], light_dir[1], light_dir[2])
    glUniformMatrix4fv(matrix_location, 1, False,
                       np.array(matrix, dtype='float32'))
    # clear stuff
    glClearColor(0, 0, 0, 0)
    glClearDepth(1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # draw world
    glBindVertexArray(world_vao)
    glBindBuffer(GL_ARRAY_BUFFER, world_vertex_buffer)
    glUniform3f(offset_location, pos_x, 0, pos_z)
    glUniform3f(color_location, 1, 1, 1)
    glDrawElements(GL_TRIANGLES, len(triangles), GL_UNSIGNED_INT, None)
    # draw pointer
    glBindVertexArray(pointer_vao)
    glBindBuffer(GL_ARRAY_BUFFER, pointer_vertex_buffer)
    glUniform3f(offset_location, pos_x - mouse_worldpos.x, -
                mouse_worldpos.y, pos_z-mouse_worldpos.z)
    glUniform3f(color_location, 1, 0, 0)
    glDrawElements(GL_TRIANGLES, len(pointer_trigs), GL_UNSIGNED_INT, None)
    # swap buffers
    glfw.swap_buffers(window)
    glfw.poll_events()

#glDrawArrays(GL_TRIANGLES, 0, len(vertices)//3)

glfw.terminate()
