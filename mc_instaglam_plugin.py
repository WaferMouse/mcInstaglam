__plugin_name__ = "instaglam"
__plugin_version__ = "0.1"
__plugin_mainclass__ = "instaglam"

import yaml
import org.bukkit
from datetime import datetime
import math
import os

global cameras
global settings

cameras = {}
settings = {}
activecameras = {}

@hook.enable
def onEnable():
    print "Hiyaaa!!!"
    global settings
    global cameras
    os.chdir(os.path.expanduser('~/spigot/1.4.7/lib/Lib'))
    settings = yaml.load(open('config.yaml'))
    cameras = yaml.load(open('cameras.yaml'))
    for world in settings['worlds']:
        activecameras[world] = []
    yaml.dump(activecameras, open('activecameras.yaml', 'w'))

@hook.command("instaglam")
def onCommand(sender, args):
    camera = {}
    name = sender.getName()
    if name == "CONSOLE":
        msg(sender,"I'm not quite sure where you are looking at, so i'm afraid that won't work")
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
            cameras['worlds'][world][str(time+'-'+name)] = camera
            yaml.dump(cameras, open('cameras.yaml', 'w'))
            activecameras[world].append(str(time+'-'+name))
            yaml.dump(activecameras, open('activecameras.yaml', 'w'))
            msg(sender,'Camera saved!')
        else:
            msg(sender,'Instaglam not available on this world.')

@hook.disable
def onDisable():
    print "Instaglam disabled!"

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