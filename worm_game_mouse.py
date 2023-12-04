"""
Jack Robbins and Randall Tarazona
PBD Recreation of Game Worm.io
"""

#!/usr/bin/python

# This is statement is required by the build system to query build info
if __name__ == '__build__':
    raise Exception

import sys
import math
import random
from math import cos as cos
from math import sin as sin
from math import pi as PI
from math import sqrt as sqrt
import glfw 

try:
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except BaseException:
    print('''
ERROR: PyOpenGL not installed properly.
        ''')
    sys.exit()

screen_dimx = 900
screen_dimy = 900
screen_leftx = -15
screen_rightx = 15
screen_topy = -15
screen_bottomy = 15
screen_world_width = screen_rightx-screen_leftx
screen_world_height = screen_bottomy-screen_topy

time_delta = 1 / 64.
particle_radii = 0.5
dragged_particle = None
is_dragging = False
particle_distance = 2.5
particle_counter = 2
last_time = 0


class Particle:
    def __init__(self, x, y, partOfWorm, isHead=False):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.px = x
        self.py = y
        self.inv_mass = 1.0
        #Lets us know if the particle is in the worm
        self.partOfWorm = partOfWorm
        #Lets us know if this the front of worm(only front is draggable)
        self.isHead = isHead


class Constraint:
    def __init__(self, id1, id2, distance):
        self.id1 = id1
        self.id2 = id2
        self.distance = distance
        #increased stiffness(looks a little better when less stiff)
        self.stiffness = 0.025


#Starting with a very small worm
particles = [Particle(0.0, 0.0, True, True),
             Particle(2.5, 0.5, True),
             Particle(5.0, 1.0, True)
             ]


distance_constraints = [Constraint(0, 1, particle_distance),
                        Constraint(1, 2, particle_distance)
                        ]


def draw_circle_outline(r, x, y):
    i = 0.0
    glLineWidth(3)
    glBegin(GL_LINE_LOOP)
    while i <= 360.0:
        glVertex2f(r * cos(PI * i / 180.0) + x,
                   r * sin(PI * i / 180.0) + y)
        i += 360.0 / 18.0
    glEnd()


def draw_rope():
    #Adjust thickness so it appears worm-like
    glLineWidth(30)
    glBegin(GL_LINES)
    for i in range(len(particles) - 1):
        if(particles[i].partOfWorm and particles[i+1].partOfWorm):
            glVertex2f(particles[i].x, particles[i].y)
            glVertex2f(particles[i + 1].x, particles[i + 1].y)
    glEnd()


def draw_circle(r, x, y):
    i = 0.0
    glLineWidth(1)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x, y)
    while i <= 360.0:
        glVertex2f(r * cos(PI * i / 180.0) + x,
                   r * sin(PI * i / 180.0) + y)
        i += 360.0 / 18.0
    glEnd()


def drawParticles():
    global dragged_particle
    global particles
    glColor3f(1.0, 1.0, 1.0)
    for particle in particles:
        draw_circle(particle_radii, particle.x, particle.y)
    draw_rope()
    glColor3f(1.0, 0.0, 0.0)
    if dragged_particle is not None:
        draw_circle_outline(
            particle_radii,
            dragged_particle.x,
            dragged_particle.y)


def distance(x1, y1, x2, y2):
    return sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1))


def distance_constraint(particle1, particle2, constraint_distance):
    correction_x1 = 0.0
    correction_y1 = 0.0
    correction_x2 = 0.0
    correction_y2 = 0.0

    if not particle1.partOfWorm or not particle2.partOfWorm:
        return (correction_x1, correction_y1, correction_x2, correction_y2)

    
    #helpers for us, simple calculations we need
    xDiff = particle1.x - particle2.x
    yDiff = particle1.y - particle2.y

    absXDiff = abs(xDiff)
    absYDiff = abs(yDiff)

    #calculate particle distance(|p1-p2| from the paper)
    particleDist = math.sqrt(xDiff * xDiff + yDiff * yDiff)

    #calculate normal x and y vectors
    normalVecX = xDiff / particleDist
    normalVecY = yDiff / particleDist
    
    #inverse mass calculations
    p1InvMassCalc =  -1*(particle1.inv_mass)/(particle1.inv_mass + particle2.inv_mass)
    p2InvMassCalc = (particle2.inv_mass)/(particle1.inv_mass + particle2.inv_mass)

    distance_constraint = particleDist - constraint_distance
    
    #update x corrections
    correction_x1 = p1InvMassCalc * distance_constraint * normalVecX
    correction_x2 = p2InvMassCalc * distance_constraint * normalVecX

    # update y corrections
    correction_y1 = p1InvMassCalc * distance_constraint * normalVecY
    correction_y2 = p2InvMassCalc * distance_constraint * normalVecY

    return (correction_x1, correction_y1, correction_x2, correction_y2)


