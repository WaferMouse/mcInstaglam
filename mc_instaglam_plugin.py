__plugin_name__ = "instaglam"
__plugin_version__ = "0.1"
__plugin_mainclass__ = "instaglam"

import yaml
import org.bukkit
from datetime import datetime
import math
import os

global cameralist
global settings

cameralist = {}
settings = {}
activecameralist = {}

@hook.enable
def onEnable():
    print "[instaglam] Instaglam enabled."
    global settings
    global cameralist
    os.chdir(os.path.expanduser('~/spigot/1.4.7/lib/Lib'))
    settings = yaml.load(open('config.yaml'))
    cameralist = yaml.load(open('cameras.yaml'))
    if cameralist['worlds'] == None:
        cameralist['worlds'] = {}
    dump = 0
    for world in settings['worlds']:
        activecameralist[world] = []
        if not world in cameralist['worlds']:
            dump = 1
            cameralist['worlds'][world] = {}
    if dump == 1:
        yaml.dump(cameralist, open('cameras.yaml', 'w'))
    yaml.dump(activecameralist, open('activecameras.yaml', 'w'))

@hook.command("instaglam")
def onCommand(sender, args):
    camera = {}
    name = sender.getName()
    if name == "CONSOLE":
        print('Dont do that!')
    else:
        location = sender.getLocation()
        world = location.world.name
        if world in settings['worlds']:
            time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
            camera['position'] = [location.x,location.y,location.z]
            camera['rotation'] = {'yaw': location.yaw, 'pitch': location.pitch}
            camera['viewdistance'] = 15
            camera['fov'] = 69
            camera['description'] = "Blarg!"
            camera['filename'] = str(time+'-'+world+'-'+name)
            camera['poly'] = getPoly(location,15,69)
            camera['boundingbox'] = boundingBox(camera['poly'])
            cameralist['worlds'][world][str(time+'-'+name)] = camera
            yaml.dump(cameralist, open('cameras.yaml', 'w'))
            activecameralist[world].append(str(time+'-'+name))
            yaml.dump(activecameralist, open('activecameras.yaml', 'w'))

@hook.event("block.BlockBreakEvent", "normal")
def onBlockBreak(event):
    checkBlock(event.getBlock().getLocation())

@hook.disable
def onDisable():
    print "[instaglam] Instaglam disabled."

def getPoly(location, viewdistance, fov):
    x1,z1 = location.x, location.z
    yaw = location.yaw
    viewdistance = (viewdistance+1) * 16
    xq,zq = pointFinder(x1,z1, yaw, viewdistance)
    x2,z2 = pointFinder(xq,zq, ((yaw+270) % 360), (viewdistance)*math.tan((fov*(math.pi/180))*0.725))
    x3,z3 = pointFinder(xq,zq, ((yaw+90) % 360), (viewdistance)*math.tan((fov*(math.pi/180))*0.725))
    poly = [[x1,z1],[x2,z2],[x3,z3]]
    return(poly)

def pointFinder(x, z, yaw, length):
    yaw = (90 + yaw)%360
    angle = yaw
    x2 = math.cos(angle*(math.pi/180)) * length
    z2 = math.sin(angle*(math.pi/180)) * length
    return (x+x2, z+z2)

def boundingBox(poly):
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

def checkBlock(location):
    world = location.world.name
    if world in cameralist['worlds']:
        if not cameralist['worlds'][world] == {}:
            for cam in cameralist['worlds'][world]:
                if not str(cam) in activecameralist[world] and not str(cam) == 'this':
                    boundingbox = cameralist['worlds'][world][cam]['boundingbox']
                    if (boundingbox['NW'][1] <= location.x <= boundingbox['SE'][1]) and (boundingbox['NW'][0] <= location.z <= boundingbox['SE'][0]):
                        if pointInsidePolygon(location.x,location.z,cameralist['worlds'][world][cam]['poly']):
                            activecameralist[world].append(str(cam))
                            yaml.dump(activecameralist, open('activecameras.yaml', 'w'))
    return

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