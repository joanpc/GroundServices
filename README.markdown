# X-Plane Ground Services plugin

Provides ground services with object animations using OpenSceneryX objects.
A great way to have some movement around your plane, and do your push-back and refueling Posted Image

## Provided services
 * PushBack: Selectable distance and rotation, fully automated.
 * Refueling: Request the desired fuel amount for each tank.
 * GPU/Stairs (animation only) the stairs may go to a wrong position if the aircraft door is not correctly defined in the .acf. I din't find any way to simulate the gpu power with the current datarefs Posted Image.


## Features
 * The plugin auto assigns fuel and push-back tugs based on the weight of your plane.
 * Each tug and fuel truck has its own characteristics like fuel rate or power.
 * I've modeled the tug power so it should give some real feel.
 * All objects are unloaded if you're far enough in order to save framerate.


## Installation

You need an updated installation of [OpenSceneryX](http://www.opensceneryx.com/) and Sandy Barbour [x-plane python interface](http://www.xpluginsdk.org/python_interface_sdk100_downloads.htm).

### OpenSceneryX

Install or update [OpenSceneryX](http://www.opensceneryx.com/). Some people are reporting missing objects please update your installation before complaining about missing objects or crashes.

### Python interface

Sandy's python interface requires a python installation in your computer, some OS come with python preinstalled.

#### Windows
window users must install [Python 2.7](http://www.python.org/ftp/python/2.7.2/python-2.7.2.msi), **windows 64bit users should also install the 32bit version**
and then [PythonInterfaceWin27.zip](http://www.xpluginsdk.org/downloads/sdk200/PythonInterfaceWin27.zip)

#### Mac OSX 
Osx comes with python preinstalled but with different versions:

 * **Leopard** 10.5:       outdated python version, install [Python 2.7.2 Mac OS X 32-bit i386/PPC](http://www.python.org/ftp/python/2.7.2/python-2.7.2-macosx10.3.dmg) and then [PythonInterfaceMac27.zip](http://www.xpluginsdk.org/downloads/sdk200/PythonInterfaceMac27.zip)
 * **Snow Leopard** 10.6:  **python 2.6** preinstalled install [PythonInterfaceMac26.zip](http://www.xpluginsdk.org/downloads/sdk200/PythonInterfaceMac26.zip)
 * **Lion** 10.7:          **python 2.7** preinstalled install [PythonInterfaceMac27.zip](http://www.xpluginsdk.org/downloads/sdk200/PythonInterfaceMac27.zip)

### Linux
Check for the your version of python:

     joanpc:~$ python --version
     Python 2.7.1

 * 2.6.x: download [PythonInterfaceLin26.zip](http://www.xpluginsdk.org/downloads/sdk200/PythonInterfaceLin26.zip)
 * 2.7.x: download [PythonInterfaceLin27.zip](http://www.xpluginsdk.org/downloads/sdk200/PythonInterfaceLin27.zip)

### All OSs

If you downloaded a python installer, run-it.

Then copy the contents of the **PythonInterface---.zip** file to your *xPlane/Resources/plugins* directory. It should look like:

    xPlane / Resources / plugins / Pythoninterface.ini
    xPlane / Resources / plugins / Pythoninterface---.xpl

## Plugin installation

Create a directory named **PythonScripts** in your *xPlane/Resources/plugins* folder and copy **PI_GroundServices.py** into it

    xPlane / Resources / plugins / PythonScripts / PI_GroundServices.py

# Notes

### Known bugs 
The rotation of the pushback doesn't work i you don't have a joystick plugged and assigned to the rudder.

### Disclaimer
The plugin is not as finished and feature-rich as I would but it's stable. I had this file sitting around for months without adding new features but it's ready to enjoy. I'll probably add more features when I get more motivation (money sometimes is a good motivations... not always :P). The source is released under the GLP license so feel free to improve-it and send-me your patches.

### Thanks
To Zach De'Cou for sharing his plans of a refueling plugin with me and debugging the plugin.
(the refueling is not yet as complete as he designed)
To ramzzess for donating some objects that the plugin is not using yet.

### Help needed
The original idea was to provide all the objects with the plugin, If you're interested in donating objects to the plugin please contact-me.
We need: fuel trucks, tugs, stairs trucks, gpus, airport buses, cargo loaders, food services... 