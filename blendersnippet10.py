import bpy, math, csv, sys, bgl, blf, os
from bpy import data, ops, props, types, context
from math import pi
from subprocess import call
#from termcolor import colored, cprint

worldname = str(sys.argv[6])
logdir = os.path.expanduser('~/mcobjcmd/')
worlddir = os.path.expanduser('~/worlds/')
outputdir = os.path.expanduser('~/renders/')
workingdir = os.path.expanduser('~/igtemp/')
javadir = os.path.expanduser('~/jmc2obj/')

def dirty_trig(x,y,z): # This function is full of dirty dirty trig to return yaw and pitch in the Minecraft system for a given target coordinate
    hyp = math.sqrt((abs(x)**2)+(abs(z)**2)) # It's probably best to ignore the horrors that lie within
    if hyp == 0:
        if y>0:
            pitch = 90
        else:
            pitch = 0-90
    else:
        pitch = math.atan(y/hyp) # It's a workaround until Skript implements yaw and pitch
        pitch = (pitch*(180/math.pi)) % 360
        if pitch > 180:
            pitch = 0-(360-pitch)
        if x == 0:
            if z > 1:
                yaw = 0
            else:
                yaw = 180
        else:
            yaw = (math.atan(abs(z)/abs(x)))*(180/math.pi)
            if x>0: yaw = 0-yaw
            if z>0: yaw = 0-yaw
            if x>0:
                yaw = 270+yaw
            else:
                yaw = 90+yaw
    return (yaw,pitch)

def point_finder(x, z, yaw, length):
    yaw = (90 + yaw)%360
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
    print()
    print("Exporting chunks")
    print()
    chunk = chunklist[0]
    i = 0
    exit = 0
    while i < len(chunklist):
        exit = 0
        chunk = chunklist[i]
        if i+1< len(chunklist):
            nextchunk = chunklist[i+1]
        else:
            exit = 1
        z=chunk[1]
        x=chunk[0]
        bx = x
        sx=int(x*32)
        sz=int(z*64)
        while nextchunk[1] == z and nextchunk[0] == x+1 and i<len(chunklist) and exit == 0:
            sx = sx+32
            x = x+1
            i = i+1
            if i+1< len(chunklist):
                nextchunk=chunklist[i+1]
        print()
        print("----- Progress: "+str(i)+"-"+str(len(chunklist))+" -----")
        print()
        i = i + 1
        add_obj((bx*32,sz,x*32,sz))
    return() 

def add_obj(obj):
    x1,z1,x2,z2 = obj
    call(["java", "-jar", javadir+"jMc2Obj-dev_r276M.jar", "-s", "--objfile=x"+str(x1)+"-z"+str(z1)+".obj", "--mtlfile=x"+str(x1)+"-z"+str(z1)+".mtl", "--output="+workingdir, "--height=50,256", "--area="+str(x1)+","+str(z1)+","+str(x2+32)+","+str(z2+64),worlddir+worldname]) #this does the actual export
    objlist.append(obj)
    return()

def import_objlist():
    print()
    print("Importing objects")
    print()
    count = 0
    for obj in objlist:
        bpy.ops.import_scene.obj(filepath=workingdir+"x"+str(obj[0])+"-z"+str(obj[1])+".obj") #does the work of importing the object to blender
#        os.remove(workingdir+"x"+str(obj[0])+"-z"+str(obj[1])+".obj") #remove .obj file to prevent eating HDD space
        count = count + 1
        print()
        print("----- Progress: "+str(count)+"-"+str(len(objlist))+" -----")
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

def islineintersect(line1, line2):
    return doLineSegmentsIntersect(line1[0][0],line1[0][1],line1[1][0],line1[1][1],line2[0][0],line2[0][1],line2[1][0],line2[1][1])
    
def find_chunks5(pos, viewdistance, fov, poly, name):
    (x1,z1),(x2,z2),(x3,z3) = poly
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
    left, top = megachunkfromcoords(left, top)
    right, bottom = megachunkfromcoords(right, bottom)
    top = int(top)
    bottom = int(bottom)
    left = int(left)
    right = int(right)
    for zloop in range(top, bottom+1):
        for xloop in range(left, right+1):
            if checkmegachunk(xloop,zloop,poly) == True:
                add_chunk(xloop,zloop)
    return()

def megachunkfromcoords(x,z):
    x = (x - (x % 32))/32
    z = (z - (z % 64))/64
    return(x,z)
    
def checkmegachunk(x,z,poly):
    if point_inside_polygon(x*32,z*64,poly) == True:
        return True
    poly2 = []
    poly2.append((x*32,z*64))
    poly2.append((31+(x*32),z*64))
    poly2.append((31+(x*32),63+(z*64)))
    poly2.append((x*32,63+(z*64)))
    for i in range(3):
        for j in range(4):
            if islineintersect([poly2[j],poly2[(j+1)%4]],[poly[i],poly[(i+1)%3]]) == True:
                return True
    return False

def isOnSegment(xi,yi,xj,yj,xk,yk):
    return ((xi <= xk or xj <= xk) and (xk <= xi or xk <= xj) and (yi <= yk or yj <= yk) and (yk <= yi or yk <= yj))

def computeDirection(xi,yi,xj,yj,xk,yk):
    a = (xk - xi) * (yj - yi)
    b = (xj - xi) * (yk - yi)
    if a<b:
        return -1
    elif a>b:
        return 1
    return 0
    
