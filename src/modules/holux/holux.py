import commands
import dbus
import dbusactions.module

class Module(dbusactions.module.Module):
    def __init__(self,moduleParams):
        super(Module,self).__init__(moduleParams)
        self.moduleName = "Holux GPS trigger"
        self.iconFilename = "holuxicon.png"
        self.interfaceList = [('org.freedesktop.Hal.Manager','DeviceAdded')]

    def dbusSystemEvent(self, *args, **keywordArgs):
        deviceName=args[0]
        device=self.systemBus.get_object('org.freedesktop.Hal',deviceName)
        deviceIntf=dbus.Interface(device,dbus_interface='org.freedesktop.Hal.Device')
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
