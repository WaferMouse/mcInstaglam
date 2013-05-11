import bpy, math, csv, sys, bgl, blf, os
from bpy import data, ops, props, types, context
from math import pi
from subprocess import call
#from termcolor import colored, cprint
import yaml

worldname = str(sys.argv[6])
worldsettings = yaml.load(open('config.yaml'))['worlds'][worldname]
logdir = os.path.expanduser(worldsettings['logdir'])
worlddir = os.path.expanduser(worldsettings['worlddir'])
outputdir = os.path.expanduser(worldsettings['outputdir'])
workingdir = os.path.expanduser(worldsettings['workingdir'])
jmc2objdir = os.path.expanduser(worldsettings['jmc2objdir'])
jmc2obj = jmc2objdir+worldsettings['jmc2obj']
os.chdir(jmc2objdir)

cellList = []
objlist = []
cameralist = yaml.load(open(logdir+'cameras.yaml'))
activecameralist = yaml.load(open(logdir+'activecameras.yaml'))

def main():
    #do something with this eventually
    return

def addCell(x,z):
    cell = x,z
    if not cellList:
        cellList.append(cell)
        return()
    i = 0
    for i in cellList:
        if i == cell:
            return()
    cellList.append(cell)
    return()

def exportCellList():
    print()
    print("Exporting cells")
    print()
    cell = cellList[0]
    i = 0
    exit = 0
    while i < len(cellList):
        exit = 0
        cell = cellList[i]
        if i+1< len(cellList):
            nextcell = cellList[i+1]
        else:
            exit = 1
        z=cell[1]
        x=cell[0]
        bx = x
        sx=int(x*32)
        sz=int(z*64)
        while nextcell[1] == z and nextcell[0] == x+1 and i<len(cellList) and exit == 0:
            sx = sx+32
            x = x+1
            i = i+1
            if i+1< len(cellList):
                nextcell=cellList[i+1]
        print()
        print("----- Progress: "+str(i)+"-"+str(len(cellList))+" -----")
        print()
        i = i + 1
        addObj((bx*32,sz,x*32,sz))
    return() 

def addObj(obj):
    x1,z1,x2,z2 = obj
#    call(["java", "-jar", jmc2obj, "-s", "--objfile=x"+str(x1)+"-z"+str(z1)+".obj", "--export=obj", "--output="+workingdir, "--height=50,256", "--area="+str(x1)+","+str(z1)+","+str(x2+32)+","+str(z2+64),worlddir+worldname]) #this does the actual export
    objlist.append(obj)
    return()

def importObjlist():
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

def mcCamera(position,rotation): # Expresses player's position in Minecraft using Blender's coordinate system
    x, z, y = position[0], position[1]-1, 0-position[2] # position argument should be a tuple containing XYZ coords
    yaw = (180-rotation[0])*(math.pi/180) # rotation argument should be a tuple containing yaw... 
    pitch = (rotation[1]+90)*(math.pi/180) # ... and pitch
    return ((x,y,z),(pitch,0,yaw)) # Returns a tuple with nested tuples ready to plug into location and rotation in Blender, respectively

def pointInsidePolygon(x,y,poly):
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
    
def findCells(poly):
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
    left, top = cellFromCoords(left, top)
    right, bottom = cellFromCoords(right, bottom)
    top = int(top)
    bottom = int(bottom)
    left = int(left)
    right = int(right)
    for zloop in range(top, bottom+1):
        for xloop in range(left, right+1):
            if checkCell(xloop,zloop,poly) == True:
                addCell(xloop,zloop)
    return()

def cellFromCoords(x,z):
    x = (x - (x % 32))/32
    z = (z - (z % 64))/64
    return(x,z)
    
def checkCell(x,z,poly):
    if pointInsidePolygon(x*32,z*64,poly) == True:
        return True
    poly2 = []
    poly2.append((x*32,z*64))
    poly2.append((31+(x*32),z*64))
    poly2.append((31+(x*32),63+(z*64)))
    poly2.append((x*32,63+(z*64)))
    for i in range(3):
        for j in range(4):
            if isLineIntersect([poly2[j],poly2[(j+1)%4]],[poly[i],poly[(i+1)%3]]) == True:
                return True
    return False

def isLineIntersect(line1, line2):
    return doLineSegmentsIntersect(line1[0][0],line1[0][1],line1[1][0],line1[1][1],line2[0][0],line2[0][1],line2[1][0],line2[1][1])

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

def placeCamera(camera):
    location, rotation = mcCamera(camera['position'],(camera['rotation']['yaw'],camera['rotation']['pitch']))
    bpy.ops.object.camera_add(location=location, rotation=rotation)
    cam = bpy.data.cameras[len(bpy.data.cameras)-1]
    cam.lens_unit = 'DEGREES'
    cam.angle = camera['fov']*(math.pi/180)*1.45
    cam.sensor_fit = 'HORIZONTAL'
    cam.clip_end = camera['viewdistance']*16
    return

###########
########### Time for the main loops!
###########

print()
print('Placing cameras')
print()

for cam in activecameralist[worldname]:
    placeCamera(cameralist['worlds'][worldname][cam])
    findCells(cameralist['worlds'][worldname][cam]['poly'])

cellList = sorted(cellList, key=lambda cell: cell[0])
cellList = sorted(cellList, key=lambda cell: cell[1])

if cellList != []:
    exportCellList()
    importObjlist()
    print()
    print('Looping Cameras')
    print()
else:
    print('Nothing to update!')

for mat in bpy.data.materials: # Illuminate!
    if mat.name.find('torch_flame') != -1:
        mat.emit = 15
#NOTE: Blender's internal renderer imports torches with single sided planes.
#TL;DR: Torches will only cast light from three quarters.  Solution pending.

c=0

sceneKey = bpy.data.scenes.keys()[0]
cameraNames=''

for obj in bpy.data.objects:
    # Find cameras that match cameraNames
    if ( obj.type =='CAMERA') and ( cameraNames == '' or obj.name.find(cameraNames) != -1) :
        print("Rendering scene["+sceneKey+"] with Camera["+obj.name+"]")

        # Set Scenes camera and output filename
        bpy.data.scenes[sceneKey].camera = obj
        bpy.data.scenes[sceneKey].render.image_settings.file_format = 'PNG'
        cam = activecameralist[worldname][c]
        bpy.data.scenes[sceneKey].render.filepath = str(outputdir)+worldname+'-'+str(cam)
        print(worldname+'-'+str(cam))
#        bpy.data.scenes[sceneKey].render.resolution_x = 768
#        bpy.data.scenes[sceneKey].render.resolution_y = 768
#        bpy.data.scenes[sceneKey].render.resolution_percentage = 100
        # Render Scene and store the scene
#        bpy.ops.render.render( write_still=True )
        c = c + 1
print('Done!')