#Randomly generates a particle(essentially the food for the worm)
def generate_particle():
    global particle_counter
    global particles
    global distance_constraints
    global particle_radii
    particle_radii
    
    if not timer():
        return

    ## Generate a particle somewhere randomly
    particles.append(Particle(random.randint(-10, 10), random.randint(-10, 10), False))
    #want particle distance to be radii * 2
    distance_constraints.append(Constraint(particle_counter, particle_counter+1, particle_radii*2.5))
    #update the number of particles
    particle_counter+=1


def timer():
    global Fextx,last_time
    current_time = glfw.get_time()
    delta_time = current_time - last_time
    #last_time = current_time
    if(delta_time > 2):
        last_time=current_time
        return True
    else:
        return False
 
generate_particle()
generate_particle()
generate_particle()

def pbd_main_loop():
    global particles
    gravity = 0.0
    for particle in particles:
        # apply external forces - line 5
        particle.vx += 0.0
        particle.vy += gravity * time_delta
        # damp velocities - line 6
        particle.vx *= 0.9
        particle.vy *= 0.9
        # get initial projected positions - line 7
        particle.px = particle.x + particle.vx * time_delta
        particle.py = particle.y + particle.vy * time_delta
    # line 9
    i = 1
    while i < 4:
        #line 10
        for constraint in distance_constraints:
            stiffness = 1 - (1 - constraint.stiffness)**(1 / i)
            delta_x1, delta_y1, delta_x2, delta_y2 = distance_constraint(
                particles[constraint.id1], particles[constraint.id2], constraint.distance)
            particles[constraint.id1].px += stiffness * delta_x1
            particles[constraint.id1].py += stiffness * delta_y1
            particles[constraint.id2].px += stiffness * delta_x2
            particles[constraint.id2].py += stiffness * delta_y2
        i += 1
    # line 12
    for particle in particles:
        # line 13
        particle.vx = (particle.px - particle.x) / time_delta
        particle.vy = (particle.py - particle.y) / time_delta
        # line 14
        particle.x = particle.px
        particle.y = particle.py
    # glutPostRedisplay()


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    drawParticles()
    glFlush()


def particle_clicked(x, y):
    res = None
    for particle in particles:
        if distance(x, y, particle.x, particle.y) <= particle_radii:
            return particle
    return res


def translate_to_world_coords(screenx, screeny):
    x = (screenx-screen_dimx/2)/screen_dimx* screen_world_width  
    y=  (screeny-screen_dimy/2)/screen_dimy* screen_world_height
    return (x, y)

def mouse_button_callback(window, button, action, mods):
    global dragged_particle, is_dragging
    x, y = glfw.get_cursor_pos(window)
    worldx,worldy = translate_to_world_coords(x,y)
    particle = particle_clicked(worldx, worldy)
    dragged_particle = particle
    #Only the head can be dragged, so check accordingly
    if button == 0 and dragged_particle is not None and dragged_particle.isHead:  
        is_dragging = not is_dragging
        dragged_particle.inv_mass = 1.0
    if button == 1 and not is_dragging:
        dragged_particle = None

def cursor_position_callback(window,x,y ):
    global dragged_particle, is_dragging
    if(x >=0 and x < screen_dimx and 
       y >=0 and y < screen_dimy):
        if is_dragging:
            if dragged_particle is not None:
                worldx, worldy = translate_to_world_coords(x,y)
                dragged_particle.x = worldx
                dragged_particle.y = worldy
                dragged_particle.inv_mass = 0



# Initialize the library
if not glfw.init():
    exit()

# Create a windowed mode window and its OpenGL context
window = glfw.create_window(screen_dimx, screen_dimy, "Worm Simulation", None, None)
if not window:
    glfw.terminate()
    exit()

# Make the window's context current
glfw.make_context_current(window)

# Set callbacks
glfw.set_mouse_button_callback(window, mouse_button_callback)
#glutPassiveMotionFunc(mousePassive)
glfw.set_cursor_pos_callback(window, cursor_position_callback);

gluOrtho2D(screen_leftx,
            screen_rightx,
            screen_bottomy,
            screen_topy)

# Main loop
while not glfw.window_should_close(window):
    # Clear the screen with black color
    pbd_main_loop()
    display()
    # Swap front and back buffers
    glfw.swap_buffers(window)

    # Poll for and process events
    glfw.poll_events()

# Terminate GLFW
glfw.terminate()