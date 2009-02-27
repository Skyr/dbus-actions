# DBus-Actions - a tray application containing modules listening to dbus events
# Copyright (C) 2009 by Stefan Schlott
# Published under the GNU Public License V2 (GPL-2)

import dbusactions.module

class Module(dbusactions.module.Module):
    def __init__(self,moduleParams):
        super(Module,self).__init__(moduleParams)
        self.moduleName = "Test module"        
        # Uncomment one of these:        
        #self.inferfaceList = []
        #self.interfaceList = ['org.gnome.Tomboy.RemoteControl']
        #self.interfaceList = [('im.pidgin.purple.PurpleInterface','ConversationSwitched')]

    def isConfigurable(self):
        return False

    def dbusSessionEvent(self, *args, **kwargs):
        params=[]
        for arg in args:
            params.append(str(arg))
        keywords=[]
        for kw in kwargs.keys():
            keywords.append("%s=%s"%(kw,kwargs[kw]))
        print "Keywords: " + ",".join(keywords)
        print "Params:   " + ",".join(params)
