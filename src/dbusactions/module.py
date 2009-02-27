# DBus-Actions - a tray application containing modules listening to dbus events
# Copyright (C) 2009 by Stefan Schlott
# Published under the GNU Public License V2 (GPL-2)

import os
import logging 
import dbus

""" 
This pyhton module contains the base class for all dbus-actions modules.
New modules have to...
- be located in a subdirectory either of /usr/share/dbus-actions/modules
  or $HOME/.dbus-actions/modules
- contain a __init__.py file
- ...which must contain a class called Module
- ...which has to be derived from dbusactions.module.Module
"""

class ModuleParams(object):
    """
    This class contains all parameters needed for the initialization of
    the base Module class. This is for convenience of module programmers:
    This parameter has to be passed opaquely to the module base class.
    If some parameters change (in future versions of dbus-actions), these
    changes are transparent to existing modules.
    """
    def __init__(self,modulePath,confAppKey,conf,updateModuleStatuses,systemBus,sessionBus):
        self.modulePath=modulePath
        self.confAppKey = confAppKey
        self.conf = conf
        self.updateModuleStatuses=updateModuleStatuses
        self.systemBus=systemBus
        self.sessionBus=sessionBus



class Module(object):
    """
    The base class for all dbus-actions modules. Each instance contains
    a number of variables and class instances, which may be used by derived 
    class. The variables are to be treated read-only.
    """
    def __init__(self,moduleParams):
        """
        In your own constructor, you have to set the following variables:
        iconFilename, moduleName, interfaceList.
        The iconFilename is just the filename (without path) - it will be
        loaded from the module's directory.
        interfaceList can be either:
        - empty: All events are captured
        - a list of interface names: All events of the given interface are captured
        - a list of interface-member tuples: Only the given events are captured
        """
        self.isActive = False
        self.updateModuleStatuses = moduleParams.updateModuleStatuses
        self.confAppKey = moduleParams.confAppKey
        self.conf = moduleParams.conf
        self.modulePath = moduleParams.modulePath
        self.systemBus = moduleParams.systemBus
        self.sessionBus = moduleParams.sessionBus
        self.logger = logging.getLogger("Module")
        # Set in overridden constructor!
        self.iconFilename = None
        self.moduleName = "Abstract module"
        self.interfaceList = []

    def getModuleName(self):
        return self.moduleName

    def getIconName(self):
        if self.iconFilename!=None:
            return os.path.join(self.modulePath,self.iconFilename)
        return None

    def isConfigurable(self):
        """
        Returns false by default. Override this method if you have implemented
        configureDialog as well.
        """
        return False
    
    def configureDialog(self,parentWidget):
        """
        If your module has a configure dialog: Override this method and 
        call it here (in a modal way).
        """
        pass

    def activate(self):
        """
        Activate module. This is called from the main config dialog (when the
        module is enabled). If (for some reason) you have to activate the
        module yourself, you can call this method as well.
        """
        if self.isActive:
            return
        self.isActive = True
        if len(self.interfaceList)>0:
            for intf in self.interfaceList:
                if type(intf)==list or type(intf)==tuple:
                    self.logger.debug("Module.activate for dbus method %s.%s" % (intf[0],intf[1]))
                    self.systemBus.add_signal_receiver(self.dbusSystemEvent,dbus_interface=intf[0],signal_name=intf[1])
                    self.sessionBus.add_signal_receiver(self.dbusSessionEvent,dbus_interface=intf[0],signal_name=intf[1])
                else:
                    self.logger.debug("Module.activate for dbus interface %s" % intf)
                    self.systemBus.add_signal_receiver(self.dbusSystemEvent,dbus_interface=intf,message_keyword='dbus_message')
                    self.sessionBus.add_signal_receiver(self.dbusSessionEvent,dbus_interface=intf,message_keyword='dbus_message')
        else:
            self.logger.debug("Module.activate for all dbus messages")
            self.systemBus.add_signal_receiver(self.dbusSystemEvent,interface_keyword='dbus_interface', member_keyword='member')
            self.sessionBus.add_signal_receiver(self.dbusSessionEvent,interface_keyword='dbus_interface', member_keyword='member')
        self.updateModuleStatuses()
        self.logger.debug("%s activated" % self.moduleName)
    
    def deactivate(self):
        """
        Deactivate module. This is called from the main config dialog (when the
        module is disabled). If (for some reason) you have to deactivate the
        module yourself, you can call this method as well.
        """
        if not self.isActive:
            return
        self.isActive = False
        if len(self.interfaceList)>0:
            for intf in self.interfaceList:
                if type(intf)==list or type(intf)==tuple:
                    self.logger.debug("Module.deactivate for dbus method %s.%s" % (intf[0],intf[1]))
                    self.systemBus.remove_signal_receiver(self.dbusSystemEvent,dbus_interface=intf[0],signal_name=intf[1])
                    self.sessionBus.remove_signal_receiver(self.dbusSessionEvent,dbus_interface=intf[0],signal_name=intf[1])
                else:
                    self.logger.debug("Module.deactivate for dbus interface %s" % intf)
                    self.systemBus.remove_signal_receiver(self.dbusSystemEvent,dbus_interface=intf)
                    self.sessionBus.remove_signal_receiver(self.dbusSessionEvent,dbus_interface=intf)
        else:
            self.logger.debug("Module.deactivate for all dbus messages")
            self.systemBus.remove_signal_receiver(self.dbusSystemEvent)
            self.sessionBus.remove_signal_receiver(self.dbusSessionEvent)
        self.updateModuleStatuses()
        self.logger.debug("%s deactivated" % self.moduleName)

    def dbusSystemEvent(self, *args, **keywordArgs):
        """
        Called for matching events on the system bus.
        The parameters are passed 1:1 from the dbus interface, thus they vary
        depending on your capture selector (the interfaceList variable initialized
        in your constructor). args are the parameters of the message, thus always
        being message-dependant. kwargs is an associative array containing the
        keywords of the notification and is thus dependant on the capture mode:
        Capturing all events (interfaceList empty):
        kwargs strings in the keys dbus_interface and member
        Capturing events of a certain interface:
        kwargs contains a dbus.lowlevel.SignalMessage object in the dbus_message key
        Capturing a specific member:
        The kwargs array is empty
        """
        pass
    
    def dbusSessionEvent(self, *args, **keywordArgs):
        """
        Called for matching events on the session bus.
        Same parameters as dbusSystemEvent.
        """
        pass
