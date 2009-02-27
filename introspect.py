#!/usr/bin/python

import dbus

# service (dot notation), path to object (path notation), method 

#bus=dbus.SystemBus()
bus=dbus.SessionBus()
for busname in bus.list_names():
    if busname[0]!=":":
        print "--- %s " % busname
        #bus_obj=bus.get_object(busname,'/org/freedesktop/DBus/Introspectable')
        bus_obj=bus.get_object(busname,'/')
        bus_intf=dbus.Interface(bus_obj,'org.freedesktop.DBus.Introspectable')
        try:
            #print bus_obj.Introspect(dbus_interface='org.freedesktop.DBus.Introspectable')
            print bus_intf.object_path
        except dbus.exceptions.DBusException:
            print "Unable to introspect"


#bus_obj=bus.get_object('org.freedesktop.DBus','/org/freedesktop/DBus')
#print bus_obj.Introspect()
#bus_intf=dbus.Interface(bus_obj,'org.freedesktop.DBus')
