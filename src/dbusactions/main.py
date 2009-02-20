import os
import sys
import glob
import imp
import pygtk
import gobject
import gtk
import gtk.glade
import gconf
import egg.trayicon
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from dbusactions.gladewindow import GladeWindow
from dbusactions.module import ModuleParams


def stockMenuItem(stockid, handler):
    item = gtk.ImageMenuItem(stockid)
    item.connect('activate',handler)
    return item

def menuItem(title, handler):
    item = gtk.MenuItem(title)
    item.connect('activate',handler)
    return item


class ConfigWindow(GladeWindow):
    def __init__(self,appDataPath,modules,storePrefProc):
        super(ConfigWindow,self).__init__(os.path.join(appDataPath,"configwindow.glade"),"windowConfig")
        self.modules=modules
        self.storeSettings=storePrefProc
        # Set up list columns
        crt=gtk.CellRendererToggle()
        crt.set_active(True)
        crt.connect("toggled",self.on_column_toggled)
        col=gtk.TreeViewColumn("Enabled",crt,active=0)
        col.set_resizable(False)
        self.moduleView.append_column(col)
        col=gtk.TreeViewColumn("Icon",gtk.CellRendererPixbuf(),pixbuf=1)
        col.set_resizable(False)
        self.moduleView.append_column(col)
        col=gtk.TreeViewColumn("Module",gtk.CellRendererText(),text=2)
        col.set_resizable(True)
        self.moduleView.append_column(col)
        # Set up storage model
        self.moduleList=gtk.ListStore(gobject.TYPE_BOOLEAN,gtk.gdk.Pixbuf,gobject.TYPE_STRING)
        self.moduleView.set_model(self.moduleList)
        # Insert module data
        modulekeys=modules.keys()
        modulekeys.sort()
        self.moduleKey=[]
        for m in modulekeys:
            icon=None
            if modules[m].getIconName()!=None:
                icon=gtk.gdk.pixbuf_new_from_file(modules[m].getIconName())
            self.moduleList.append([modules[m].isActive,icon,modules[m].getModuleName()])
            self.moduleKey.append(m)
    
    def updateModuleStatuses(self):
        for i in range(0,len(self.moduleKey)):
            self.moduleList.set(self.moduleList.get_iter(str(i)),0,self.modules[self.moduleKey[i]].isActive)
    
    def on_moduleView_cursor_changed(self, widget):
        module=self.moduleKey[self.moduleView.get_cursor()[0][0]]
        self.buttonConfigure.set_sensitive(self.modules[module].isConfigurable())

    def on_column_toggled(self,widget,path):
        newstate=not self.modules[self.moduleKey[int(path)]].isActive
        #self.moduleList.set(self.moduleList.get_iter(path),0,newstate)
        if newstate:
            self.modules[self.moduleKey[int(path)]].activate()
        else:
            self.modules[self.moduleKey[int(path)]].deactivate()

    def on_buttonConfigure_clicked(self, widget):
        module=self.moduleKey[self.moduleView.get_cursor()[0][0]]
        self.modules[module].configureDialog(self.windowConfig)
    
    def on_buttonOk_clicked(self, widget):
        self.windowConfig.hide()
        self.storeSettings()
        


