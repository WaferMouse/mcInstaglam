import bpy, math, csv, sys, bgl, blf
from bpy import data, ops, props, types, context
from math import pi
from subprocess import call

#sudo java -jar ~/Downloads/jMc2Obj-dev_r276M.jar -s -o ~/mcobj/ --area=0,0,16,16 /Users/joe/Library/Application\ Support/minecraft/saves/bitekiland

def dirty_trig(x,y,z): # This function is full of dirty dirty trig to return yaw and pitch in the Minecraft system for a given target coordinate
    hyp = math.sqrt((abs(x)**2)+(abs(z)**2)) # It's probably best to ignore the horrors that lie within
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

def find_chunks(pos, yaw, clip):
    x0, z0 = pos[0]/16, pos[2]/16
    px = point_finder((x0,z0), yaw, viewdistance)
    print(x0,z0,px)
    print()
    x1, z1 = point_finder(px, yaw-90,viewdistance/math.tan(fov/2))
    x2, z2 = point_finder(px, yaw+90,viewdistance/math.tan(fov/2))
    top, bottom, left, right = x0, x0, z0, z0
    if z1 < top: top = z1
    if z2 < top: top = z2
    if z1 > bottom: bottom = z1
    if z2 > bottom: bottom = z2
    if x1 < left: left = x1
    if x2 < left: left = x2
    if x1 > right: right = x1
    if x2 > right: right = x2
    print("TOP "+str(top))
    print("BOTTOM "+str(bottom))
    print("LEFT "+str(left))
    print("RIGHT "+str(right))
#    chunkz = top
#    while chunkz <= bottom:
#        chunkx = left
#        while chunkx <= right:
#            if point_inside_polygon(chunkx, chunkz,((x0,z0),(x1,z1),(x2,z2))) == 1:
#                add_chunk(chunkx,chunkz)
#            chunkx +=1
#        chunkz +=1
    return()

def find_chunks2(pos, yaw, viewdistance):
    x,y,z = pos
    print(str(x)+","+str(y)+","+str(z))
    if x < 0: x -= 16
    if z < 0: z -= 16
    x = int(x/16)
    z = int(z/16)
    for iz in range(0 - viewdistance, (viewdistance*2)+1):
        for ix in range(0 - viewdistance, (viewdistance*2)+1):
            add_chunk(ix+x,iz+z)
    return()
    
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
    
def point_finder(pos, yaw, length):
    x, z = pos[0], pos[1]
    angle = 90-yaw%90
    yaw = yaw%360
    a = length/math.sin(angle)
    b = a*math.tan(angle)
    if 180 <= yaw < 270:
        x = x-a
        z = z+b
    elif 90 <= yaw < 180:
        x = x-b
        z = z-a
    elif 0 <= yaw < 90:
        x = x+a
        z = z-b
    else:
        x = x+b
        z = z+a
    return (x, z)

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
        
def mc_player(position,rotation): # Expresses player's position in Minecraft using Blender's coordinate system
    x, z, y = position[0], position[1]-1, 0-position[2] # position argument should be a tuple containing XYZ coords
    yaw = (180-rotation[0])*(math.pi/180) # rotation argument should be a tuple containing yaw... 
    pitch = (rotation[1]+90)*(math.pi/180) # ... and pitch
    return ((x,y,z),(pitch,0,yaw)) # Returns a tuple with nested tuples ready to plug into location and rotation in Blender, respectively

#bpy.ops.import_scene.obj(filepath="minecraft.obj")

filepath = sys.argv[6]

csvfile = open(filepath, 'r', newline='')
ofile = csv.reader(csvfile, delimiter=',')
fov = 70
viewdistance = 16
chunklist = []

print('Placing cameras')

for row in ofile:
    x, y, z = float(row[3]), float(row[4]), float(row[5])
    targetx, targety, targetz = float(row[6]), float(row[7]), float(row[8])
    location, rotation = mc_player((x,y,z),dirty_trig(targetx,targety,targetz))
    find_chunks(location, dirty_trig(targetx,targety,targetz)[0], viewdistance)
#    find_chunks2((x,y,z), dirty_trig(targetx,targety,targetz)[0], viewdistance)
#    call(["java", "-jar ~/Downloads/jMc2Obj-dev_r276M.jar -s -o ~/mcobj/"])# java -jar ~/Downloads/jMc2Obj-dev_r276M.jar -s -o ~/mcobj/ --area=0,0,16,16 /Users/joe/Library/Application\ Support/minecraft/saves/bitekiland
#    bpy.ops.object.camera_add(location=location, rotation=rotation)
#    cam = bpy.data.cameras[len(bpy.data.cameras)-1]
#    cam.lens = (cam.sensor_width/2)/math.tan(fov)
csvfile.close()

sceneKey = bpy.data.scenes.keys()[0]
cameraNames=''

print('Looping Cameras')
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
#        bpy.ops.render.render( write_still=True )
        c = c + 1
print('Done!')