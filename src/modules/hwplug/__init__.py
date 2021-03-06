# DBus-Actions - a tray application containing modules listening to dbus events
# Copyright (C) 2009 by Stefan Schlott
# Published under the GNU Public License V2 (GPL-2)

import os
import commands
import gobject
import gtk
import gconf
import dbus
import dbusactions.module
from dbusactions.gladewindow import GladeWindow


class HardwareProperties(object):
    def __init__(self,deviceName):
        self.deviceName=deviceName
        self.deviceId=deviceName[deviceName.rfind("/")+1:]
        self.properties=[]
    
    def getProperties(self,systemBus):
        device=systemBus.get_object('org.freedesktop.Hal',self.deviceName)
        deviceIntf=dbus.Interface(device,dbus_interface='org.freedesktop.Hal.Device')
        props=deviceIntf.GetAllProperties()
        sortedkeys=props.keys()
        sortedkeys.sort()
        for k in sortedkeys:
            if not type(props[k]) in [dbus.Array,dbus.ByteArray,dbus.Dictionary]: 
                self.properties.append([str(k),str(props[k]),False])

    def propertyMatch(self,prop,val):
        for p in self.properties:
            if p[0]==prop:
                return (p[1]==val)
        return False

    def copyFromTriggerData(self,triggerData):
        for cond in triggerData.conditions:
            c=cond.split("=",1)
            self.properties.append([c[0],c[1],True])
    

class TriggerData(object):
    def __init__(self,schemaName,confBasePath,confPath=None,hwProperties=None):
        assert(confPath!=None or hwProperties!=None)
        self.confPath=confPath
        self.schemaName=schemaName
        self.name=None
        self.conditions=[]
        self.command=None
        if hwProperties!=None:
            self.confPath=confBasePath+"/"+hwProperties.deviceId
            for p in hwProperties.properties:
                if p[2]:
                    self.conditions.append("%s=%s" % (p[0],p[1]))

    def load(self,conf):
        self.name=None
        self.conditions=[]
        self.command=None
        if conf.dir_exists(self.confPath):
            self.name=conf.get_string(self.confPath+"/name")
            self.conditions=conf.get_list(self.confPath+"/conditions",gconf.VALUE_STRING)
            self.command=conf.get_string(self.confPath+"/command")
    
    def store(self,conf):
        conf.set_string(self.confPath+"/name",self.name)
        conf.set_list(self.confPath+"/conditions",gconf.VALUE_STRING,self.conditions)
        conf.set_string(self.confPath+"/command",self.command)
        #TODO: Set schema
        #conf.set_schema(self.confPath,self.schemaName) 
    
    def delete(self,conf):
        if conf.dir_exists(self.confPath):
            conf.recursive_unset(self.confPath,gconf.UNSET_INCLUDING_SCHEMA_NAMES)
            conf.remove_dir(self.confPath)
            

class CaptureDialog(GladeWindow):
    def __init__(self,module,parentWidget):
        super(CaptureDialog,self).__init__(os.path.join(module.modulePath,"capturedialog.glade"),"dialogCapture",parentWidget)
        self.module=module
        # Set up list columns for properties
        crt=gtk.CellRendererToggle()
        crt.set_active(True)
        crt.connect("toggled",self.on_column_toggled)
        col=gtk.TreeViewColumn("Check",crt,active=0)
        col.set_resizable(False)
        self.propView.append_column(col)
        col=gtk.TreeViewColumn("Property",gtk.CellRendererText(),text=1)
        self.propView.append_column(col)
        # Set up storage model for properties
        self.propList=gtk.ListStore(gobject.TYPE_BOOLEAN,gobject.TYPE_STRING)
        self.propView.set_model(self.propList)
        # Set up list columns for hw objects
        col=gtk.CellRendererText()
        self.cbHardware.pack_start(col,True)
        self.cbHardware.add_attribute(col,"text",0)
        # Set up storage model for hw objects
        self.hwList=gtk.ListStore(gobject.TYPE_STRING)
        self.cbHardware.set_model(self.hwList)        
        # At start: No hw
        self.hw=[]
        self.numPropsChecked=0

    def appendHardwareProps(self,hwProps):
        self.hw.append(hwProps)
        self.cbHardware.append_text(self.hw[-1].deviceId)
        if (self.cbHardware.get_active()<0):
            self.cbHardware.set_active(0)
        
    def newHardware(self,deviceName):
        hwProps=HardwareProperties(deviceName)
        hwProps.getProperties(self.module.systemBus)
        self.appendHardwareProps(hwProps)
    
    def on_cbHardware_changed(self,widget):
        self.numPropsChecked=0
        if self.cbHardware.get_active()>=0:
            hwnum=self.cbHardware.get_active()
            self.propList.clear()
            for p in self.hw[hwnum].properties:
                self.propList.append([p[2],"%s=%s" % (p[0],p[1])])
                if p[2]:
                    self.numPropsChecked=self.numPropsChecked+1
        self.btnOk.set_sensitive(self.numPropsChecked>0)
    
    def on_column_toggled(self,widget,path):
        hwnum=self.cbHardware.get_active()
        propnum=int(path)
        newstate=not self.hw[hwnum].properties[propnum][2]
        self.propList.set(self.propList.get_iter(path),0,newstate)
        self.hw[hwnum].properties[propnum][2]=newstate
        if newstate:
            self.numPropsChecked=self.numPropsChecked+1
        else:
            self.numPropsChecked=self.numPropsChecked-1
        self.btnOk.set_sensitive(self.numPropsChecked>0)

    def on_btnOk_clicked(self,widget):
        self.dialogCapture.response(gtk.RESPONSE_OK)


