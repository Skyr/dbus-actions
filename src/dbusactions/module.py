# DBus-Actions - a tray application containing modules listening to dbus events
# Copyright (C) 2009 by Stefan Schlott
# Published under the GNU Public License V2 (GPL-2)

import os
import logging 
import dbus


class ModuleParams(object):
    def __init__(self,modulePath,confAppKey,conf,updateModuleStatuses,systemBus,sessionBus):
        self.modulePath=modulePath
        self.confAppKey = confAppKey
        self.conf = conf
        self.updateModuleStatuses=updateModuleStatuses
        self.systemBus=systemBus
        self.sessionBus=sessionBus

class Module(object):
    def __init__(self,moduleParams):
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
        return False
    
    def configureDialog(self,parentWidget):
        pass

    def activate(self):
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
        pass
    
    def dbusSessionEvent(self, *args, **keywordArgs):
        pass
