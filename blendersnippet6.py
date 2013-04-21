import bpy, math, csv, sys, bgl, blf
from bpy import data, ops, props, types, context
from math import pi
from subprocess import call
#from termcolor import colored, cprint

#sudo java -jar ~/Downloads/jMc2Obj-dev_r276M.jar -s -o ~/mcobj/ --area=0,0,16,16 /Users/joe/Library/Application\ Support/minecraft/saves/bitekiland

def dirty_trig(x,y,z): # This function is full of dirty dirty trig to return yaw and pitch in the Minecraft system for a given target coordinate
    hyp = math.sqrt((abs(x)**2)+(abs(z)**2)) # It's probably best to ignore the horrors that lie within
    if hyp == 0:
        if y>0:
            pitch = 90
        else:
            pitch = 0-90
        yaw = 0
    else:
        pitch = math.atan(abs(y)/hyp) # It's a workaround until Skript implements yaw and pitch
        pitch = pitch*(180/math.pi)
        if y<1: pitch = 0-pitch
        yaw = (math.atan(abs(z)/abs(x)))*(180/math.pi) # Fairly certain that this thing is just begging to /0 in several places
        if x>0: yaw = 0-yaw
        if z>0: yaw = 0-yaw
        if x>0:
            yaw = 270+yaw
        else:
            yaw = 90+yaw
    return (yaw,pitch)

def w_swap(a,b):
    return (b,a)

def find_chunks2(pos, yaw, viewdistance):
    x,y,z = pos
    print(str(x)+","+str(y)+","+str(z))
    if x < 0: x -= 16
    if z < 0: z -= 16
    x = int(x/16)
    z = int(z/16)
    for iz in range(0 - viewdistance, viewdistance+1):
        for ix in range(0 - viewdistance, viewdistance+1):
            add_chunk(ix+x,iz+z)
    return()

def find_chunks3(pos, yaw, viewdistance, fov):
    x1,y,z1 = pos
    x1,z1 = point_finder(x1,z1, yaw+180, 32)
    x1 = x1/16
    z1 = z1/16
    xq,zq = point_finder(x1,z1, yaw, viewdistance+1)
    x2,z2 = point_finder(xq,zq, yaw+270, (viewdistance+1)*math.tan((fov/2)+5))
    x3,z3 = point_finder(xq,zq, yaw+90, (viewdistance+1)*math.tan((fov/2)+5))
    top = int(z1)
    bottom = int(z1)
    left = int(x1)
    right = int(x1)
    if z2 < top: top = int(z2)
    if z3 < top: top = int(z3)
    if z2 > bottom: bottom = int(z2)
    if z3 > bottom: bottom = int(z3)
    if x2 < left: left = int(x2)
    if x3 < left: left = int(x3)
    if x2 > right: right = int(x2)
    if x3 > right: right = int(x3)
    poly = (x1,z1),(x2,z2),(x3,z3)
    for zloop in range(top, bottom):
        for xloop in range(left, right):
            if point_inside_polygon(xloop,zloop,poly) == True:
                add_chunk(xloop,zloop)
    return()

def point_finder(x, z, yaw, length):
    yaw = 360 - (yaw%360)
    angle = yaw
    x2 = math.cos(angle*(math.pi/180)) * length
    z2 = math.sin(angle*(math.pi/180)) * length
    return (x+x2, z+z2)

def add_chunk(x,z):
    chunk = x,z
    if not chunklist:
        chunklist.append(chunk)
        return()
    i = 0
    for i in chunklist:
        if i == chunk:
            return()
    chunklist.append(chunk)
    return()

def export_chunklist():
#    for i in chunklist:
#        export_chunk(i)
    print()
    print("Exporting chunks")
    print()
    chunk = chunklist[0]
    i = 0
    exit = 0
    while i < len(chunklist):
        chunk = chunklist[i]
        if i+1< len(chunklist):
            nextchunk = chunklist[i+1]
        else:
            exit = 1
        z=chunk[1]
        x=chunk[0]
        bx = x
        sx=int(x*16)
        sz=int(z*16)
        while nextchunk[1] == z and nextchunk[0] == x+1 and i<len(chunklist) and exit == 0:
            sx = sx+16
            x = x+1
            i = i+1
            if i+1< len(chunklist):
                nextchunk=chunklist[i+1]
        print()
        print("----- Progress: "+str(i)+"-"+str(len(chunklist))+" -----")
        print()
        i = i + 1
#        call(["java", "-jar", "jMc2Obj-dev_r276M.jar", "-s", "--objfile=x"+str(bx)+"-z"+str(z)+".obj", "--area="+str((bx*16)-16)+","+str(sz-16)+","+str(sx)+","+str(sz),"/Users/joe/bitekiland"])# java -jar ~/Downloads/jMc2Obj-dev_r276M.jar -s -o ~/mcobj/ --area=0,0,16,16 /Users/joe/Library/Application\ Support/minecraft/saves/bitekiland
        add_obj((bx*16,sz,sx,sz))