class ConfigDialog(GladeWindow):
    def __init__(self,module,parentWidget):
        super(ConfigDialog,self).__init__(os.path.join(module.modulePath,"configdialog.glade"),"dialogHwPlugConfig",parentWidget)
        self.module=module
        # Set up list columns
        col=gtk.TreeViewColumn("Trigger name",gtk.CellRendererText(),text=0)
        self.triggerView.append_column(col)
        # Set up storage model
        self.triggerList=gtk.ListStore(gobject.TYPE_STRING)
        self.triggerView.set_model(self.triggerList)        
        # Insert trigger data
        for t in self.module.triggers:
            self.triggerList.append([t.name])
    
    def checkButtons(self):
        active=self.triggerView.get_cursor()[0]!=None
        self.btnEdit.set_sensitive(active)
        self.btnDel.set_sensitive(active)
            
    def on_triggerView_cursor_changed(self,widget):
        #self.triggerView.get_cursor()[0][0]
        self.checkButtons()

    def on_btnAdd_clicked(self,widget):
        capturedlg=CaptureDialog(self.module,self.dialogHwPlugConfig)
        moduleActive=self.module.isActive
        self.module.configNewHardware=capturedlg.newHardware
        if not moduleActive:
            self.module.activate()
        if capturedlg.dialogCapture.run()==gtk.RESPONSE_OK:
            newTrigger=TriggerData(self.module.triggerSchemaName,self.module.moduleAppKey,hwProperties=capturedlg.hw[capturedlg.cbHardware.get_active()])
            newTrigger.name=capturedlg.entryRulename.get_text()
            newTrigger.command=capturedlg.entryCmd.get_text()
            newTrigger.store(self.module.conf)
            self.module.triggers.append(newTrigger)
            self.triggerList.append([newTrigger.name])
        if not moduleActive:
            self.module.deactivate()
        self.module.configNewHardware=None
        capturedlg.dialogCapture.destroy()
    
    def on_btnEdit_clicked(self,widget):
        num=int(self.triggerView.get_cursor()[0][0])
        if num>=0 and num<len(self.module.triggers):
            props=HardwareProperties("")
            props.copyFromTriggerData(self.module.triggers[num])
            capturedlg=CaptureDialog(self.module,self.dialogHwPlugConfig)
            capturedlg.appendHardwareProps(props)
            capturedlg.entryRulename.set_text(self.module.triggers[num].name)
            capturedlg.entryCmd.set_text(self.module.triggers[num].command)
            capturedlg.cbHardware.set_sensitive(False)
            capturedlg.propView.set_sensitive(False)
            if capturedlg.dialogCapture.run()==gtk.RESPONSE_OK:
                self.module.triggers[num].name=capturedlg.entryRulename.get_text()
                self.module.triggers[num].command=capturedlg.entryCmd.get_text()
                self.module.triggers[num].store(self.module.conf)
                self.triggerList.set(self.triggerList.get_iter(num),0,self.module.triggers[num].name)
            capturedlg.dialogCapture.destroy()

    def on_btnDel_clicked(self,widget):
        num=int(self.triggerView.get_cursor()[0][0])
        if num>=0 and num<len(self.module.triggers):
            self.triggerList.remove(self.triggerList.get_iter(num))
            self.module.triggers[num].delete(self.module.conf)
            del(self.module.triggers[num])
            self.checkButtons()


class Module(dbusactions.module.Module):
    def __init__(self,moduleParams):
        super(Module,self).__init__(moduleParams)
        self.moduleName = '"Device added" trigger'
        self.iconFilename = "hwplugicon.png"
        self.interfaceList = [('org.freedesktop.Hal.Manager','DeviceAdded')]
        self.configNewHardware = None
        self.triggers = []
        self.triggerSchemaName = "/schemas"+self.confAppKey+"/hwplug/trigger"
        self.moduleAppKey = self.confAppKey+"/hwplug"
        self.loadTriggers()

    def loadTriggers(self):
        if self.conf.dir_exists(self.confAppKey+"/hwplug"):
            for t in self.conf.all_dirs(self.confAppKey+"/hwplug"):
                self.triggers.append(TriggerData(self.triggerSchemaName,self.moduleAppKey,t))
                self.triggers[-1].load(self.conf)
                if self.triggers[-1].name==None:
                    del(self.triggers[-1])

    def isConfigurable(self):
        return True
    
    def configureDialog(self,parentWidget):
        cfgdlg=ConfigDialog(self,parentWidget)
        cfgdlg.dialogHwPlugConfig.run()
        cfgdlg.dialogHwPlugConfig.destroy()

    def dbusSystemEvent(self, *args, **keywordArgs):
        # Argument 0: Object name of new device
        deviceName=args[0]
        if self.configNewHardware:
            self.configNewHardware(deviceName)
        else:
            hwprops=HardwareProperties(deviceName)
            hwprops.getProperties(self.systemBus)
            for trigger in self.triggers:
                match=True
                for cond in trigger.conditions:
                    c=cond.split("=",1)
                    if not hwprops.propertyMatch(c[0],c[1]):
                        match=False
                if match:
                    self.logger.debug("Trigger '%s' matches. Executing '%s'" % (trigger.name,trigger.command))
                    result=commands.getstatusoutput(trigger.command)
                    self.logger.debug("%s" % result[1])