def doLineSegmentsIntersect(x1,y1,x2,y2,x3,y3,x4,y4):
    d1 = computeDirection(x3, y3, x4, y4, x1, y1)
    d2 = computeDirection(x3, y3, x4, y4, x2, y2)
    d3 = computeDirection(x1, y1, x2, y2, x3, y3)
    d4 = computeDirection(x1, y1, x2, y2, x4, y4)
    return (((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0))) or (d1 == 0 and isOnSegment(x3, y3, x4, y4, x1, y1)) or (d2 == 0 and isOnSegment(x3, y3, x4, y4, x2, y2)) or (d3 == 0 and isOnSegment(x1, y1, x2, y2, x3, y3)) or (d4 == 0 and isOnSegment(x1, y1, x2, y2, x4, y4))

def placeCamera(player, viewdistance, fov, poly, name):
    location, rotation = mc_player(player[0],player[1]) # narf!
    bpy.ops.object.camera_add(location=location, rotation=rotation)
    cam = bpy.data.cameras[len(bpy.data.cameras)-1]
    cam.lens_unit = 'DEGREES'
    cam.angle = fov*(math.pi/180)*1.45
    cam.sensor_fit = 'HORIZONTAL'
    cam.clip_end = viewdistance*16
    return

def addCamera(location, rotation, viewdistance, fov, name):
    camera = getPoly(location, rotation, viewdistance, fov, name)
    cameralist.append(camera)
    return

def getPoly(location, rotation, viewdistance, fov, name):
    x1,y,z1 = location
    yaw = rotation[0]
    viewdistance = (viewdistance+1) * 16
    xq,zq = point_finder(x1,z1, yaw, viewdistance)
    x2,z2 = point_finder(xq,zq, ((yaw+270) % 360), (viewdistance)*math.tan((fov*(math.pi/180))*0.725))
    x3,z3 = point_finder(xq,zq, ((yaw+90) % 360), (viewdistance)*math.tan((fov*(math.pi/180))*0.725))
    poly = (x1,z1),(x2,z2),(x3,z3)
    position = location, rotation
    return(position, viewdistance, fov, poly, name)

def addActiveCamera(cam):
    if not activecameralist:
        activecameralist.append(cam)
        return()
    i = 0
    for i in activecameralist:
        if i == cam:
            return()
    activecameralist.append(cam)
    return()

csvfile = open(logdir+'blendit-'+worldname+'.log', 'r', newline='')
ofile = csv.reader(csvfile, delimiter=',')
fov = 69
viewdistance = 15
chunklist = []
objlist = []
cameralist = []
activecameralist = []

name = 1

print()
print('Placing cameras')
print()

for row in ofile:
    x, y, z = float(row[3]), float(row[4]), float(row[5])
    targetx, targety, targetz = float(row[6]), float(row[7]), float(row[8])
    addCamera((x,y,z),dirty_trig(targetx,targety,targetz),viewdistance,fov, name)
    name = name + 1
csvfile.close()

updatefile = open(logdir+'update-'+worldname+'.log', 'r', newline='')
ofile = csv.reader(updatefile, delimiter=',')
updatelist = list(ofile)
updatefile.close()

for cam in cameralist:
    result = 0
    i=0
    while result == 0 and i < len(updatelist):
        line = updatelist[i]
        if point_inside_polygon(float(line[2]),float(line[4]),cam[3]):
            addActiveCamera(cam)
            result = 1
        else:
            i=i+1

for cam in activecameralist:
    placeCamera(cam[0],cam[1],cam[2],cam[3],cam[4])
    find_chunks5(cam[0],cam[1],cam[2],cam[3],cam[4])

chunklist = sorted(chunklist, key=lambda chunk: chunk[0])
chunklist = sorted(chunklist, key=lambda chunk: chunk[1])

if chunklist != []:
    export_chunklist()
    import_objlist()
else:
    print('Nothing to update!')

print()
print('Looping Cameras')
print()

c=0

for mat in bpy.data.materials: # Illuminate!
    if mat.name.find('torch_flame') != -1:
        mat.emit = 4
#NOTE: Blender's internal renderer imports torches with single sided planes.
#TL;DR: Torches will only cast light from three quarters.  Solution pending.

sceneKey = bpy.data.scenes.keys()[0]
cameraNames=''

for obj in bpy.data.objects:
    # Find cameras that match cameraNames
    if ( obj.type =='CAMERA') and ( cameraNames == '' or obj.name.find(cameraNames) != -1) :
        print("Rendering scene["+sceneKey+"] with Camera["+obj.name+"]")

        # Set Scenes camera and output filename
        bpy.data.scenes[sceneKey].camera = obj
        bpy.data.scenes[sceneKey].render.image_settings.file_format = 'PNG'
        cam = activecameralist[c]
        bpy.data.scenes[sceneKey].render.filepath = str(outputdir)+worldname+'-'+str(cam[4])
        print(worldname+'-'+str(cam[4]))
#        bpy.data.scenes[sceneKey].render.resolution_x = 768
#        bpy.data.scenes[sceneKey].render.resolution_y = 768
#        bpy.data.scenes[sceneKey].render.resolution_percentage = 100
        # Render Scene and store the scene
        bpy.ops.render.render( write_still=True )
        c = c + 1
print('Done!')