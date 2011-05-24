# My X-plane python Scripts Collection

A collection of my X-plane python plugins.

## Fast Plan - rfinder to FMC

If you don't have time to make your own flight-plans and program the x-plane FMC. You should try this tool.

Just enter your departure and destination airports and FastPlan will find a route using http://rfinder.asalink.net/free/ and program your FMC.

### Limitations:
* Routes with more than 100 points doesn't fit the x-plane FMC. FastPlan will try to compress large routes.
* FastPlan doesn't plan climb and descent, Vertical Navigation is on your hands. No SID/STAR.
* You need an internet connection :)

### Changes
I realized that x-plane can handle 100 FMS navpoints :)
Auto compression of plans with more than 100 fixes  


## PI_CSV_logger Script

Dataref CVS Logger allows you to log any x-plane dataref values into a CSV (spreadsheet) file to facilitate data analysis.

You can start/stop logging from the plugins menu and specify a different datarefs to log for each plane.

Read and edit the included .ini file to specify dataref values to be logged and get more info.

It can be useful to plane makers and test pilots.

## Weight & Fuel Profiles 

Allows storing the current Weight and Fuel in profiles.

### Features:

* Per aircraft config.
* Unlimited profiles.
* Can be easily modified to store any kind of dataref into profiles.

### Usage:
Set Weight and Fuel in the Aircraft menu.
Go to the plugins menu -> W & Fuel Profiles -> New Profile
Type a name for your profile and click save (click on the default checkbox to load this profile each time you load the plane)

You will find your new profile in W & Fuel Profiles -> Load Profile



(c) 2011 Joan Perez i Cauhe