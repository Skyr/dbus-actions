#!/usr/bin/env python


# Register schemas with: gconftool-2 --install-schema-file gpslog-downloader.schemas

# idVendor: 10c4 = 4292dec
# idProduct: ea60 = 60000dec


import os
import sys
import time
import commands
from optparse import OptionParser
try:
    import pygtk
    pygtk.require("2.0")
except:
    sys.exit(1)
try:
    import gtk
    import gtk.glade
    import gconf
except:
    sys.exit(1)


def findGladeFile(filename):
    fullname=os.path.join("/usr/share/gpslog-downloader",filename)
    if os.path.isfile(fullname):
        return fullname
    fullname=os.path.join("/usr/local/share/gpslog-downloader",filename)
    if os.path.isfile(fullname):
        return fullname
    fullname=os.path.join(os.path.dirname(sys.argv[0]),filename)
    if os.path.isfile(fullname):
        return fullname
    return filename


class SettingsDialog:
    def __init__(self, mainDlg):
        self.mainDlg = mainDlg
        # Set the Glade file
        self.gladefile = findGladeFile("settingsdialog.glade")
        self.wTree = gtk.glade.XML(self.gladefile, "dialogSettings")
        # Autoconnect events
        self.wTree.signal_autoconnect(self)
        # Add each widget as an attribute of object
        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            # make sure we don't clobber existing attributes
            assert not hasattr(self, name)
            setattr(self, name, w)
        # Set default data
        self.dirchooser.set_current_folder(self.mainDlg.dataPath)
        self.entryFilenameTemplate.set_text(self.mainDlg.dataFilenameTemplate)
        self.entryDownloadCmd.set_text(self.mainDlg.downloadCmd)
        self.entryEraseCmd.set_text(self.mainDlg.eraseCmd)
        self.cbEraseOnDevice.set_active(self.mainDlg.eraseOnDevice)
        self.entryDefaultDevice.set_text(self.mainDlg.defaultDevice)
    
    def on_buttonOk_clicked(self, widget):
        self.dialogSettings.hide()
        # Transmit entered data
        self.mainDlg.dataPath=self.dirchooser.get_filename()
        self.mainDlg.dataFilenameTemplate=self.entryFilenameTemplate.get_text()
        self.mainDlg.downloadCmd=self.entryDownloadCmd.get_text()
        self.mainDlg.eraseCmd=self.entryEraseCmd.get_text()
        self.mainDlg.eraseOnDevice=self.cbEraseOnDevice.get_active()
        self.mainDlg.defaultDevice=self.entryDefaultDevice.get_text()
        # Store and apply
        self.mainDlg.storeSettings()
        self.mainDlg.setDefaultValues()
    
    def on_buttonCancel_clicked(self, widget):
        self.dialogSettings.hide()


class ImportDialog:
    """Main dialog"""
    def __init__(self, deviceName):
        self.deviceName=deviceName
        # Set the Glade file
        self.gladefile = findGladeFile("importwindow.glade")
        self.wTree = gtk.glade.XML(self.gladefile, "windowImport")
        # Autoconnect events
        self.wTree.signal_autoconnect(self)
        # Get GConf client
        self.conf = gconf.client_get_default()
        self.confAppKey = "/apps/gpslog-downloader"
        # Add each widget as an attribute of object
        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            # make sure we don't clobber existing attributes
            assert not hasattr(self, name)
            setattr(self, name, w)
        # Set default values
        self.getSettings()
        self.setDefaultValues()

    def getSettings(self):
        self.eraseOnDevice = self.conf.get_bool(self.confAppKey+"/erase_on_device")
        self.downloadCmd = self.conf.get_string(self.confAppKey+"/download_cmd")
        self.eraseCmd = self.conf.get_string(self.confAppKey+"/erase_cmd")
        self.dataPath = self.conf.get_string(self.confAppKey+"/data_path")
        self.dataFilenameTemplate = self.conf.get_string(self.confAppKey+"/data_filename_template")
        self.defaultDevice = self.conf.get_string(self.confAppKey+"/default_device")

    def storeSettings(self):
        self.conf.set_bool(self.confAppKey+"/erase_on_device",self.eraseOnDevice)
        self.conf.set_string(self.confAppKey+"/download_cmd",self.downloadCmd)
        self.conf.set_string(self.confAppKey+"/erase_cmd",self.eraseCmd)
        self.conf.set_string(self.confAppKey+"/data_path",self.dataPath)
        self.conf.set_string(self.confAppKey+"/data_filename_template",self.dataFilenameTemplate)
        self.conf.set_string(self.confAppKey+"/default_device",self.defaultDevice)
    
    def setDefaultValues(self):
        self.cbErase.set_active(self.eraseOnDevice)
        self.filechooser.set_current_folder(self.dataPath)
        dataFilename=time.strftime(self.dataFilenameTemplate)
        self.filechooser.set_current_name(dataFilename)

    def on_windowImport_destroy(self, *args):
        gtk.main_quit()

    def on_buttonConfigure_clicked(self, *args):
        dlg = SettingsDialog(self)
        dlg.dialogSettings.show()

    def on_buttonCancel_clicked(self, *args):
        gtk.main_quit()

    def on_buttonOk_clicked(self, *args):
        if not self.deviceName:
            self.deviceName=self.defaultDevice
        dataFilename=self.filechooser.get_filename()
        exportAndQuit=True
        if os.path.exists(dataFilename):
            if not os.path.isfile(dataFilename):
                return
            dlg = gtk.MessageDialog(parent=self.windowImport,type=gtk.MESSAGE_WARNING,buttons=gtk.BUTTONS_YES_NO)
            dlg.set_title("File exists")
            dlg.set_markup("File %s already exists - overwrite?" % (dataFilename))
            if dlg.run()!=gtk.RESPONSE_YES:
                exportAndQuit=False
        if exportAndQuit:
            # Execute commands
            paramMap = {
                'filename' : "%s" % (dataFilename),
                'device' : "%s" % (self.deviceName),  
            }
            downloadCmd = self.downloadCmd % paramMap 
            eraseCmd = self.eraseCmd % paramMap
            print "Running %s" % (downloadCmd)
            result=commands.getstatusoutput(downloadCmd)
            print "Result: %s" % (result[1])
            if result[0]==0:
                print "Running %s" % (eraseCmd)
                commands.getstatusoutput(eraseCmd)
            else:
                dlg = gtk.MessageDialog(parent=self.windowImport,type=gtk.MESSAGE_ERROR,buttons=gtk.BUTTONS_OK)
                dlg.set_title("Error downloading data")
                dlg.set_markup("Error downloading data:\n%s" % (result[1]))
                dlg.run()
            # Quit application
            gtk.main_quit()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--device", dest="deviceName",
                  help="Device name of GPS device", default=None)
    (options, args) = parser.parse_args()
    dlgImport = ImportDialog(options.deviceName)
    gtk.main()