#        bpy.ops.import_scene.obj(filepath="x"+str(bx)+"-z"+str(z)+".obj")
    return() 

def export_chunklist2():
    chunk0 = chunklist[0]
    x1 = chunk0[0]
    z1 = chunk0[1]
    x2 = x1
    z2 = z1
    for i in chunklist:
        if i[0]>x2:
            x2 = i[0]
        if i[1]>z2:
            z2 = i[1]
        if i[0]<x1:
            x1 = i[0]
        if i[1]<z1:
            z1 = i[1]
    add_obj((int(x1*16),int(z1*16),int(x2*16),int(z2*16)))
    return()

def add_obj(obj):
    x1,z1,x2,z2 = obj
    call(["java", "-jar", "jMc2Obj-dev_r276M.jar", "-s", "--objfile=x"+str(x1)+"-z"+str(z1)+".obj", "--height=50,256", "--area="+str(x1)+","+str(z1)+","+str(x2+16)+","+str(z2+16),"/Users/joe/bitekiland"])
    objlist.append(obj)
    return()

def import_objlist():
    print()
    print("Importing objects")
    print()
    count = 0
    for obj in objlist:
        bpy.ops.import_scene.obj(filepath="x"+str(obj[0])+"-z"+str(obj[1])+".obj")
        count = count + 1
        print()
        print("----- Progress: "+str(count)+"-"+str(len(objlist))+" -----")
        print()
    return()

def mc_player(position,rotation): # Expresses player's position in Minecraft using Blender's coordinate system
    x, z, y = position[0], position[1]-1, 0-position[2] # position argument should be a tuple containing XYZ coords
    yaw = (180-rotation[0])*(math.pi/180) # rotation argument should be a tuple containing yaw... 
    pitch = (rotation[1]+90)*(math.pi/180) # ... and pitch
    return ((x,y,z),(pitch,0,yaw)) # Returns a tuple with nested tuples ready to plug into location and rotation in Blender, respectively

def point_inside_polygon(x,y,poly):
    n = len(poly)
    inside =False
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside

#bpy.ops.import_scene.obj(filepath="minecraft.obj")

filepath = sys.argv[6]
print(360 % 360)
print()
csvfile = open(filepath, 'r', newline='')
ofile = csv.reader(csvfile, delimiter=',')
fov = 70
viewdistance = 16
chunklist = []
objlist = []

#call(["java", "-jar", "jMc2Obj-dev_r276M.jar", "-s", "-o", "/Users/joe/mcobj/", "--area=0,0,16,16", "/Users/joe/bitekiland"])

print()
print('Placing cameras')
print()

for row in ofile:
    x, y, z = float(row[3]), float(row[4]), float(row[5])
    targetx, targety, targetz = float(row[6]), float(row[7]), float(row[8])
    location, rotation = mc_player((x,y,z),dirty_trig(targetx,targety,targetz))
#    find_chunks(location, rotation[0], clip)
    find_chunks3((x,y,z), dirty_trig(targetx,targety,targetz)[0], viewdistance, fov)
    bpy.ops.object.camera_add(location=location, rotation=rotation)
    cam = bpy.data.cameras[len(bpy.data.cameras)-1]
    cam.lens = (cam.sensor_width/2)/math.tan(fov)
    cam.clip_end = viewdistance*16
csvfile.close()

chunklist = sorted(chunklist, key=lambda chunk: chunk[0])
chunklist = sorted(chunklist, key=lambda chunk: chunk[1])

export_chunklist2()
import_objlist()

sceneKey = bpy.data.scenes.keys()[0]
cameraNames=''

print()
print('Looping Cameras')
print()

c=0
for obj in bpy.data.objects:
    # Find cameras that match cameraNames
    if ( obj.type =='CAMERA') and ( cameraNames == '' or obj.name.find(cameraNames) != -1) :
        print("Rendering scene["+sceneKey+"] with Camera["+obj.name+"]")

        # Set Scenes camera and output filename
        bpy.data.scenes[sceneKey].camera = obj
#        bpy.data.scenes[sceneKey].camera.lens_unit = 'FOV'
#        bpy.data.scenes[sceneKey].camera.lens = 70*(pi/180.0)
        bpy.data.scenes[sceneKey].render.image_settings.file_format = 'JPEG'
        bpy.data.scenes[sceneKey].render.filepath = '//camera_' + str(c)
#        bpy.data.scenes[sceneKey].render.resolution_x = 1920
#        bpy.data.scenes[sceneKey].render.resolution_y = 1080
#        bpy.data.scenes[sceneKey].render.resolution_percentage = 100
        # Render Scene and store the scene
        bpy.ops.render.render( write_still=True )
        c = c + 1
print('Done!')