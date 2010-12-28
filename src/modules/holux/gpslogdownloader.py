#!/usr/bin/env python

# DBus-Actions - a tray application containing modules listening to dbus events
# gpslogdownloader - module/standalone app for a small GUI wrapper for gpsbabel, etc.
# Copyright (C) 2009 by Stefan Schlott
# Published under the GNU Public License V2 (GPL-2)


# Register schemas with: gconftool-2 --install-schema-file gpslog-downloader.schemas

# idVendor: 10c4 = 4292dec
# idProduct: ea60 = 60000dec


import logging 
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


gladePath=None

def findGladeFile(filename):
    global gladePath
    if gladePath:
        fullname=os.path.join(gladePath,filename)
        if os.path.isfile(fullname):
            return fullname        
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


class Settings:
    def __init__(self):
        # Get GConf client
        self.conf = gconf.client_get_default()
        self.confAppKey = "/apps/gpslog-downloader"

    def getSettings(self):
        self.eraseOnDevice = self.conf.get_bool(self.confAppKey+"/erase_on_device")
        self.downloadCmd = self.conf.get_string(self.confAppKey+"/download_cmd")
        if not self.downloadCmd:
            self.downloadCmd = "" 
        self.eraseCmd = self.conf.get_string(self.confAppKey+"/erase_cmd")
        if not self.eraseCmd:
            self.eraseCmd = ""
        self.dataPath = self.conf.get_string(self.confAppKey+"/data_path")
        if not self.dataPath:
            self.dataPath = os.path.expanduser("~")
        self.dataFilenameTemplate = self.conf.get_string(self.confAppKey+"/data_filename_template")
        if not self.dataFilenameTemplate:
            self.dataFilenameTemplate = "gpsdata-%Y%m%d.gpx"
        self.defaultDevice = self.conf.get_string(self.confAppKey+"/default_device")
        if not self.defaultDevice:
            self.defaultDevice=""

    def storeSettings(self):
        self.conf.set_bool(self.confAppKey+"/erase_on_device",self.eraseOnDevice)
        self.conf.set_string(self.confAppKey+"/download_cmd",self.downloadCmd)
        self.conf.set_string(self.confAppKey+"/erase_cmd",self.eraseCmd)
        self.conf.set_string(self.confAppKey+"/data_path",self.dataPath)
        self.conf.set_string(self.confAppKey+"/data_filename_template",self.dataFilenameTemplate)
        self.conf.set_string(self.confAppKey+"/default_device",self.defaultDevice)
    

class SettingsDialog:
    def __init__(self, settings):
        self.settings = settings
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
        self.dirchooser.set_current_folder(self.settings.dataPath)
        self.entryFilenameTemplate.set_text(self.settings.dataFilenameTemplate)
        self.entryDownloadCmd.set_text(self.settings.downloadCmd)
        self.entryEraseCmd.set_text(self.settings.eraseCmd)
        self.cbEraseOnDevice.set_active(self.settings.eraseOnDevice)
        self.entryDefaultDevice.set_text(self.settings.defaultDevice)
    
    def on_buttonOk_clicked(self, widget):
        self.dialogSettings.hide()
        # Transmit entered data
        self.settings.dataPath=self.dirchooser.get_filename()
        self.settings.dataFilenameTemplate=self.entryFilenameTemplate.get_text()
        self.settings.downloadCmd=self.entryDownloadCmd.get_text()
        self.settings.eraseCmd=self.entryEraseCmd.get_text()
        self.settings.eraseOnDevice=self.cbEraseOnDevice.get_active()
        self.settings.defaultDevice=self.entryDefaultDevice.get_text()
        # Store and apply
        self.settings.storeSettings()
    
    def on_buttonCancel_clicked(self, widget):
        self.dialogSettings.hide()


class ImportDialog:
    """Main dialog"""
    def __init__(self, deviceName):
        self.deviceName=deviceName
        self.logger = logging.getLogger("Module")        
        # Set the Glade file
        #self.gladefile = findGladeFile("importwindow.glade")
        #self.wTree = gtk.glade.XML(self.gladefile, "windowImport")
        self.gladefile = findGladeFile("importdialog.glade")
        self.wTree = gtk.glade.XML(self.gladefile, "dialogImport")
        # Autoconnect events
        self.wTree.signal_autoconnect(self)
        # Add each widget as an attribute of object
        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            # make sure we don't clobber existing attributes
            assert not hasattr(self, name)
            setattr(self, name, w)
        # Set default values
        self.settings=Settings()
        self.settings.getSettings()
        self.setDefaultValues()

    def setDefaultValues(self):
        self.cbErase.set_active(self.settings.eraseOnDevice)
        self.filechooser.set_current_folder(self.settings.dataPath)
        dataFilename=time.strftime(self.settings.dataFilenameTemplate)
        self.filechooser.set_current_name(dataFilename)

    def on_buttonConfigure_clicked(self, *args):
        cfgdlg = SettingsDialog(self.settings)
        if cfgdlg.dialogSettings.run()==gtk.RESPONSE_OK:
            self.setDefaultValues()
        cfgdlg.dialogSettings.destroy()

    def on_buttonCancel_clicked(self, *args):
        self.dialogImport.response(gtk.RESPONSE_CANCEL)

    def on_buttonOk_clicked(self, *args):
        if not self.deviceName:
            self.deviceName=self.settings.defaultDevice
        dataFilename=self.filechooser.get_filename()
        exportAndQuit=True
        if os.path.exists(dataFilename):
            if not os.path.isfile(dataFilename):
                return
            dlg = gtk.MessageDialog(parent=self.dialogImport,type=gtk.MESSAGE_WARNING,buttons=gtk.BUTTONS_YES_NO)
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
            downloadCmd = self.settings.downloadCmd % paramMap 
            eraseCmd = self.settings.eraseCmd % paramMap
            self.logger.debug("Running %s" % (downloadCmd))
            result=commands.getstatusoutput(downloadCmd)
            self.logger.debug("Result: %s" % (result[1]))
            if result[0]==0:
                self.logger.debug("Running %s" % (eraseCmd))
                commands.getstatusoutput(eraseCmd)
                self.dialogImport.response(gtk.RESPONSE_OK)
            else:
                dlg = gtk.MessageDialog(parent=self.dialogImport,type=gtk.MESSAGE_ERROR,buttons=gtk.BUTTONS_OK)
                dlg.set_title("Error downloading data")
                dlg.set_markup("Error downloading data:\n%s" % (result[1]))
                dlg.run()
                self.dialogImport.response(gtk.RESPONSE_REJECT)
        else:
            self.dialogImport.response(gtk.RESPONSE_REJECT)


def run(deviceName,showConfig):
    result=gtk.RESPONSE_REJECT
    while result==gtk.RESPONSE_REJECT:
        dlgImport = ImportDialog(deviceName)
        if showConfig:
            dlgImport.cfgButtonBox.show()
        result=dlgImport.dialogImport.run()
        dlgImport.dialogImport.destroy()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--device", dest="deviceName",
                  help="Device name of GPS device", default=None)
    (options, args) = parser.parse_args()
    run(options.deviceName,True)
