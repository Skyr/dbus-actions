import os
import commands
import gobject
import gtk
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
    def __init__(self,modulePath,parentWidget):
        super(ConfigDialog,self).__init__(os.path.join(modulePath,"configdialog.glade"),"dialogHwPlugConfig",parentWidget)
        self.modulePath=modulePath
        # Set up list columns
        col=gtk.TreeViewColumn("Trigger",gtk.CellRendererText(),text=0)
        self.triggerView.append_column(col)
        # Set up storage model
        self.triggerList=gtk.ListStore(gobject.TYPE_STRING)
        self.triggerView.set_model(self.triggerList)        
        # Insert trigger data
        self.triggerList.append(["Foo"])
        self.triggerList.append(["Bar"])
    
    def on_btnOk_clicked(self,widget):
        self.dialogHwPlugConfig.destroy()

    def on_triggerView_cursor_changed(self,widget):
        #self.triggerView.get_cursor()[0][0]
        self.btnDel.set_sensitive(True)

    def on_btnAdd_clicked(self,widget):
        capturedlg=CaptureDialog(self.modulePath,self.dialogHwPlugConfig)
        capturedlg.dialogCapture.run()
        capturedlg.dialogCapture.destroy()
    
    def on_btnDel_clicked(self,widget):
        print self.triggerView.get_cursor()[0][0]


class Module(dbusactions.module.Module):
    def __init__(self,moduleParams):
        super(Module,self).__init__(moduleParams)
        self.moduleName = '"Device added" trigger'
        self.iconFilename = "hwplugicon.png"
        self.interfaceList = [('org.freedesktop.Hal.Manager','DeviceAdded')]
        self.configuring = False

    def isConfigurable(self):
        return True
    
    def configureDialog(self,parentWidget):
        cfgdlg=ConfigDialog(self.modulePath,parentWidget)
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
