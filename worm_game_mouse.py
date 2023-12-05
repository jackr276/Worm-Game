"""
Jack Robbins and Randall Tarazona
PBD Recreation of Game Worm.io
"""

"""
TODO Checklist
Make the randomly generated particles move somehow
make the worm less jittery when moving
**make worm addition less jarring, currently very jittery**
"""



#!/usr/bin/python

# This is statement is required by the build system to query build info
if __name__ == '__build__':
    raise Exception

import sys
import math
import random
import time
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

screen_dimx = 1080
screen_dimy = 1080
screen_leftx = -15
screen_rightx = 15
screen_topy = -15
screen_bottomy = 15
screen_world_width = screen_rightx-screen_leftx
screen_world_height = screen_bottomy-screen_topy

time_delta = 1 / 64.
particle_radii = 0.2
dragged_particle = None
is_dragging = False
particle_distance = 2.5
nextId = 3
last_time = 0


class Particle:
    def __init__(self, pid, x, y, partOfWorm, isHead=False, isEnd = False):
        self.pid = pid
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.px = x
        self.py = y
        self.moveX = 0
        self.moveY = 0
        self.inv_mass = 1.0
        #Lets us know if the particle is in the worm
        self.partOfWorm = partOfWorm
        #Lets us know if this the front of worm(only front is draggable)
        self.isHead = isHead
        self.isEnd = isEnd
            


class Constraint:
    def __init__(self, id1, id2, distance):
        self.id1 = id1
        self.id2 = id2
        self.distance = distance
        #increased stiffness(looks a little better when less stiff)
        self.stiffness = 0.09


"""
We will need to make dictionaries for all of these
"""

#Starting with a very small worm
particles = {0 : Particle(0, 0.0, 0.0, True, True),
             1 : Particle(1, 2.5, 0.5, True),
             2: Particle(2, 5.0, 1.0, True, False, True)
            }

#ID of every particle in the worm
wormIDs = [0, 1, 2]

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
    for i in range(len(wormIDs)-1):
        glVertex2f(particles[wormIDs[i]].x, particles[wormIDs[i]].y)
        glVertex2f(particles[wormIDs[i+1]].x, particles[wormIDs[i+1]].y)
           
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
    for particle in particles.values():
        if particle.partOfWorm:
            glColor3f(0.39, 0.27, 0.13)
        else:
            glColor3f(0.99, 0.97, 0.9)

        draw_circle(particle_radii, particle.x, particle.y)
    
    glColor3f(0.39, 0.27, 0.13)

    draw_rope()
    glColor3f(1.0, 0.0, 0.0)
    if dragged_particle is not None:
        draw_circle_outline(
            particle_radii,
            dragged_particle.x,
            dragged_particle.y)


def distance(x1, y1, x2, y2):
    return sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1))


# This will be called when the worm "eats" a particle
def consume(otherParticle):
    global wormIDs
    global particle_distance
    otherParticle.partOfWorm = True
    otherParticle.isTail = True

    if otherParticle.pid in wormIDs:
        return

    wormIDs.append(otherParticle.pid)
    distance_constraints.append(Constraint(wormIDs[-2], wormIDs[-1], particle_distance))

    #Print out current score
    print("Your current score is: " + str(len(wormIDs) - 3))
    

