import os
import commands
import gobject
import gtk
import gconf
import dbus
import dbusactions.module
from dbusactions.gladewindow import GladeWindow


class CaptureDialog(GladeWindow):
    def __init__(self,modulePath,parentWidget):
        super(CaptureDialog,self).__init__(os.path.join(modulePath,"capturedialog.glade"),"dialogCapture",parentWidget)
        # Set up list columns
        crt=gtk.CellRendererToggle()
        crt.set_active(True)
        crt.connect("toggled",self.on_column_toggled)
        col=gtk.TreeViewColumn("Check",crt,active=0)
        col.set_resizable(False)
        self.propView.append_column(col)
        col=gtk.TreeViewColumn("Property",gtk.CellRendererText(),text=1)
        self.propView.append_column(col)
        # Set up storage model
        self.propList=gtk.ListStore(gobject.TYPE_BOOLEAN,gobject.TYPE_STRING)
        self.propView.set_model(self.propList)        
        # Insert trigger data
        self.propList.append([True,"Foo=0"])
        self.propList.append([False,"Bar=42"])
    
    def on_column_toggled(self,widget,path):
        #self.moduleList.set(self.moduleList.get_iter(path),0,newstate)
        print path
        pass


class ConfigDialog(GladeWindow):
    def __init__(self,module,parentWidget):
        super(ConfigDialog,self).__init__(os.path.join(module.modulePath,"configdialog.glade"),"dialogHwPlugConfig",parentWidget)
        self.module=module
        # Set up list columns
        col=gtk.TreeViewColumn("Trigger",gtk.CellRendererText(),text=0)
        self.triggerView.append_column(col)
        # Set up storage model
        self.triggerList=gtk.ListStore(gobject.TYPE_STRING)
        self.triggerView.set_model(self.triggerList)        
        # Insert trigger data
        for t in module.triggers:
            self.triggerList.append([t.name])
    
    def on_btnOk_clicked(self,widget):
        self.dialogHwPlugConfig.destroy()

    def on_triggerView_cursor_changed(self,widget):
        #self.triggerView.get_cursor()[0][0]
        self.btnDel.set_sensitive(True)

    def on_btnAdd_clicked(self,widget):
        capturedlg=CaptureDialog(self.module.modulePath,self.dialogHwPlugConfig)
        result=capturedlg.dialogCapture.run()
        capturedlg.dialogCapture.destroy()
        print result
    
    def on_btnDel_clicked(self,widget):
        print self.triggerView.get_cursor()[0][0]


class TriggerData(object):
    def __init__(self,confPath,schemaName):
        self.confPath=confPath
        self.schemaName=schemaName
        self.name=None
        self.conditions=[]
        self.command=None

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
        conf.set_schema(self.confPath,self.schemaName)
    
    def delete(self,conf):
        if conf.dir_exists(self.confPath):
            conf.recursive_unset(self.confPath,gconf.UNSET_INCLUDING_SCHEMA_NAMES)
            conf.remove_dir(self.confPath)
            

class Module(dbusactions.module.Module):
    def __init__(self,moduleParams):
        super(Module,self).__init__(moduleParams)
        self.moduleName = '"Device added" trigger'
        self.iconFilename = "hwplugicon.png"
        self.interfaceList = [('org.freedesktop.Hal.Manager','DeviceAdded')]
        self.configuring = False
        self.triggers = []

    def loadTriggers(self):
        if self.conf.dir_exists(self.confAppKey+"/hwplug"):
            for t in self.conf.all_dirs(self.confAppKey+"/hwplug"):
                self.triggers.append(TriggerData(t,"/schemas"+self.confAppKey+"/hwplug/trigger"))
                self.triggers[-1].load(self.conf)

    def isConfigurable(self):
        return True
    
    def configureDialog(self,parentWidget):
        cfgdlg=ConfigDialog(self,parentWidget)
        cfgdlg.dialogHwPlugConfig.run()
        cfgdlg.dialogHwPlugConfig.destroy()

    def dbusSystemEvent(self, *args, **keywordArgs):
        # Argument 0: Object name of new device
        deviceName=args[0]
        # Get object properties
        device=self.systemBus.get_object('org.freedesktop.Hal',deviceName)
        deviceIntf=dbus.Interface(device,dbus_interface='org.freedesktop.Hal.Device')
        if self.configuring:
            pass
        else:
            if deviceIntf.PropertyExists("serial.device"):
                if deviceIntf.PropertyExists("info.parent"):
                    parentDeviceName=deviceIntf.GetPropertyString("info.parent")
                    parentDevice=self.systemBus.get_object('org.freedesktop.Hal',parentDeviceName)
                    parentDeviceIntf=dbus.Interface(parentDevice,dbus_interface='org.freedesktop.Hal.Device')
                    if parentDeviceIntf.PropertyExists("usb.vendor_id") and parentDeviceIntf.PropertyExists("usb.product_id") and \
                        parentDeviceIntf.GetPropertyInteger("usb.vendor_id")==4292 and parentDeviceIntf.GetPropertyInteger("usb.product_id")==60000:
                        cmd="/home/sts/source/gpslog-downloader/src/gpslog-downloader.py -d %s" % deviceIntf.GetPropertyString("serial.device")
                        self.logger.debug("Executing %s" % cmd)
                        result=commands.getstatusoutput(cmd)
