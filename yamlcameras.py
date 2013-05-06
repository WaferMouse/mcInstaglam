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

fov = 69
viewdistance = 15
cellList = []
objlist = []
cameralist = {}
activecameralist = []
yamlcameras = []

name = 1

def main():
    #do something with this eventually
    return

def dirtyTrig(x,y,z): # This function is full of dirty dirty trig to return yaw and pitch in the Minecraft system for a given target coordinate
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
    return {'yaw':yaw,'pitch':pitch}

def pointFinder(x, z, yaw, length):
    yaw = (90 + yaw)%360
    angle = yaw
    x2 = math.cos(angle*(math.pi/180)) * length
    z2 = math.sin(angle*(math.pi/180)) * length
    return (x+x2, z+z2)

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

def boundingBox(poly):
    NW = []
    SE = []
    top = poly[0][1]
    bottom = poly[0][1]
    left = poly[0][0]
    right = poly[0][0]
    if poly[1][1] < top: top = int(poly[1][1])
    if poly[2][1] < top: top = int(poly[2][1])
    if poly[1][1] > bottom: bottom = int(poly[1][1])
    if poly[2][1] > bottom: bottom = int(poly[2][1])
    if poly[1][0] < left: left = int(poly[1][0])
    if poly[2][0] < left: left = int(poly[2][0])
    if poly[1][0] > right: right = int(poly[1][0])
    if poly[2][0] > right: right = int(poly[2][0])
    return({'NW':[top, left],'SE':[bottom, right]})

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
#        bpy.ops.import_scene.obj(filepath=workingdir+"x"+str(obj[0])+"-z"+str(obj[1])+".obj") #does the work of importing the object to blender
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
    
def findCells(pos, viewdistance, fov, poly, name):
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

def placeCamera(player, viewdistance, fov, poly, name):
    location, rotation = mcCamera(player[0],player[1]) # narf!
    bpy.ops.object.camera_add(location=location, rotation=rotation)
    cam = bpy.data.cameras[len(bpy.data.cameras)-1]
    cam.lens_unit = 'DEGREES'
    cam.angle = fov*(math.pi/180)*1.45
    cam.sensor_fit = 'HORIZONTAL'
    cam.clip_end = viewdistance*16
    return

def addCamera(location, rotation, viewdistance, fov, name):
    camera = getPoly(location, rotation, viewdistance, fov, name)
    cameralist[int(name)] = camera
    return

def getPoly(location, rotation, viewdistance, fov, name):
    x1,y,z1 = location
    yaw = rotation['yaw']
    viewdistance = (viewdistance+1) * 16
    xq,zq = pointFinder(x1,z1, yaw, viewdistance)
    x2,z2 = pointFinder(xq,zq, ((yaw+270) % 360), (viewdistance)*math.tan((fov*(math.pi/180))*0.725))
    x3,z3 = pointFinder(xq,zq, ((yaw+90) % 360), (viewdistance)*math.tan((fov*(math.pi/180))*0.725))
    poly = [[x1,z1],[x2,z2],[x3,z3]]
    return({'filename':name,'description':'Blarg!','poly':poly,'boundingbox':boundingBox(poly),'viewdistance':int(viewdistance/16),'fov':fov,'rotation':rotation, 'location':location})  #  location, rotation, viewdistance, fov, poly, boundingBox(poly), name)

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

###########
########### Time for the main loops!
###########

print()
print('Placing cameras')
print()

csvfile = open(logdir+'blendit-'+worldname+'.log', 'r', newline='')
ofile = csv.reader(csvfile, delimiter=',')

for row in ofile:
    x, y, z = float(row[3]), float(row[4]), float(row[5])
    targetx, targety, targetz = float(row[6]), float(row[7]), float(row[8])
    addCamera([x,y,z],dirtyTrig(targetx,targety,targetz),viewdistance,fov, name)
    name = name + 1
csvfile.close()

updatefile = open(logdir+'update-'+worldname+'.log', 'r', newline='')
ofile = csv.reader(updatefile, delimiter=',')
updatelist = list(ofile)
updatefile.close()

print(yaml.dump(cameralist))

#for cam in cameralist:
#    print(yaml.dump(cam))
#print('Done!')