def collision_constraint(particle1, particle2):
    global particle_radii
    correction_x1 = 0.0
    correction_y1 = 0.0
    correction_x2 = 0.0
    correction_y2 = 0.0

    desiredDistance = particle_radii * 2

    particleDist = distance(particle1.x, particle1.y, particle2.x, particle2.y)

    #if particle1 is particle2, don't do any collision checking
    if particleDist == 0:
        return (correction_x1,correction_y1, correction_x2,correction_y2)

    #if our distance is less than radius*2, we have a collision
    if particleDist < desiredDistance-0.001:
        if particle1.isHead:
            consume(particle2)
            return correction_x1, correction_y1, correction_x2, correction_y2
        
        #loss condition
        if particle1.partOfWorm and not particle2.partOfWorm or not particle1.partOfWorm and particle2.partOfWorm:
            print("Worm Body Collision! Game Over")
            print("Your final score is: " + str(len(wormIDs) - 3))
            time.sleep(5)
            glfw.terminate()
            exit()

        #helpers for us, simple calculations we need
        xDiff = particle1.x - particle2.x
        yDiff = particle1.y - particle2.y

        absXDiff = abs(xDiff)
        absYDiff = abs(yDiff)

        #normal vector tells us direction of correction
        normalVecX = xDiff / particleDist
        normalVecY = yDiff / particleDist 

        #Corrections weighted according to inverse masses
        p1InvMassCalc =  -1*(particle1.inv_mass)/(particle1.inv_mass + particle2.inv_mass)
        p2InvMassCalc = (particle2.inv_mass)/(particle1.inv_mass + particle2.inv_mass)

        # constraint is how far we must adjust
        constraint = particleDist - desiredDistance - 0.001

        #apply correction factors
        correction_x1 = p1InvMassCalc * constraint * normalVecX
        correction_x2 = p2InvMassCalc * constraint * normalVecX

        correction_y1 = p1InvMassCalc * constraint * normalVecY
        correction_y2 = p2InvMassCalc * constraint * normalVecY

    return (correction_x1,correction_y1,
            correction_x2,correction_y2)


def resolve_collision_constraints():
	for p1 in particles.values():
		for p2 in particles.values():
			delta_x1, delta_y1, delta_x2, delta_y2 = collision_constraint(p1,p2)
			p1.px +=  delta_x1
			p1.py +=  delta_y1
			p2.px +=  delta_x2
			p2.py +=  delta_y2


def distance_constraint(particle1, particle2, constraint_distance):
    correction_x1 = 0.0
    correction_y1 = 0.0
    correction_x2 = 0.0
    correction_y2 = 0.0

    #If they're not in the worm, they don't need to be moved
    if not particle1.partOfWorm and not particle2.partOfWorm:
        return correction_x1, correction_y1, correction_x2, correction_y2

    #helpers for us, simple calculations we need
    xDiff = particle1.x - particle2.x
    yDiff = particle1.y - particle2.y

    absXDiff = abs(xDiff)
    absYDiff = abs(yDiff)

    #calculate particle distance(|p1-p2| from the paper)
    particleDist = math.sqrt(xDiff * xDiff + yDiff * yDiff)

    if xDiff == 0 or yDiff == 0:
        return correction_x1, correction_y1, correction_x2, correction_y2

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
    global nextId
    global particles
    global distance_constraints
    global particle_radii
    particle_radii

    if not timer():
        return

    ## Generate a particle somewhere randomly
    particles[nextId] = Particle(nextId, random.randint(-15, 15), random.randint(-15, 15), False, False)
    particles[nextId].vx = random.uniform(-3.0, 3.0)
    particles[nextId].vy = random.uniform(-3.0, 3.0)
    nextId += 1


#Only want to generate a particle every couple of seconds, this helper function returns true if time difference is more than 3 seconds
def timer():
    global last_time
    current_time = time.time()
    delta = current_time - last_time
    if(delta > 2):
        last_time = current_time
        return True
    else:
        return False


def pbd_main_loop():
    global particles
    gravity = 0.0
    generate_particle()
    for particle in particles.values():
        # apply external forces - line 5
        particle.vx += 0.0
        particle.vy += gravity * time_delta
        # damp velocities - line 6
        particle.vx *= 0.9
        particle.vy *= 0.9
        # get initial projected positions - line 7
        particle.px = particle.x + particle.vx * time_delta
        particle.py = particle.y + particle.vy * time_delta

    #line 8, resolve collisions
    resolve_collision_constraints()
    
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
    for particle in particles.values():
        # line 13
        particle.vx = (particle.px - particle.x) / time_delta
        particle.vy = (particle.py - particle.y) / time_delta
        # line 14
        particle.x = particle.px
        particle.y = particle.py
    # glutPostRedisplay()


def display():
    #make background color green
    glClearColor(0.0, 0.2, 0.13, 0.9)
    glClear(GL_COLOR_BUFFER_BIT)
    drawParticles()
    glFlush()


def particle_clicked(x, y):
    res = None
    for particle in particles.values():
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
glfw.set_cursor_pos_callback(window, cursor_position_callback)


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