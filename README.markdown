# My X-plane python Scripts Collection

A collection of my X-plane python plugins.

In order to use the plugins you need to install [sandy's python interface](http://www.xpluginsdk.org/python_interface_sdk100_downloads.htm)
Create a folder named **PythonScripts** in your *X-plane/Resources/plugins* folder and move the .py files into.
If you're using windows or an old osx version you must also install [Python 2.6.6](http://www.python.org/download/releases/2.6.6/)

All the scripts are released under the terms of the GNU General Public License.

## Fast Plan - rfinder to FMC

If you don't have time to make your own flight-plans and program the x-plane FMC. You should try this tool.

Just enter your departure and destination airports and FastPlan will find a route using http://rfinder.asalink.net/free/ and program your FMC.

If you have UFMC installed a **to UFMC** button will appear to save the fetched plan to the *Resources/plugins/FJCC_FMC/FlightPlans* folder

### Limitations:
* Routes with more than 100 points doesn't fit the x-plane FMC. FastPlan will try to compress large routes.
* FastPlan doesn't plan climb and descent, Vertical Navigation is on your hands. No SID/STAR.
* The plan should be loaded into the UFMC by hand (loaded not typed :) 
* You need an internet connection :)

### Changes
I realized that x-plane can handle 100 FMS navpoints :)
Auto compression of plans with more than 100 fixes
UFMC support by popular request


## PI_CSV_logger Script

Dataref CVS Logger allows you to log any x-plane dataref values into a CSV (spreadsheet) file to facilitate data analysis.

You can start/stop logging from the plugins menu and specify a different datarefs to log for each plane.

Read and edit the included .ini file to specify dataref values to be logged and get more info.

It can be useful to plane makers and test pilots.

## Weight & Fuel: Profiles and Set by numbers 

Allows storing the current Weight and Fuel in profiles and provides an alternative dialog for setting W&F by numbers (without sliders) 

### Features:

* Per aircraft config.
* Unlimited profiles.
* Can be easily modified to store any kind of dataref into profiles.
* # of tanks auto-detection

### Usage:
Set Weight and Fuel in the Aircraft menu or with the provided W&F dialog.
Go to the plugins menu -> W & Fuel Profiles -> New Profile
Type a name for your profile and click save (click on the default checkbox to load this profile each time you load the plane)

You will find your new profile in W & Fuel Profiles -> Load Profile



(c) 2011 Joan Perez i Cauhe