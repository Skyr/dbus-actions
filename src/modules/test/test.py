import dbusactions.module

class Module(dbusactions.module.Module):
    def __init__(self,moduleParams):
        #dbusactions.module.Module.__init__(self,systemBus,sessionBus)
        super(Module,self).__init__(moduleParams)
        self.moduleName = "Test module"
        #self.interfaceList = ['org.gnome.Tomboy.RemoteControl']
        self.interfaceList = [('im.pidgin.purple.PurpleInterface','ConversationSwitched')]

    def isConfigurable(self):
        return False

    def dbusSessionEvent(self, *args, **kwargs):
        params=[]
        for arg in args:
            params.append(str(arg))
        keywords=[]
        for kw in kwargs.keys():
            keywords.append("%s=%s"%(kw,kwargs[kw]))
        #eventstr="%s.%s(%s)" % (kwargs['dbus_interface'],kwargs['member'],",".join(params))
        #print "dbus session bus: %s" % eventstr
        print "Keywords: " + ",".join(keywords)
        print "Params:   " + ",".join(params)
