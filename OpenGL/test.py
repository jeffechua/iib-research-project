from OpenGL.GL import *
import OpenGL.GL.shaders
import glfw
import numpy

glfw.init()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
window = glfw.create_window(800, 600, "My Window", None, None)

glfw.make_context_current(window)

triangle = [-0.5, -0.5, 0.0,
            0.5, -0.5, 0.0,
            0.0,  0.5, 0.0]

triangle  = numpy.array(triangle, dtype=numpy.float32)

vertex_shader = """
#version 330
in vec3 position;
in vec3 color;

out vec3 newColor;
void main()
{
    gl_Position = vec4(position, 1.0f);
    newColor = color;
}
"""
fragment_shader = """
#version 330
in vec3 newColor;

out vec4 outColor;
void main()
{
    outColor = vec4(newColor, 1.0f);
}
"""


VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO)
glBufferData(GL_ARRAY_BUFFER, 72, triangle, GL_STATIC_DRAW)

vao = glGenVertexArrays(1)
glBindVertexArray(vao)

shader = OpenGL.GL.shaders.compileProgram(OpenGL.GL.shaders.compileShader(vertex_shader, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER))

position = glGetAttribLocation(shader, "position")
glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
glEnableVertexAttribArray(position)

color = glGetAttribLocation(shader, "color")
glVertexAttribPointer(color, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
glEnableVertexAttribArray(color)



glUseProgram(shader)


glClearColor(.1, .3, .5, 1.0)


while not glfw.window_should_close(window):
    glfw.poll_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glDrawArrays(GL_TRIANGLES, 0, 3)
    glfw.swap_buffers(window)

glfw.terminate()