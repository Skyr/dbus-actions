About
=====

dbus is meant to easily interconnect desktop applications. But sometimes, you
just want some convenience activities in response to some dbus events - but 
there is no simple scripting possibility.

dbus-actions tries to fill this gap. By writing a simple python module, you
can extend dbus-actions with your own custom actions. Some modules for common
applications (new hardware plugged in, dbus message display) are already
included.

dbus-actions shows up on the desktop as single icon in the notification area.
Using a doppeldecker bus as icon seemed obvious (DBus -> Doppeldecker Bus) :-)


Requirements
============

dbus-actions is written in python/gtk an requires the gtk/gnome python
bindings (pyobject, pygtk, dbus-python, gnome-python, gnome-python-extras).


More information
================

More information (parameters, how to write own modules, etc.) can be found
in the src/README file.


Copyright, license
==================

Copyright (C) 2009 by Stefan Schlott

Published under the GNU Public License V2 (GPL-2)

