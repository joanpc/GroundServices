'''
X-Plane Ground Services

Provides ground services with object animations using the OpenSceneryX library.
A nice plugin to have some movement around your plane, and do your push-back
and refueling.

Copyright (C) 2011  Joan Perez i Cauhe
---
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

from XPLMDefs import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *
from XPLMPlanes import *
from SandyBarbourUtilities import *
from PythonScriptMessaging import *
from XPLMPlugin import *
from XPLMMenus import *
from XPWidgetDefs import *
from XPWidgets import *
from XPStandardWidgets import *
from XPLMScenery import *
from XPLMDisplay import *
from os import path
from random import randint
from math import *
import cPickle

DEBUG=False

# False constants
__VERSION__='alpha-5'
PRESETS_FILE='WFprofiles.wfp'
HELP_CAPTION='Profile name: '
# Far from that range objects will be destroyed
DESTROY_DISTANCE = 500

# ARBS 4600 l/min
#RFLOW=1200
# basket 1300k/min 2800 lb/min 1600 litres/min
#RFLOW=420


#Callback interval
REFUEL_INTERVAL=0.2

# Animation rate
# 0.04 = 25FPS,  0.05 = 20FPS...
ANIM_RATE=0.04

#Tug rudder offset
TUG_OFFSET=4.2

# Nose wheel tiller joy axis assignment
NOSE_WHEEL_TILLER = 37

OBJ_PATH = 'Custom Scenery/OpenSceneryX/objects/airport/vehicles/'

class Empty:
    # an empty class for assigning values
    pass

class c:
    '''
    Conversion rates and other useful constants
    '''
    # weight
    LB2KG=0.45359237
    KG2LB=2.20462262
    # Volume
    #L2GAL=0.264172052
    GAL2LIT=3.785411784
    L2GAL=1/GAL2LIT
    
    # density
    JETADENSITY=0.8
    AVGASDENSITY=0.721
    
    # Flow
    GPM2KPM=GAL2LIT*JETADENSITY
    
    # Force
    #HP2W = 745.699872
    HP2W    = 745.69987158227022
    W2HP    = 1/HP2W
    BHP2W   = 9810.657  
    
    KMH2MS = 1000/3600
    MS2KMH = 3600/1000
    '''
    Useful functions
    '''
    @classmethod
    def circular(self, x):
        if (x>1): x = 0
        return (1-x**2)**0.5
    
    @classmethod
    def circularRev(self, x):
        if (abs(x)>1): x = 1
        if (abs(x)<0): x = 0
        return 1-(1-x**2)**0.5
    
    @classmethod
    def shortHdg(self, a, b):
        if a == 360: a = 0
        if b == 360: b = 0
        if a > b:
            cw = (360 - a + b)
            ccw = -(a - b);
        else:
            cw = -(360 - b + a)
            ccw = (b - a)     
        if abs(cw) < abs(ccw):
            return cw
        return ccw
    @classmethod
    def fullHdg(self, a, b):
        if a == 360: a = 0
        if b == 360: b = 0
        if b > a:
            return (b - a)
        else:
            return (360 - a + b)
    @classmethod
    def limit(self, x, lim = 1):
        if      x > lim: return lim
        elif    x < -lim: return -lim
        else:   return x
    @classmethod
    def stime(self, sec):
        # returns formated seconds
        return '%d:%02d:%02d' % ( sec/3600, sec%3600/60, sec%3600%60 )
class Config:
    
    #Avaliable objects
    # Tugs
    T_SMALL = OBJ_PATH + 'tugs/small/%i/object.obj' % randint(1,2)
    T_MEDIUM = OBJ_PATH + 'tugs/large/4/object.obj'
    #T_MEDIUM = OBJ_PATH + 'tugs/large/misc/misc.obj'
        
    T_LARGE  = OBJ_PATH + 'tugs/large/%i/object.obj' % 3
    T_LARGED = OBJ_PATH + 'tugs/large/%i/object.obj' % 2
    T_MILI  = OBJ_PATH + 'tugs/military/1/object.obj'
    
    F_LARGE = OBJ_PATH + 'fuel/large/%i/object.obj' % randint(1,8)
    F_MEDIUM   = OBJ_PATH + 'fuel/medium/%i/object.obj' % randint(1,9)
    F_SMALL = OBJ_PATH + 'fuel/small/1/object.obj'
    
    ## Avaliable tugs
    tugs = {'tbl600':
                    {'name':    'TBL600',
                    'obj':      T_LARGED,
                    'power':    567,
                    'desc':     'Douglas-Kalmar TBL-600',
                    'mspeed':   3.2,
                    'weight':   6000,
                    'gdist':    5,
                   },
            'tbl180':
                    {'name':    'TBL180',
                    'obj':      T_LARGE,
                    'power':    82,
                    'desc':     'Douglas-Kalmar TBL-180',
                    'mspeed':   3.2,
                    'weight':   2000,
                    'gdist':    7,
                   },
            'tbl50':
                    {'name':    'TBL180',
                    'obj':      T_MEDIUM,
                    'power':    72,
                    'desc':     'Douglas-Kalmar TBL-180',
                    'mspeed':   3.2,
                    'weight':   1500,
                    'gdist':    5,
                   },
            'manual':
                    {'name':     'manual',
                    'obj':      T_SMALL,
                    'power':    4,
                    'desc':     'manual tow',
                    'mspeed':   3.2,
                    'weight':   30,
                    'gdist':    5,
                   },
                    
    }
    # Class defaults
    defaults = { 'ABC':   { # TBL600 522 kW
                           'tug':     tugs['tbl600'],
                           'truck':   F_LARGE,
                           'flow':    800,
                          },
                'D':     { 'tug':    tugs['tbl180'],
                           'truck':   F_MEDIUM,
                           'flow':    600,
                          },
                 'EF':     { 'tug':    tugs['tbl50'],
                           'truck':   F_SMALL,
                           'flow':    400,
                          },
                 'GA':     { 'tug':   tugs['manual'],
                           'truck':   F_SMALL,
                           'flow':    50,
                          },
                }

    def __init__(self, plugin):
        
        self.plugin = plugin
        # Defaults
        # Scenery Objects
        self.obj = Empty()
        self.tug = Empty()
        
        self.obj.stairs = OBJ_PATH + 'stairs/1/object.obj'
        self.obj.bus    = OBJ_PATH + 'busses_coaches/minibusses/swissport/1/object.obj'
        self.obj.gpu    = OBJ_PATH + 'gpus/1/object.obj'
    
        self.tug.autopilot = True
        self.getConfig('A')
        
    def getConfig(self, acfClass = False):
        '''
        Todo, get config..
        '''
        if acfClass:
            for k in self.defaults:
                if acfClass in k:
                    self.obj.truck  = self.defaults[k]['truck']
                    self.obj.tug    = self.defaults[k]['tug']['obj']
                    self.tpower     = self.defaults[k]['tug']['power'] * 1000
                    self.tgearDist  = self.defaults[k]['tug']['gdist']
                    self.tweight    = self.defaults[k]['tug']['weight']
                    self.flow       = self.defaults[k]['flow'] * c.GPM2KPM
                    if DEBUG:
                        print self.defaults[k]
                    break
        pass
        
        
class PythonInterface:
    def XPluginStart(self):
        self.Name = "GroundServices - " + __VERSION__
        self.Sig = "GroundServices.joanpc.PI"
        self.Desc = "X-Plane Ground Services"
        
        # TODO: DELETE Array of presets
        self.presets = []
        self.presetFile = False
        
        # Sim pause
        self.paused = EasyDref('sim/time/paused', 'int')
        
        self.window, self.fuelWindow, self.reFuelWindow, self.pushbackWindow, self.aboutWindow = [False] * 5
        
        self.Mmenu = self.mainMenuCB
        
        self.mPluginItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), 'Ground Services', 0, 1)
        self.mMain       = XPLMCreateMenu(self, 'Ground Services', XPLMFindPluginsMenu(), self.mPluginItem, self.Mmenu, 0)
        
        # Menu Items
        self.mReFuel    =  XPLMAppendMenuItem(self.mMain, 'Request Refuel', 1, 1)
        self.mPushBack  =  XPLMAppendMenuItem(self.mMain, 'Request Pushback', 2, 1)
        self.mPushBack  =  XPLMAppendMenuItem(self.mMain, 'Request Stairs', 3, 1)
        self.mGpu       =  XPLMAppendMenuItem(self.mMain, 'GPU', 4, 1)
        self.mAbout     =  XPLMAppendMenuItem(self.mMain, 'About', 5, 1)
        
        self.tailnum = ''
        
        # Fuel floop
        self.RefuelFloopCB = self.RefuelCallback
        XPLMRegisterFlightLoopCallback(self, self.RefuelFloopCB, 0, 0)
        
        # Push back callback
        self.PushbackCB = self.pushBackCallback
        XPLMRegisterFlightLoopCallback(self, self.PushbackCB, 0, 0)
        
        # Main Floop
        self.mainCB = self.mainCallback
        XPLMRegisterFlightLoopCallback(self, self.mainCB, 60, 0)
        
        # Aicraft data access
        self.acf = Aircraft()
        
        # Scenery objects
        self.refuel, self.pos , self.truck, self.tug, self.stairs, self.bus, self.gpu = tuple([False]) * 7
        self.stairStatus, self.gpuStatus = False, False
        
        # Init config
        self.conf = Config(self)
        
        # Register commands
        self.cmd = []
        self.cmd.append(EasyCommand(self, 'pusback_request', self.PushBack, 'Request', 'Request Push Back, toggle window'))
        self.cmd.append(EasyCommand(self, 'pusback_cancel', self.PushBack, ('Stop', True), 'Cancel Push Back')) 
        self.cmd.append(EasyCommand(self, 'refuel_request', self.Refuel, 'Request', 'Request Refuel, toggle window')) 
        self.cmd.append(EasyCommand(self, 'refuel_cancel', self.Refuel, ('Stop', True), 'Cancel Refuel'))
        self.cmd.append(EasyCommand(self, 'stairs_request', self.stairsC, 'come', 'Request Stairs'))
        self.cmd.append(EasyCommand(self, 'stairs_cancel', self.stairsC, 'go', 'Stairs recede'))
        self.cmd.append(EasyCommand(self, 'stairs_toggle', self.stairsC, 'toggle', 'Toggle stairs'))
        self.cmd.append(EasyCommand(self, 'gpu_request', self.gpuTruck, 'come', 'Request GPU'))
        self.cmd.append(EasyCommand(self, 'gpu_cancel', self.gpuTruck, 'go', 'Recede GPU'))
        self.cmd.append(EasyCommand(self, 'gpu_toggle', self.gpuTruck, 'toggle', 'Toggle GPU'))
        
        return self.Name, self.Sig, self.Desc

    def reset(self):
        '''
        Resets all animations, actions and windows
        '''
        if self.reFuelWindow:
            XPDestroyWidget(self, self.ReFuelWindowWidget, 1)
            self.reFuelWindow = False
        
        if self.pushbackWindow:
            XPHideWidget(self.pushbackCancelButton)
            XPShowWidget(self.pushbackButton)
        
        # Stop pushback
        XPLMSetFlightLoopCallbackInterval(self, self.PushbackCB, 0, 0, 0)
        # Stop Refuel
        XPLMSetFlightLoopCallbackInterval(self, self.RefuelFloopCB, 0, 0, 0)
        # Destroy all objects
        SceneryObject.destroyAll()
        self.pos , self.truck, self.tug, self.stairs, self.bus, self.gpu = tuple([False]) * 6

    def XPluginStop(self):
        XPLMDestroyMenu(self, self.mMain)
        # Unregister commands
        for c in self.cmd:
            c.destroy()
        self.reset()
        
        # Reset windows
        if self.pushbackWindow:
            XPDestroyWidget(self, self.PusbackWindowWidget, 1)
                # Reset windows
        if self.aboutWindow:
            XPDestroyWidget(self, self.aboutWindowWidget, 1)
            
        XPLMUnregisterFlightLoopCallback(self, self.RefuelFloopCB, 0)
        XPLMUnregisterFlightLoopCallback(self, self.PushbackCB, 0)
        XPLMUnregisterFlightLoopCallback(self, self.mainCB, 0)
        pass
        
    def XPluginEnable(self):
        return 1
    
    def XPluginDisable(self):
        pass
    
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        if (inFromWho == XPLM_PLUGIN_XPLANE):
            if inParam == XPLM_PLUGIN_XPLANE: 
                if inMessage == XPLM_MSG_PLANE_LOADED:# On aircraft change
                    # On plane load
                    pass
                elif inMessage == 106:# On aircraft unload
                    # On plane unload
                    if DEBUG:
                        print "Plane unloaded"
                    pass
                elif inMessage == XPLM_MSG_AIRPORT_LOADED: # On aiport load
                    self.reset()
                    self.tailnum = self.acf.tailNumber.value[0]
                    self.conf.getConfig(self.acf.getClass())
                    plane, plane_path = XPLMGetNthAircraftModel(0)
        
    def mainMenuCB(self, menuRef, menuItem):
        '''
        Main menu Callback
        '''
        if menuItem == 1:
            self.Refuel("Request")
        elif menuItem == 2:
            self.PushBack("Request")
        elif menuItem == 3:
            self.stairsC('toggle')
        elif menuItem == 4:
            self.gpuTruck('toggle')
        elif menuItem == 5:
            if (not self.aboutWindow):
                self.CreateAboutWindow(221, 640, 200, 165)
                self.aboutWindow = True
            elif (not XPIsWidgetVisible(self.aboutWindowWidget)):
                XPShowWidget(self.aboutWindowWidget)
            
    
    def mainCallback(self, elapsedMe, elapsedSim, counter, refcon):
        '''
        Check every minute if we can earse distant objects
        '''
        if len(SceneryObject.objects):
            for object in SceneryObject.objects: 
                if self.acf.getPointDist(object.getPos()) > DESTROY_DISTANCE:
                    object.destroy()
            return 60
        return 0
    
    def CreateAboutWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - 40 - 20 * 8
        Buffer = "Ground Services"
        
        # Create the Main Widget window
        self.aboutWindowWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,0 , xpWidgetClass_MainWindow)
        window = self.aboutWindowWidget
        
        # Create the Sub window
        subw = XPCreateWidget(x+10, y-30, x2-20 + 10, y2+40 -25, 1, "" ,  0,window, xpWidgetClass_SubWindow)
        # Set the style to sub window
        XPSetWidgetProperty(subw, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)
        x += 20
        y -= 30
        
        # Add Close Box decorations to the Main Widget
        XPSetWidgetProperty(window, xpProperty_MainWindowHasCloseBoxes, 1)
               
        from sys import version_info
        
        # Get Open Scenery X Version
        osxlib = open('%s/Custom Scenery/OpenSceneryX/library.txt' % XPLMGetSystemPath())
        if osxlib:
            for line in iter(osxlib):
                if 'Version' in line:
                    osxversion = line[line.find('v'):]
                    break
            if not osxversion:
                osxversion = 'Not found'
        else:
            osxversion = 'Not found'
        XPlaneVersion, XPLMVersion, HostID = XPLMGetVersions()
    
        sysinfo = [
        'Ground Services: %s' % __VERSION__,
        '(c) joan perez cauhe 2011',
        ]
        for label in sysinfo:
            y -= 15
            XPCreateWidget(x, y, x+40, y-20, 1, label, 0, window, xpWidgetClass_Caption)
        
        # Visit site 
        self.aboutVisit = XPCreateWidget(x+20, y-20, x+120, y-60, 1, "Visit site", 0, window, xpWidgetClass_Button)
        XPSetWidgetProperty(self.aboutVisit, xpProperty_ButtonType, xpPushButton)
        
        y -= 40
        sysinfo = [
        'System information:',
        'X-plane: %.2f' % (int(XPlaneVersion)/1000.0),
        'Python: %i.%i.%i' % (version_info[0], version_info[1], version_info[2]),
        'OpenSceneryX: %s' % osxversion
        ]
        
        for label in sysinfo:
            y -= 15
            XPCreateWidget(x, y, x+40, y-20, 1, label, 0, window, xpWidgetClass_Caption)
        
        # Register our widget handler
        self.aboutWindowHandlerCB = self.aboutWindowHandler
        XPAddWidgetCallback(self, window, self.aboutWindowHandlerCB)
    
    def aboutWindowHandler(self, inMessage, inWidget, inParam1, inParam2):
        if (inMessage == xpMessage_CloseButtonPushed):
            if (self.aboutWindow):
                XPHideWidget(self.aboutWindowWidget)
            return 1

        # Handle any button pushes
        if (inMessage == xpMsg_PushButtonPressed):

            if (inParam1 == self.aboutVisit):
                from webbrowser import open_new
                open_new('http://forums.x-plane.org/index.php?app=downloads&showfile=14790');
                return 1
        return 0
            
    def CreatePushBackWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h -25
        Buffer = "Request PushBack"
        
        # Create the Main Widget window
        self.PusbackWindowWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,0 , xpWidgetClass_MainWindow)
        window = self.PusbackWindowWidget
        
        # Create the Sub window
        subw = XPCreateWidget(x+10, y-30, x2-20 + 10, y2+40 -25, 1, "" ,  0,window, xpWidgetClass_SubWindow)
        # Set the style to sub window
        XPSetWidgetProperty(subw, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)
        
        # Add Close Box decorations to the Main Widget
        XPSetWidgetProperty(window, xpProperty_MainWindowHasCloseBoxes, 1)
        
        x += 20
        # distance
        XPCreateWidget(x, y-40, x+40, y-60, 1, 'Distance (m)', 0, window, xpWidgetClass_Caption)
        self.pusbackDistInput = XPCreateWidget(x+80, y-40, x+140, y-62, 1, '80', 0, window, xpWidgetClass_TextField)
        XPSetWidgetProperty(self.pusbackDistInput, xpProperty_TextFieldType, xpTextEntryField)
        XPSetWidgetProperty(self.pusbackDistInput, xpProperty_Enabled, 1)
        
        y -= 30
        
        # Disable rotation if we don't have a joystick
        rotation_default = 0;
        rotation_enabled = 0;
        
        if not self.acf.has_joystic.value:
            XPCreateWidget(x, y-40, x+80, y-60, 1, 'Rotation disabled: No joystick', 0, window, xpWidgetClass_Caption)
        elif not self.acf.hasYaw():
            XPCreateWidget(x, y-40, x+80, y-60, 1, 'No Rotation: no yaw assigned', 0, window, xpWidgetClass_Caption)
        else:
            rotation_default = 90
            rotation_enabled = 1
                
        # rotation
        XPCreateWidget(x, y-40, x+40, y-60, rotation_enabled, 'Rotation (deg)', 0, window, xpWidgetClass_Caption)
        self.pusbackRotInput = XPCreateWidget(x+80, y-40, x+140, y-62, rotation_enabled, str(rotation_default), 0, window, xpWidgetClass_TextField)
        XPSetWidgetProperty(self.pusbackRotInput, xpProperty_TextFieldType, xpTextEntryField)
        XPSetWidgetProperty(self.pusbackRotInput, xpProperty_Enabled, rotation_enabled)
        
        y-= 25
        
        # NoseRight checkbox
        XPCreateWidget(x, y-40, x+20, y-60, rotation_enabled, 'Nose Right', 0, window, xpWidgetClass_Caption)
        self.pusbackRightCheck = XPCreateWidget(x+70, y-40, x+80, y-60, rotation_enabled, "", 0, window, xpWidgetClass_Button)
        XPSetWidgetProperty(self.pusbackRightCheck, xpProperty_ButtonType, xpRadioButton)
        XPSetWidgetProperty(self.pusbackRightCheck, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        XPSetWidgetProperty(self.pusbackRightCheck, xpProperty_Enabled, rotation_enabled)
        
        # Tow checkbox
        XPCreateWidget(x+90, y-40, x+130, y-60, 1, 'Tow', 0, window, xpWidgetClass_Caption)
        self.pusbackTow = XPCreateWidget(x+120, y-40, x+130, y-60, 1, "", 0, window, xpWidgetClass_Button)
        XPSetWidgetProperty(self.pusbackTow, xpProperty_ButtonType, xpRadioButton)
        XPSetWidgetProperty(self.pusbackTow, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        
        y-= 20
        
        # Push back manual mode
        XPCreateWidget(x+10, y-40, x+130, y-60, 1, 'Drive tug manually', 0, window, xpWidgetClass_Caption)
        self.pusbackAutopilot = XPCreateWidget(x+120, y-40, x+130, y-60, 1, "", 0, window, xpWidgetClass_Button)
        XPSetWidgetProperty(self.pusbackAutopilot, xpProperty_ButtonType, xpRadioButton)
        XPSetWidgetProperty(self.pusbackAutopilot, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        
        y-= 10
        
        # Request Button 
        self.pushbackButton = XPCreateWidget(x+20, y-60, x+140, y-80, 1, "REQUEST", 0, window, xpWidgetClass_Button)
        XPSetWidgetProperty(self.pushbackButton, xpProperty_ButtonType, xpPushButton)
        
        # Cancel Button 
        self.pushbackCancelButton = XPCreateWidget(x+20, y-60, x+140, y-80, 1, "CANCEL", 0, window, xpWidgetClass_Button)
        XPSetWidgetProperty(self.pushbackButton, xpProperty_ButtonType, xpPushButton)
        XPHideWidget(self.pushbackCancelButton)
        
        # Register our widget handler
        self.PusbackWindowHandlerCB = self.PushbackWindowHandler
        XPAddWidgetCallback(self, window, self.PusbackWindowHandlerCB)
        
        pass
    
    def PushbackWindowHandler(self, inMessage, inWidget, inParam1, inParam2):
        if (inMessage == xpMessage_CloseButtonPushed):
            if (self.pushbackWindow):
                XPHideWidget(self.PusbackWindowWidget)
            return 1

        # Handle any button pushes
        if (inMessage == xpMsg_PushButtonPressed):

            if (inParam1 == self.pushbackButton):
                self.PushBack('Requested')
                return 1
            elif (inParam1 == self.pushbackCancelButton ):
                self.PushBack('Stop', True)
                return 1
        return 0
    
    def CreateReFuelWindow(self, x, y, w, h):
        # Get number of fuel tanks
        self.nFuelTanks = self.acf.nFuelTanks.value
        
        x2 = x + w
        y2 = y - h - self.nFuelTanks * 20 - 20
        Buffer = "Request Refuel"
        
        # Create the Main Widget window
        self.ReFuelWindowWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,0 , xpWidgetClass_MainWindow)
        
        # Create the Sub window
        subw = XPCreateWidget(x+10, y-30, x2-20 + 10, y2+40, 1, "" ,  0, self.ReFuelWindowWidget , xpWidgetClass_SubWindow)
        # Set the style to sub window
        XPSetWidgetProperty(subw, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)
        
        y-= 10
        
        # Add Close Box decorations to the Main Widget
        XPSetWidgetProperty(self.ReFuelWindowWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        
        self.reFuelTankInput = []
        self.reFuelTankLabel = []
        total = self.acf.fuelTotal.value
        ratio = self.acf.tankRatio.value
        
        XPCreateWidget(x+20, y-20, x+40, y-42, 1, 'Tank #', 0, self.ReFuelWindowWidget, xpWidgetClass_Caption)
        XPCreateWidget(x+70, y-20, x+120, y-42, 1, 'Loaded (lb)', 0, self.ReFuelWindowWidget, xpWidgetClass_Caption)
        XPCreateWidget(x+195, y-20, x+250, y-42, 1, 'Request (lb)', 0, self.ReFuelWindowWidget, xpWidgetClass_Caption)
        
        # Draw tank input 
        for i in range(self.nFuelTanks):
            XPCreateWidget(x+30, y-46, x+40, y-54, 1, '%i' % (i+1), 0, self.ReFuelWindowWidget, xpWidgetClass_Caption)
            # tank label
            tankLabel = XPCreateWidget(x+70, y-40, x+130, y-62, 1, 'qty ', 0, self.ReFuelWindowWidget, xpWidgetClass_TextField)
            XPSetWidgetProperty(tankLabel, xpProperty_TextFieldType, xpTextEntryField)
            XPSetWidgetProperty(tankLabel, xpProperty_Enabled, 0)
            
            # tank  total label
            max = total * ratio[i] * c.KG2LB
            XPCreateWidget(x+130, y-40, x+180, y-62, 1, '/ %.0f ' % max, 0, self.ReFuelWindowWidget, xpWidgetClass_Caption)
            
            tankInput = XPCreateWidget(x+190, y-40, x+250, y-62, 1, '', 0, self.ReFuelWindowWidget, xpWidgetClass_TextField)
            XPSetWidgetProperty(tankInput, xpProperty_TextFieldType, xpTextEntryField)
            XPSetWidgetProperty(tankInput, xpProperty_Enabled, 1)
            y -= 20
            self.reFuelTankInput.append(tankInput)
            self.reFuelTankLabel.append(tankLabel)
        
        # TOTALS
        y -= 10
        XPCreateWidget(x+20, y-46, x+40, y-54, 1, 'TOTAL: ', 0, self.ReFuelWindowWidget, xpWidgetClass_Caption)
        # tank label
        self.reFuelTankTotal = XPCreateWidget(x+70, y-40, x+130, y-62, 1, 'qty ', 0, self.ReFuelWindowWidget, xpWidgetClass_TextField)
        XPSetWidgetProperty(self.reFuelTankTotal, xpProperty_TextFieldType, xpTextEntryField)
        XPSetWidgetProperty(self.reFuelTankTotal, xpProperty_Enabled, 0)
            
        # tank  total label
        XPCreateWidget(x+130, y-40, x+280, y-62, 1, '/ %.0f ' % (total *c.KG2LB), 0, self.ReFuelWindowWidget, xpWidgetClass_Caption)
        
        # ETA
        self.reFuelETA = XPCreateWidget(x+20, y-75, x+60, y-93, 1, '', 0, self.ReFuelWindowWidget, xpWidgetClass_Caption)
        
        # TODO: request total    
        #XPCreateWidget(x+190, y-40, x+250, y-62, 1, '', 0, self.ReFuelWindowWidget, xpWidgetClass_TextField)
        #XPSetWidgetProperty(tankInput, xpProperty_TextFieldType, xpTextEntryField)
        #XPSetWidgetProperty(tankInput, xpProperty_Enabled, 0)
        
        # Cancel button
        self.CancelReFuelButton = XPCreateWidget(x+100, y-80, x+200, y-92, 1, "STOP", 0, self.ReFuelWindowWidget, xpWidgetClass_Button)
        XPSetWidgetProperty(self.CancelReFuelButton, xpProperty_ButtonType, xpPushButton)
        
        # Save button
        self.ReFuelButton = XPCreateWidget(x+100, y-80, x+200, y-92, 1, "START PUMP", 0, self.ReFuelWindowWidget, xpWidgetClass_Button)
        XPSetWidgetProperty(self.ReFuelButton, xpProperty_ButtonType, xpPushButton)
        
        # Register our widget handler
        self.ReFuelWindowHandlerCB = self.ReFuelWindowHandler
        XPAddWidgetCallback(self, self.ReFuelWindowWidget, self.ReFuelWindowHandlerCB)
        
        self.ReFuelWindowRefresh()
    
    def ReFuelWindowRefresh(self):
        '''
        Refresh window qty Labels
        '''
        if XPIsWidgetVisible(self.ReFuelWindowWidget):
            tank = self.acf.fuelTanks.value
            total = 0
            for i in range(len(self.reFuelTankLabel)):
                XPSetWidgetDescriptor(self.reFuelTankLabel[i], "%.0f" % (tank[i] * c.KG2LB))
                total += tank[i]
            XPSetWidgetDescriptor(self.reFuelTankTotal, "%.0f" % (total * c.KG2LB))
            
            if self.refuel:
                tofuel = sum(self.refuel)
                if tofuel > 0: 
                    eta = c.stime( tofuel / self.conf.flow * 60)
                    XPSetWidgetDescriptor(self.reFuelETA, "ETA: " + eta)
                else: XPSetWidgetDescriptor(self.reFuelETA, "")
        
    def ReFuelWindowHandler(self, inMessage, inWidget, inParam1, inParam2):
        if (inMessage == xpMessage_CloseButtonPushed):
            if (self.reFuelWindow):
                XPHideWidget(self.ReFuelWindowWidget)
            if self.truck and not self.refuel:
                self.fuelTruck('go')
            return 1

        # Handle any button pushes
        if (inMessage == xpMsg_PushButtonPressed):
            if (inParam1 == self.ReFuelButton):
                self.Refuel('Start')
                return 1
            if (inParam1 == self.CancelReFuelButton):
                self.Refuel('Stop', True)
        return 0
    
    def RefuelCallback(self, elapsedMe, elapsedSim, counter, refcon):
        '''
        Refuel Callback
        '''
        if self.refuel and sum(self.refuel) > 0:
            #ignore first call
            if elapsedMe > REFUEL_INTERVAL * 4: return REFUEL_INTERVAL
            
            # remove cap and wait
            if not self.acf.fuelCap.value:
                self.acf.fuelCap.value = 1
                return 1
            
            tank = self.acf.fuelTanks.value
            
            for i in range(len(self.refuel)):
                if self.refuel[i] > 0: 
                    break
                
            toFuel = self.conf.flow/60.0*elapsedMe
            if toFuel > self.refuel[i]: 
                toFuel = self.refuel[i]
            
            self.refuel[i]-= toFuel
            tank[i] += toFuel
            
            self.acf.fuelTanks.value = tank
            
            self.ReFuelWindowRefresh()
            # Tank last
            if self.refuel[i] <= 0:
                # tank switch delay
                return 2 
            
            return REFUEL_INTERVAL
        else:
            self.Refuel("Stop")
            return 0

    def PushBack(self, op = "Request", user = False):
        if op == 'Request':
            ## Pushback
            if (not self.pushbackWindow):
                self.CreatePushBackWindow(221, 640, 200, 165)
                self.pushbackWindow = True
            elif (not XPIsWidgetVisible(self.PusbackWindowWidget)):
                XPShowWidget(self.PusbackWindowWidget)
            else:
                XPHideWidget(self.PusbackWindowWidget)
            pass
        elif op == 'Requested':
            XPHideWidget(self.pushbackButton)
            XPShowWidget(self.pushbackCancelButton)

            # Set pushback options                
            buff = []
            XPGetWidgetDescriptor(self.pusbackDistInput, buff, 256)
            self.pusbackDist    = self.float(buff[0])
            if self.pusbackDist < 1: self.pusbackDist = 1
            buff = []
            XPGetWidgetDescriptor(self.pusbackRotInput, buff, 256)
            a = float(buff[0])
            if a < 1: a = 1
            self.pusbackAngle   = abs(a)
            
            right = XPGetWidgetProperty(self.pusbackRightCheck, xpProperty_ButtonState, None)
            if right:
                self.pushbackTurnDir =-1
            else:
                self.pushbackTurnDir = 1
            
            # Push or tow    
            tow = XPGetWidgetProperty(self.pusbackTow, xpProperty_ButtonState, None)
            if tow:
                self.pushbackDir = -1
                self.pushbackTurnDir *= -1
            else:
                self.pushbackDir = 1
            
            # Manual mode
            autopilot = XPGetWidgetProperty(self.pusbackAutopilot , xpProperty_ButtonState, None)
            if autopilot:
                self.conf.tug.autopilot = False
            else:
                self.conf.tug.autopilot = True
            
            # Clear other actions
            objects = [self.fuelTruck, self.stairsC, self.gpuTruck]
            for obj in objects: obj('go')
            self.tugTruck('come')
            self.tug.animEndCallback = self.pushBackReady
            #self.pushBackReady()
        
        elif op == 'Ready':
            if (self.acf.pbrake.value):
                if self.conf.tug.autopilot:
                    XPLMSpeakString('%s Push back ready, please release park brakes' % self.tailnum)
                else:
                    XPLMSpeakString('Push back ready, please release park brakes, and use the throttle to control the tug gas. Use park brakes to finalize the operation.')
            else:
                if self.conf.tug.autopilot:
                    XPLMSpeakString('%s Starting pushback.' % self.tailnum)
                else:
                     XPLMSpeakString('Push back ready, please use the throttle to control the tug gas. Use park brakes to finalize the operation.')
            
            self.pusbackStatus = False
            self.pusbackWaitBrakes = True
            self.pusbackInitPos = self.acf.get()
            self.pusbackToPos = self.acfP(0,-30)
            XPLMSetFlightLoopCallbackInterval(self, self.PushbackCB, -1, 0, 0)
            pass

        elif op == 'Start':
            # TO clean
            self.pusbackReference = False
            #erase me
            self.count = 0
            self.pusbackStatus = 'Start'
            # gear distance init
            self.acf.getGearcCoord(1)
            
            if self.acf.gearDist > 3:
                self.pushbackMaxSpeed = 4
            else:
                # walking speed
                self.pushbackMaxSpeed = 3
        
            self.pusbackWaitBrakes = False
            
            # Overrides
            if self.conf.tug.autopilot:
                self.acf.headingOverride.value = 1
                self.acf.artstabOverride.value = 1
                self.acf.disableNoseWheelTiller()
            else:
                self.acf.brakeOverride.value = 1
                self.acf.throttleOverride.value = 1
                self.pusbackStatus = 'Autopilot'
                print "MANUAL"
            
            # Center yoke
            self.acf.yokeHeading.value = 0.0
            
            self.pushbackTime   = 0.0
            self.mypsi = 0.0
            pass
        elif op == 'Stop':
            XPLMSetFlightLoopCallbackInterval(self, self.PushbackCB, 0, 0, 0)
            if self.pushbackWindow:
                XPHideWidget(self.pushbackCancelButton)
                XPShowWidget(self.pushbackButton)
            if user: 
                XPLMSpeakString('%s Push back advorted' % self.tailnum)
            else :
                XPLMSpeakString('%s Push back finalized' % self.tailnum)
            
            # Unset overrides
            self.acf.brakeOverride.value = 0
            self.acf.throttleOverride.value = 0
            self.acf.headingOverride.value = 0
            self.acf.artstabOverride.value = 0
            if self.conf.tug.autopilot:
                self.acf.enableNoseWheelTiller()
            if self.tug:
                self.tug.animEndCallback = False
                self.tugTruck('go')
        
    def pushBackCallback(self, elapsedMe, elapsedSim, counter, refcon):
        '''
        Pushback Floop Callback
        '''
        # do nothing if sim is paused
        if self.paused.value: return 1

        # Wait for break release
        if (self.acf.pbrake.value):
            if (not self.pusbackWaitBrakes):
                self.acf.brakeOverride.value = 0
                self.PushBack('Stop', True)
                return 0
            else:
                # wait for release
                return -1
        
        # Start push back
        if not self.pusbackStatus:
            self.PushBack('Start')
            self.pushbackTime = elapsedSim
        
        maxSpeed = self.pushbackMaxSpeed
        gspeed   = self.acf.groundspeed.value
        
        #Overspeed
        if self.conf.tug.autopilot and gspeed > (maxSpeed * 1.5): 
            self.PushBack('Stop', True)
            return 0
        
        # detect reverse direction
        if self.pushbackDir > 0: 
            if abs(c.shortHdg(self.acf.psi.value, self.acf.hpath.value)) < 90: gspeed *= -1
        elif abs(c.shortHdg(self.acf.psi.value, self.acf.hpath.value)) > 90: gspeed *= -1 
        
        if self.pusbackStatus == 'Start':

            dist        = self.acf.getPointDist(self.pusbackInitPos)
            targetSpeed = sin(3*(self.pusbackDist - dist)/self.pusbackDist) * maxSpeed
            init        = self.pusbackDist
            
            x = c.limit((self.pusbackDist - dist)/self.pusbackDist)
            
            if x > 0.5:
                targetSpeed = (1-0.9*x**4) * maxSpeed
            else:
                targetSpeed  =  (1-(1-x)**8) * maxSpeed
            
            dist += self.acf.gearDist
            
            # maintain heading
            dev = c.limit(c.shortHdg(self.acf.psi.value, self.pusbackInitPos[4])/10)
            self.acf.yokeHeading.value = -dev**3
            
            if DEBUG and (self.count %30) == 0:
                print "init: %f, psi: %f, short: %f, dev: %f" % (self.pusbackInitPos[4], self.acf.psi.value, c.shortHdg(self.acf.psi.value, self.pusbackInitPos[4]) ,  dev)
            
        ## Rotation  
        elif self.pusbackStatus == 'Rotate':
            # rotation speed
            rotation    = self.pusbackAngle
            # add rotation speed
            gspeed      += abs(self.acf.gearDist * self.acf.rotation.value)
            init        = rotation
            dist        = abs(init - c.fullHdg(self.acf.get()[4], (self.pusbackInitPos[4] + rotation) %360))
            
            x = c.limit((rotation - dist)/rotation)
            # Slow down GA
            if self.acf.gearDist < 3: x *= 0.04
            if x > 0:
                targetSpeed = (x**0.3-0.3*x) * maxSpeed
            else:
                targetSpeed = 0.0
                
            if not self.pusbackReference:
                self.pusbackReference = self.acf.get()
                if DEBUG:
                    print "TURN"
        
            turnRatio = c.limit(self.acf.getPointDist(self.pusbackReference) / self.acf.gearDist)
            if turnRatio < 0: turnRatio = 0
            self.acf.yokeHeading.value = (turnRatio**2) * self.pushbackTurnDir
            # Finalize rotation
            rleft = rotation - dist
            if rleft < 0:
                self.PushBack('Stop', True)
                return 0
            if rleft < 15:
                self.acf.yokeHeading.value = (rleft/15)**0.8 * self.pushbackTurnDir
            
        ## Pushback phase change
        if self.conf.tug.autopilot and dist + 0.1 > init:
            if  self.pusbackStatus == 'Start':
                if self.pusbackAngle > 0:
                    self.pusbackStatus = 'Rotate'
                else: self.PushBack('Stop')
            elif self.pusbackStatus == 'Rotate':
                self.PushBack('Stop')
                return 0
            
        # Accelerate aircraft
        if (elapsedMe < 1):
            power = self.conf.tpower
            self.count += 1
            if self.conf.tug.autopilot:
                x = c.limit((targetSpeed - gspeed)/maxSpeed)
                if DEBUG and (self.count %30) == 0:print x
                if targetSpeed > gspeed:
                    # Gas curve
                    power *= x**0.5
                else:
                    # Brakes (aprox maxPower/4)
                    power *= 0.25*x**3
                    if DEBUG and (self.count %30) == 0:print "brake"
            else:
                # Let the user control the throttle
                power *=  self.acf.throttle.value[0]
                # reversers
                self.pushbackDir = ( 1 - self.acf.reversers.value[0] * 2)
                gspeed = abs(self.acf.gearDist * self.acf.rotation.value) + self.acf.groundspeed.value
                pass

            # Debug
            if DEBUG and (self.count %30) == 0: 
                stime = c.stime(elapsedSim - self.pushbackTime)
                print '%s distance: %f/%f, speed: %f, targetSpeed: %f, power: %.0f' % (stime, dist, init, gspeed, targetSpeed, power/self.conf.tpower *100)
            
            # Add power to plane
            drag = self.conf.tpower * gspeed/maxSpeed*0.25
            power -= drag
            a = radians(self.acf.psi.value) + 180 % 360
            h = power / (self.acf.m_total.value + self.conf.tweight)* elapsedMe
            
            # substract angular vel
            #av = sin(radians(self.acf.yokeHeading.value * self.acf.gearMaxSteer.value)) /self.acf.gearDist * h
            #yv = cos(radians(self.acf.yokeHeading.value * self.acf.gearMaxSteer.value)) * h
            av = sin(radians(self.mypsi)) /self.acf.gearDist * h
            yv = cos(radians(self.mypsi)) * h
            
            self.acf.rotation.value -= av * self.pushbackDir
            self.acf.vx.value -= cos(a) * yv * self.pushbackDir
            self.acf.vz.value -= sin(a) * yv * self.pushbackDir
            
            if DEBUG and (self.count %30) == 0: 
                print "av: %f, xv: %f, yv: %f" % (self.acf.rotation.value, self.acf.vx.value,  self.acf.vz.value)
                print "power: %f, drag: %f, av: %f, yv: %f" % (power, drag, av, yv)
                #print "psi: %f, beta: %f, diff: %f" % (self.acf.psi.value, self.acf.hpath.value, c.shortHdg(self.acf.psi.value, self.acf.hpath.value))
        
        if self.tug:
            # Stick tug to aircraft
            gear = self.acf.getGearcCoord(0)
            ## test slow
            #psi = self.acf.yokeHeading.value * self.acf.gearMaxSteer.value
            #self.acf.yokeHeading = self.acf.y
            self.mypsi +=  ((self.acf.tire_steer_act.value[0] - self.mypsi) * 0.8 * elapsedMe)
            psi = self.mypsi
            pos  = self.acf.getPointAtHdg(self.conf.tgearDist, psi, gear)
            self.tug.setPos(pos, True)
            self.tug.psi += psi
        
        return -1
    
    def Refuel(self, op = 'Start', user = False):
        """
        Manages refueling actions
        """
        if op == 'Request':
            self.fuelTruck('come')
            if (not self.reFuelWindow):
                self.CreateReFuelWindow(221, 640, 290, 105)
                self.reFuelWindow = True
            elif (not XPIsWidgetVisible(self.ReFuelWindowWidget)):
                XPShowWidget(self.ReFuelWindowWidget)
            else:
                XPHideWidget(self.ReFuelWindowWidget)
        elif op == 'Stop':
            if user:
                XPLMSpeakString('%s Refuelling canceled' % self.tailnum)
            else:
                XPLMSpeakString('%s Refuelling compleated' % self.tailnum)
            self.refuel = False;
            if self.truck:
                self.fuelTruck('go')
            XPLMSetFlightLoopCallbackInterval(self, self.RefuelFloopCB, 0, 0, 0)
            if self.reFuelWindow:
                XPSetWidgetDescriptor(self.reFuelETA, "")
                XPHideWidget(self.CancelReFuelButton)
                XPShowWidget(self.ReFuelButton)
            self.acf.fuelCap.value = 0
        elif op == 'Start':
            data = []
            total = self.acf.fuelTotal.value
            ratio = self.acf.tankRatio.value
            curr = self.acf.fuelTanks.value
            for i in range(self.nFuelTanks):
                buff = []
                XPGetWidgetDescriptor(self.reFuelTankInput[i], buff, 256)
                qty = self.float(buff[0]) * c.LB2KG
                max = total * ratio[i] - curr[i] 
                if qty > max:
                    qty = max
                    XPSetWidgetDescriptor(self.reFuelTankInput[i], "%.0f" % (qty * c.KG2LB))  
                data.append(qty)
            self.refuel = data
            XPHideWidget(self.ReFuelButton)
            XPShowWidget(self.CancelReFuelButton)
            
            if self.truck and not self.truck.visible:
                self.truck.show()
            
            XPLMSpeakString('%s Starting refuel' % self.tailnum)
            XPLMSetFlightLoopCallbackInterval(self, self.RefuelFloopCB, 3, 1, 0)
            pass

    def pushBackReady(self):
        self.PushBack('Ready')
        pass

    def float(self, string):
        # try to convert to float or return 0
        try: 
            val = float(string)
        except ValueError:
            val = 0.0
        return val
    
    '''
    Object animations
    '''
    
    def fuelTruck(self, op):
        '''
        Controls Fuel truck
        '''
        if not self.truck or not self.truck.enabled:
            self.truck = SceneryObject(self, self.conf.obj.truck)
            self.lop = ''
        
        init = self.acfP(84, 40)
        
        path = [(self.acfP(15, 7), 6),
                (self.acfP(12, 18), 2),
               ]
        backcourse = [(self.acfP(3, 28), 3), 
                      (init, 6)
                      ]
        if  op == 'come' != self.truck.lop:
            self.truck.setPos(init, True)
            self.truck.animate(path, False)
            self.truck.show()
        elif op == 'go' and self.truck.lop == 'come':
            self.truck.animate(backcourse, False)
        self.truck.lop = op
        
    def tugTruck(self, op):
        '''
        Controls Tug object
        '''
        if not self.tug or not self.tug.enabled:
            self.tug = SceneryObject(self, self.conf.obj.tug)
            self.lop = ''
                    
        gear = self.acf.getGearcCoord(self.conf.tgearDist)
        
        path = [ (self.acf.getPointAtHdg(6, 0, gear), 5),
                (self.acf.getPointAtHdg(10 + self.conf.tgearDist, 0, gear), self.conf.tgearDist),
                (gear, 5, self.acf.psi.value)
              ]
        backcourse = [(self.acf.getGearcCoord(10 + self.conf.tgearDist) , 5),
                      (self.acf.getPointAtHdg(20, 50), 2),
                       (self.acf.getPointAtHdg(50, 94), 3),
                       (self.acf.getPointAtHdg(64, 130), 3)
                     ]
        
        if  op == 'come' != self.tug.lop:
            self.tug.setPos(self.acf.getPointAtHdg(100, 270), True)
            self.tug.psi = self.tug.getHeading(self.tug.getPos(), self.acf.get()) + 30 %360
            self.tug.animate(path, False)
            self.tug.show()
        elif op == 'go' != self.tug.lop == 'come':
            self.tug.animate(backcourse, False)
        self.tug.lop = op
    
    def acfP(self, x, z):
        'Shorcut for 2d points'
        return self.acf.getPointAtRel([x, 0.0, z, 0.0, 0.0])
    
    def stairsC(self, op):
        '''
        Controls Stairs
        '''
        
        if not self.stairs or not self.stairs.enabled:
            self.stairs = SceneryObject(self, self.conf.obj.stairs)
            self.lop = ''
        
        door = self.acf.getDoorCoord(0)
        hinv =  door[4] + 90%360
        
        init = self.acfP(-100, 40)
        
        path = [(self.acfP(-30, -20), 5),
                (self.acf.getPointAtHdg(5, hinv, door), 3),
                (door , 2, door[4]),
                ]
        
        backcourse = [(self.acf.getPointAtHdg(6, hinv, door), 3, door[4]),
                      (self.acfP(-30, -20), 5),
                      (init , 5),
                      ]
        
        if op == 'toggle':
            if self.stairs.lop == 'come': op = 'go'
            else: op = 'come'
        
        if  op == 'come' != self.stairs.lop:
            self.stairs.setPos(init, True)
            self.stairs.show()
            self.stairs.animate(path, False)
            self.stairs.animEndCallback = self.buses
        elif op == 'go' and self.stairs.lop == 'come':
            if self.bus:
                self.bus.loop = False
            self.stairs.animate(backcourse, False)
        self.stairs.lop = op
    
    def buses(self):
        '''
        Controls buses
        '''
        if not self.bus or not self.bus.enabled:
            self.bus = SceneryObject(self, self.conf.obj.bus)
        
        door = self.acf.getDoorCoord(20)
        door2 = door[:]
        door2[2] += 4
        init = self.acfP(-80, 40)
        
        path = [(door , 5),
                (door2, 2),
                (door2, 20),
                (init, 5),
                (init, 20),
                ]
        
        self.bus.setPos(init, True)
        self.bus.show()
        self.bus.animate(path, False, True)
    
    def gpuTruck(self, op):
        '''
        Controls gpu truck
        '''
        if not self.gpu or not self.gpu.enabled:
            self.gpu = SceneryObject(self, self.conf.obj.gpu)
            self.lop = ''
        
        init = self.acfP(80, 40)
        pos = self.acfP(2, 19)
        pos2 = self.acfP(12, 20)
        path = [(pos2 , 5),
                (pos, 2),
                ]
        backcourse = [(pos2 , 5),
                      (init, 5),
                      ]
        if op == 'toggle':
            if self.gpu.lop == 'come': op = 'go'
            else: op = 'come'
        if op == 'come' != self.gpu.lop:
            self.gpu.setPos(init, True)
            self.gpu.show()
            self.gpu.animate(path, False)
        elif op == 'go'and self.gpu.lop  == 'come':
            self.gpu.animate(backcourse, False)
        self.gpu.lop = op
        
'''
Includes
'''
class Aircraft:
    '''
    Aircraft data, position and other utilities
    '''
    def __init__(self):
       
        # Fuel
        self.payLoad    = EasyDref('sim/flightmodel/weight/m_fixed')
        self.fuelTanks  = EasyDref('sim/flightmodel/weight/m_fuel[0:9]')
        self.fuelTotal  = EasyDref('sim/aircraft/weight/acf_m_fuel_tot', 'float')
        self.jettison   = EasyDref('sim/flightmodel/weight/m_jettison')
        self.jato       = EasyDref('sim/flightmodel/misc/jato_left')
        self.nFuelTanks = EasyDref('sim/aircraft/overflow/acf_num_tanks(int)')
        self.tankRatio  = EasyDref('sim/aircraft/overflow/acf_tank_rat[0:9]', 'float')
        
        self.fuelCap    = EasyDref('sim/operation/failures/rel_fuelcap(int)')
        
        # Payload
        self.m_empty    = EasyDref('sim/aircraft/weight/acf_m_empty(float)') 
        self.m_total    = EasyDref('sim/flightmodel/weight/m_total(float)')
        self.m_max      = EasyDref('sim/flightmodel/weight/m_total(float)')
        
        #Tail number
        self.tailNumber = EasyDref('sim/aircraft/view/acf_tailnum[0:40]', 'bit')
        
        # local position
        self.lx = EasyDref('sim/flightmodel/position/local_x', 'double')
        self.ly = EasyDref('sim/flightmodel/position/local_y', 'double')
        self.lz = EasyDref('sim/flightmodel/position/local_z', 'double')
        
        # Orientation
        self.q = EasyDref('sim/flightmodel/position/q[0:3]', 'float')
        
        self.theta   = EasyDref('sim/flightmodel/position/theta', 'float')
        self.psi     = EasyDref('sim/flightmodel/position/psi', 'float')
        self.phi     = EasyDref('sim/flightmodel/position/phi', 'float')
        
        # Velocity 
        self.vx = EasyDref('sim/flightmodel/position/local_vx', 'float')
        self.vy = EasyDref('sim/flightmodel/position/local_vy', 'float')
        self.vz = EasyDref('sim/flightmodel/position/local_vz', 'float')
        
        # path heading
        self.hpath = EasyDref('sim/flightmodel/position/hpath', 'float')
        
        # brakes
        self.pbrake = EasyDref('sim/flightmodel/controls/parkbrake', 'float')
        
        # overrides
        self.brakeOverride      = EasyDref('sim/operation/override/override_gearbrake', 'int')
        self.throttleOverride   = EasyDref('sim/operation/override/override_throttles', 'int')
        self.headingOverride    = EasyDref('sim/operation/override/override_joystick_heading', 'int')
        self.rollOverride       = EasyDref('sim/operation/override/override_joystick_roll', 'int')
        self.artstabOverride    = EasyDref('sim/operation/override/override_artstab', 'int')
        self.joyOverride        = EasyDref('sim/operation/override/override_joystick', 'int')
        
        self.throttle = EasyDref('sim/flightmodel/engine/ENGN_thro[0]', 'float')
        self.throttleUse = EasyDref('sim/flightmodel/engine/ENGN_thro_use[0:8]', 'float')
        
        # Ground speed
        self.groundspeed = EasyDref('sim/flightmodel/position/groundspeed', 'float')
        
        # Rotation rate
        self.rotation = EasyDref('sim/flightmodel/position/Rrad', 'float')
        # Rudder deflection
        self.rudder = EasyDref('sim/flightmodel/controls/ldruddef', 'float')
        
        # Gear deflection
        self.yokeHeading = EasyDref('sim/joystick/yolk_heading_ratio', 'float')
        self.yokeRoll    = EasyDref('sim/joystick/yolk_roll_ratio', 'float')
        
        self.tire_steer_act = EasyDref('sim/flightmodel/parts/tire_steer_act[0:1]', 'float')
        
        
        self.gearMaxSteer = EasyDref('sim/aircraft/gear/acf_nw_steerdeg1', 'float')
        self.gearMaxSteer2 = EasyDref('sim/aircraft/gear/acf_nw_steerdeg1', 'float')

        #
        # yoke
        # sim/joystick/yolk_heading_ratio
        #
        self.has_joystic = EasyDref('sim/joystick/has_joystick', 'int')
        
        # Gear position
        # self.gear = EasyDref('sim/aircraft/parts/acf_gear_znodef[0:10]', 'float')
        # self.gear = EasyDref('sim/aircraft/parts/acf_Zarm[0:10]', 'float')
        # self.gear = EasyDref('sim/flightmodel/parts/tire_z_no_deflection[0:10]', 'float')
        self.gear = EasyDref('sim/flightmodel/parts/tire_z_no_deflection[0:10]', 'float')
        
        # Gpu
        self.gpuOn   = EasyDref('sim/cockpit/electrical/gpu_on', 'int')
        #self.gpuAmps = EasyDref('sim/cockpit/electrical/gpu_amps', 'float')
        
        # Door position
        self.doorX = EasyDref('sim/aircraft/view/acf_door_x', 'float')
        self.doorZ = EasyDref('sim/aircraft/view/acf_door_z', 'float')
        
        self.nose_steer = EasyDref('sim/cockpit2/controls/nosewheel_steer_on', 'int')
        
        # joy assignments
        self.joyAssignments = EasyDref('sim/joystick/joystick_axis_assignments[0:100]','int')
        self.gearType = EasyDref('sim/aircraft/parts/acf_gear_type[0:1]', 'int')
        
        self.reversers = EasyDref('sim/cockpit/warnings/annunciators/reverser_on[0:1]', 'int')
        
    def refresh(self):
        # refresh values on acf change
        pass
   
    def disableNoseWheelTiller(self):
        '''
        Disables the nose wheel tiller
        (non-rotation bug workaround)
        '''
        self.assigns = self.joyAssignments.value
        self.assginsBkp = self.assigns[:]
        self.noseWheelTiller = False
        for i in range(100):
            if self.assigns[i] == NOSE_WHEEL_TILLER:
                self.assigns[i] = 0
                self.noseWheelTiller = True
        self.joyAssignments.value = self.assigns
       
    def enableNoseWheelTiller(self):
        if self.noseWheelTiller and self.assginsBkp:
            self.joyAssignments.value = self.assginsBkp
   
    def hasYaw(self):
        '''
        Check if the yaw is assigned to a joystick axis
        '''
        self.assigns = self.joyAssignments.value
        for i in range(100):
            if self.assigns[i] == 3:
                return True
        return False
    
    def getClass(self):
        '''
        Get class by weight
        '''
        w = self.m_max.value * c.KG2LB
        
        if   w > 255000:  self.Class = 'AB'
        elif w > 180000:  self.Class = 'C'
        elif w >  41000:  self.Class = 'D'
        elif w >  12500:  self.Class = 'E'
        elif w >   4500:  self.Class = 'F'
        else: self.Class = 'GA' 
        
        if DEBUG:
            print "%s, empty: %i max: %i class: %s" % (self.tailNumber.value[0], self.m_empty.value * c.KG2LB , self.m_max.value * c.KG2LB, self.Class)
        return self.Class
        
    def get(self):
        # Return a position array suitable for Drawing
        return [self.lx.value, self.ly.value, self.lz.value, self.theta.value, self.psi.value, self.phi.value]
        pass
    
    def getGearcCoord(self, dist = TUG_OFFSET):
        h = self.gear.value
        h.sort()
        self.gearDist = abs(h[0])
        h = h[0]*-1 + dist # tug gear separation
        pos = self.getPointAtHdg(h)
        
        return pos
    
    def getDoorCoord(self, dist = 0):
        pos = [self.doorX.value, 0 ,self.doorZ.value, 0.0, 0.0]
        psi = 90
        if pos[0] > 0: psi = 270
        pos[0] -= dist * pos[0]**0
        # BUG Ivented Y
        pos[2] *= -1
        pos = self.getPointAtRel(pos)
        pos[4] = self.psi.value +psi%360
        
        return pos

    def getPointAtHdg(self, dist, hdg = 0, orig = False):
        '''
        Return a point at a given distance and heading
        BUG: inverted Z and heading
        '''
        if not orig:
            orig = self.get()
            
        a = 90 + hdg + orig[4]
        h = dist
        x = cos(radians(a)) * h
        z = sin(radians(a)) * h
        
        orig = orig[:]
        orig[0] -= x * orig[0]**0
        orig[2] -= z * orig[2]**0
        
        return orig
    
    def getPointAtRel(self, pos, orig = False):
        '''
        Get a point relative to the aircraft or orig
        '''        
        p1 = self.getPointAtHdg(pos[0], 90, orig)
        return self.getPointAtHdg(pos[2], 0, p1)
    
    def getPointDist(self, pos, orig = False):
        if not orig:
            orig = self.get()
        x, y = pos[0] - orig[0], pos[2] - orig[2]
        return (x**2 + y**2)**0.5
    
class SceneryObject:
    '''
    Loads and draws an object in a specified position
    '''
    ProbeRef = XPLMCreateProbe(xplm_ProbeY)
    # Inventory
    objects = []
    drawing = False
    DrawCB = False
    
    def __init__(self, plugin, file, visible = False):
        self.__class__.plugin = plugin
        
        # position
        self.x, self.y, self.z, = 0.0, 0.0, 0.0
        # orientation
        self.theta, self.psi, self.phi = 0.0, 0.0, 0.0
        
        # Queue
        self.queue = []
        # Backup queue for loops
        self._queue = []
        
        self.loop = False
        
        # visible?
        self.visible = visible
        self.floor = 1
        
        # load object
        self.object = XPLMLoadObject(file)
        
        self.lop = 'load'
        
        # Return false on error
        if not self.object:
            print "Can't open file: %s" % file
            self.loaded = False
            self.enabled = False
            return None
        
        self.loaded = True
        self.__class__.objects.append(self) 
        
        self.animEndCallback = False
        
        if not self.drawing:
            self.__class__.DrawCB = self.__class__.DrawCallback
            XPLMRegisterDrawCallback(self.__class__.plugin, self.__class__.DrawCB, xplm_Phase_Objects, 0, 0)
            self.__class__.drawing = True
        
        # Sim pause
        self.paused = EasyDref('sim/time/paused', 'int')
        
        # Main floop
        self.floop = self.floopCallback
        XPLMRegisterFlightLoopCallback(self.__class__.plugin, self.floop, 0, 0)
        self.enabled = True
   
    def animate(self, queue, floor = True, loop = False):
        self._queue,  self.queue = queue[:], queue
        
        self.loop = loop
        
        next = self.queue.pop(0)
        if len(next) == 3:
            to, time, psi = next
            to[4] = psi
        else:
            to, time = next
            to[4] = self.getHeading(self.getPos(), to)
            
        self.MoveTo(to, time, floor)
    
    def getHeading(self, p1, p2):
        # Get heading from point to point
        res = [p2[0] - p1[0], p2[2] - p1[2]]
        
        if res[0] == 0:
            if  res[1] > 0: return 0
            else: return 180
        if res[1] == 0:
            if res[0] > 0: 90
            else: return 270
            
        h = (res[0]**2 + res[1]**2)**0.5
        hdg = fabs(degrees(asin(res[1]/h)))

        #quadrants
        if res[1] < 0:
            if res[0] > 0: hdg = 90 - hdg
            else: hdg = 270 + hdg 
        else:
            if res[0] > 0: hdg = 90 + hdg
            else: hdg = 270 - hdg
        
        return hdg
    
    def MoveTo(self, pos, time, floor = True):
        self.goTo = pos
        self.time = float(time)
        
        self.totHeading =  c.shortHdg(self.psi, self.goTo[4])
        XPLMSetFlightLoopCallbackInterval(self.__class__.plugin, self.floop, ANIM_RATE, 0, 0)    
    
    def floopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        '''
        Cheap Animation callback
        '''
        # do nothing if sim is paused
        if self.paused.value: return 1
        if elapsedMe > ANIM_RATE * 4:
            return ANIM_RATE
        
        elif self.time > ANIM_RATE:
            pos = [self.x, self.y, self.z, self.theta, self.psi, self.phi]
            pos[0] += (self.goTo[0] - pos[0]) / self.time * elapsedMe
            # No vertical animation
            #pos[1] += (self.goTo[1] - pos[1]) / self.time * ANIM_RATE
            pos[2] += (self.goTo[2] - pos[2]) / self.time * elapsedMe
            
            if self.totHeading != 0 and pos[4] != self.goTo[4]:
                a = c.shortHdg(pos[4], self.goTo[4])
                #tohd = (a/self.time * elapsedMe)*3
                tohd = (a * elapsedMe)
                pos[4] += tohd
                pos[4] += 360 
                pos[4] %= 360
                            
            
            self.setPos(pos, True)
            self.time -= elapsedMe
            
            return ANIM_RATE
 
        # Enqueue next
        elif len(self.queue):
            next = self.queue.pop(0)
            if len(next) == 3:
                self.goTo, self.time, psi = next
                self.goTo[4] = psi
            else:
                self.goTo, self.time = next
                self.goTo[4] = self.getHeading(self.getPos(), self.goTo)
                self.totHeading = c.shortHdg(self.psi, self.goTo[4])
            return ANIM_RATE
        
        # end callback
        elif self.animEndCallback: 
            self.animEndCallback()
            return 0
        
        # loop
        elif self.loop: 
            self.queue = self._queue[:]
            return ANIM_RATE
        return 0
    
    @classmethod    
    def DrawCallback(self, inPhase, inIsBefore, inRefcon):
        '''
        Drawing callback
        '''
        for obj in self.objects: 
            pos = obj.x, obj.y, obj.z, obj.theta, obj.psi, obj.phi
            XPLMDrawObjects(obj.object, 1, [pos], 0, 0)
        return 1
    
    def setPos(self, pos, floor = False):
        '''
        Set position: floor = True to stick to the floor
        '''
        if floor:
            self.floor = 0
            info = []
            XPLMProbeTerrainXYZ(self.ProbeRef, pos[0], pos[1], pos[2], info)
            self.x, self.y, self.z = info[1], info[2],info[3]
            self.theta, self.psi, self.phi = info[4], pos[4], info[5]
        else:
            self.x, self.y, self.z, self.theta, self.psi, self.phi = tuple(pos)
    def getPos(self):
        return [self.x, self.y, self.z, self.theta, self.psi, self.phi]
    
    def hide(self):
        '''
        Hide object
        '''
        self.visible = False
    def show(self):
        '''
        Show object
        '''
        self.visible = True
    
    def destroy(self):
        '''
        Destroy object and callbacks
        '''
        self.__class__.objects.remove(self)
        XPLMSetFlightLoopCallbackInterval(self.__class__.plugin, self.floop, ANIM_RATE, 0, 0)    
        XPLMUnregisterFlightLoopCallback(self.__class__.plugin, self.floop, 0)
        XPLMUnloadObject(self.object)
        self.enabled = False
        if len(self.__class__.objects) < 1 and self.drawing:
            self.__class__.drawing = False
            XPLMUnregisterDrawCallback(self.plugin, self.DrawCB, xplm_Phase_Objects, 0, 0)
        self = False

    @classmethod
    def destroyAll(self):
        for obj in self.objects[:]:
            obj.destroy()
        if self.drawing:
            self.drawing = False
            XPLMUnregisterDrawCallback(self.plugin, self.DrawCB, xplm_Phase_Objects, 0, 0)
            

class EasyCommand:
    '''
    Creates a command with an assigned callback with arguments
    '''
    def __init__(self, plugin, command, function, args = False, description =''):
        command = 'xjpc/ground_services/' + command
        self.command = XPLMCreateCommand(command, description)
        self.commandCH = self.commandCHandler
        XPLMRegisterCommandHandler(plugin, self.command, self.commandCH, 1, 0)

        self.function = function
        self.args = args        
        self.plugin = plugin
        # Command handlers
    def commandCHandler(self, inCommand, inPhase, inRefcon):
        if inPhase == 0:
            if self.args:
                if type(self.args).__name__ == 'tuple':
                    self.function(*self.args)
                else:
                    self.function(self.args)
            else:
                self.function()
        return 0
    def destroy(self):
        XPLMUnregisterCommandHandler(self.plugin, self.command, self.commandCH, 1, 0)

class EasyDref:    
    '''
    Easy Dataref access
    
    Copyright (C) 2011  Joan Perez i Cauhe
    '''
    def __init__(self, dataref, type = "float"):
        # Clear dataref
        dataref = dataref.strip()
        self.isarray, dref = False, False
        
        if ('"' in dataref):
            dref = dataref.split('"')[1]
            dataref = dataref[dataref.rfind('"')+1:]
        
        if ('(' in dataref):
            # Detect embedded type, and strip it from dataref
            type = dataref[dataref.find('(')+1:dataref.find(')')]
            dataref = dataref[:dataref.find('(')] + dataref[dataref.find(')')+1:]
        
        if ('[' in dataref):
            # We have an array
            self.isarray = True
            range = dataref[dataref.find('[')+1:dataref.find(']')].split(':')
            dataref = dataref[:dataref.find('[')]
            if (len(range) < 2):
                range.append(range[0])
            
            self.initArrayDref(range[0], range[1], type)
            
        elif (type == "int"):
            self.dr_get = XPLMGetDatai
            self.dr_set = XPLMSetDatai
            self.cast = int
        elif (type == "float"):
            self.dr_get = XPLMGetDataf
            self.dr_set = XPLMSetDataf
            self.cast = float  
        elif (type == "double"):
            self.dr_get = XPLMGetDatad
            self.dr_set = XPLMSetDatad
            self.cast = float
        else:
            print "ERROR: invalid DataRef type", type
        
        if dref: dataref = dref
        self.DataRef = XPLMFindDataRef(dataref)
        if self.DataRef == False:
            print "Can't find " + dataref + " DataRef"
    
    def initArrayDref(self, first, last, type):
        self.index = int(first)
        self.count = int(last) - int(first) +1
        self.last = int(last)
        
        if (type == "int"):
            self.rget = XPLMGetDatavi
            self.rset = XPLMSetDatavi
            self.cast = int
        elif (type == "float"):
            self.rget = XPLMGetDatavf
            self.rset = XPLMSetDatavf
            self.cast = float  
        elif (type == "bit"):
            self.rget = XPLMGetDatab
            self.rset = XPLMSetDatab
            self.cast = float
        else:
            print "ERROR: invalid DataRef type", type
        pass

    def set(self, value):
        if (self.isarray):
            self.rset(self.DataRef, value, self.index, len(value))
        else:
            self.dr_set(self.DataRef, self.cast(value))
            
    def get(self):
        if (self.isarray):
            list = []
            self.rget(self.DataRef, list, self.index, self.count)
            return list
        else:
            return self.dr_get(self.DataRef)
        
    def __getattr__(self, name):
        if name == 'value':
            return self.get()
        else:
            raise AttributeError
    
    def __setattr__(self, name, value):
        if name == 'value':
            self.set(value)
        else:
            self.__dict__[name] = value
