import os
import re
import gobject
import gtk
import dbus
import dbusactions.module
from dbusactions.gladewindow import GladeWindow


class Msg:
    def __init__(self,systemMsg,msg):
        self.systemMsg=systemMsg
        self.msg=msg


class DebugWindow(GladeWindow):
    def __init__(self,module):
        super(DebugWindow,self).__init__(os.path.join(module.modulePath,"debugwindow.glade"),"windowDebug")
        self.module=module
        # Load icons
        iconTheme=gtk.icon_theme_get_default()
        try:
            self.iconSystemBus=iconTheme.load_icon("system",16,gtk.ICON_LOOKUP_FORCE_SVG)
        except:
            self.iconSystemBus=None
        try:
            self.iconSessionBus=iconTheme.load_icon("session-properties",16,gtk.ICON_LOOKUP_FORCE_SVG)
        except:
            self.iconSessionBus=None
        # Prepare list columns
        col=gtk.TreeViewColumn("Icon",gtk.CellRendererPixbuf(),pixbuf=0)
        col.set_resizable(False)
        self.msgView.append_column(col)
        col=gtk.TreeViewColumn("Module",gtk.CellRendererText(),text=1)
        col.set_resizable(True)
        self.msgView.append_column(col)
        self.rowCount=0
        # Set up storage model
        self.msgList=gtk.ListStore(gtk.gdk.Pixbuf,gobject.TYPE_STRING)
        self.msgView.set_model(self.msgList)
        # Clear contents        
        self.clearAll()

    def on_buttonApply_clicked(self,widget):
        self.setFilter(self.entryFilter.get_text())
        self.rebuildList()
    
    def on_buttonClear_clicked(self,widget):
        self.setFilter("")
        self.rebuildList()

    def on_windowDebug_destroy(self,widget):
        self.module.deactivate()

    def setFilter(self,filterString):
        if len(filterString)>0 and filterString[0]!="^":
            self.filterString=".*"+filterString
        else:
            self.filterString=filterString
        self.filterReg=re.compile(self.filterString,re.IGNORECASE)

    def rebuildList(self):
        self.msgList.clear()
        self.rowCount=0
        for msg in self.elements:
            self.displayMsg(msg)
        #adj=self.msgScroller.get_vadjustment()
        #adj.set_value(adj.upper)
        if self.rowCount>0:
            self.msgView.scroll_to_cell(self.rowCount-1)

    def clearAll(self):
        self.setFilter("")
        self.elements=[]
        self.togglebuttonPause.set_active(False)
        self.rebuildList()

    def msgMatchesFilter(self,msg):
        return (self.filterReg.match(msg.msg)!=None)

    def displayMsg(self,msg):
        if self.msgMatchesFilter(msg):
            self.rowCount=self.rowCount+1
            if msg.systemMsg:
                self.msgList.append([self.iconSystemBus,msg.msg])
            else:
                self.msgList.append([self.iconSessionBus,msg.msg])

    def appendMsg(self,msg):
        if self.togglebuttonPause.get_active():
            return
        self.elements.append(msg)
        self.displayMsg(msg)
        if len(self.elements)>500:
            if self.msgMatchesFilter(self.elements[0]):
                self.msgList.remove(self.msgList.get_iter_from_string("0"))
                self.rowCount=self.rowCount-1
            del(self.elements[0])
        if self.rowCount>0:
            self.msgView.scroll_to_cell(self.rowCount-1)


class Module(dbusactions.module.Module):
    def __init__(self,moduleParams):
        super(Module,self).__init__(moduleParams)
        self.moduleName = "Monitor dbus messages"
        self.iconFilename = "debugicon.png"
        self.debugwindow=None

    def activate(self):
        if self.isActive:
            return
        super(Module,self).activate()
        self.debugwindow=DebugWindow(self)
        self.debugwindow.windowDebug.show()

    def deactivate(self):
        if not self.isActive:
            return
        super(Module,self).deactivate()
        self.debugwindow.windowDebug.hide()
        self.debugwindow.windowDebug.destroy()
        self.debugwindow=None

    def dbusSystemEvent(self, *args, **kwargs):
        params=[]
        for arg in args:
            params.append(str(arg))
        eventstr="%s.%s(%s)" % (kwargs['dbus_interface'],kwargs['member'],",".join(params))
        self.debugwindow.appendMsg(Msg(True,eventstr))

    def dbusSessionEvent(self, *args, **kwargs):
        params=[]
        for arg in args:
            params.append(str(arg))
        eventstr="%s.%s(%s)" % (kwargs['dbus_interface'],kwargs['member'],",".join(params))
        self.debugwindow.appendMsg(Msg(False,eventstr))