class Tray:
    def __init__(self,deactivateModules):
        # Determine app data path: Must contain configwindow.glade
        appDataPath = os.path.dirname(sys.argv[0])
        if not os.path.exists(os.path.join(appDataPath,"configwindow.glade")):
            appDataPath = "/usr/share/dbusactions"
        # Initialize global options
        self.confAppKey = "/apps/dbus-actions"
        self.globalOptions = {
            "appDataPath" : appDataPath,
            "localModulesDir" : os.path.join(os.getenv("HOME"),".dbus-actions"),
        }
        self.globalOptions["globalModulesDir"]=os.path.join(self.globalOptions["appDataPath"],"modules")
        self.systemBus = dbus.SystemBus(mainloop=DBusGMainLoop())
        self.sessionBus = dbus.SessionBus(mainloop=DBusGMainLoop())
        self.configWindow = None
        # Scan modules
        self.conf = gconf.client_get_default()
        self.modules={}
        self.scanModules(self.globalOptions["globalModulesDir"])
        self.scanModules(self.globalOptions["localModulesDir"])
        # Load global settings
        if not deactivateModules:
            self.loadSettings()
        # Tray menu
        self.trayMenu = gtk.Menu()
        self.trayMenu.add(menuItem("Configure",self.trayMenu_config_activate))
        self.trayMenu.add(gtk.SeparatorMenuItem())
        self.trayMenu.add(stockMenuItem(gtk.STOCK_QUIT,self.trayMenu_quit_activate))
        self.trayMenu.show_all()
        # Tray icon image
        self.trayIconImage = gtk.Image()
        self.trayIconImage.set_from_file(os.path.join(self.globalOptions["appDataPath"],"trayicon.png"))
        # Event box (content of tray icon area)
        self.trayEventBox = gtk.EventBox()
        self.trayEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.POINTER_MOTION_HINT_MASK | gtk.gdk.CONFIGURE)
        self.trayEventBox.add(self.trayIconImage)
        self.trayEventBox.set_tooltip_text("DBus Actions")
        self.trayEventBox.connect("button_press_event",self.trayEventBox_face_click)
        # Assemble tray icon
        self.trayicon = egg.trayicon.TrayIcon("DBus Actions")
        self.trayicon.add(self.trayEventBox)
        self.trayicon.show_all()
        # Create config window
        self.configWindow=ConfigWindow(self.globalOptions["appDataPath"],self.modules,self.storeSettings)
        # If no modules are enabled: Show config window
        activeCnt=0
        for module in self.modules.keys():
            if self.modules[module].isActive:
                activeCnt=activeCnt+1
        if activeCnt==0:
            self.configWindow.windowConfig.show()
        self.updateModuleStatuses()

    def trayEventBox_face_click(self, window, event, *data):
        if event.button==3: 
            self.trayMenu.popup(None,None,None,0,event.time);
    
    def trayMenu_config_activate(self, widget):
        self.configWindow.windowConfig.show()
    
    def trayMenu_quit_activate(self, widget):
        self.storeSettings()
        gtk.main_quit()

    def loadSettings(self):
        enabledModules=self.conf.get_list(self.confAppKey+"/enabled_modules",gconf.VALUE_STRING)
        # Enable modules
        for module in enabledModules:
            if self.modules.has_key(module):
                self.modules[module].activate()

    def storeSettings(self):
        enabledModules=[]
        for module in self.modules.keys():
            if self.modules[module].isActive:
                enabledModules.append(module)
        self.conf.set_list(self.confAppKey+"/enabled_modules",gconf.VALUE_STRING,enabledModules)

    def updateModuleStatuses(self):
        if self.configWindow:
            self.configWindow.updateModuleStatuses()
            cnt=0
            for module in self.modules.keys():
                if self.modules[module].isActive:
                    cnt=cnt+1
            self.trayEventBox.set_tooltip_text("DBus Actions\nActive modules: %d" % cnt)

    def scanModules(self, path):
        if os.path.exists(path) and os.path.isdir(path):
            for dir in glob.glob(os.path.join(path,"*")):
                if os.path.isdir(dir):
                    modulename=os.path.basename(dir)
                    modulepath=dir
                    modulefile=os.path.join(dir,"__init__.py")
                    if os.path.exists(modulefile) and os.path.isfile(modulefile):
                        try:
                            # Load module
                            file,filename,description = imp.find_module("%s" % (modulename),[path])
                            module=imp.load_module("%s" % (modulename),file,filename,description)
                            # Get instance (class name must be Module)
                            self.modules[modulename]=module.Module(ModuleParams(dir,self.confAppKey,self.conf,self.updateModuleStatuses,self.systemBus,self.sessionBus))
                        except ImportError:
                            print("Unable to load module %s: %s" % (modulefile))
