# DBus-Actions - a tray application containing modules listening to dbus events
# Copyright (C) 2009 by Stefan Schlott
# Published under the GNU Public License V2 (GPL-2)

import gtk

class GladeWindow(object):
    def __init__(self,gladeFilename,gladeRootElement,parentWidget=None):
        # Set the Glade file
        self.gladefile = gladeFilename
        self.wTree = gtk.glade.XML(self.gladefile, gladeRootElement)
        # Autoconnect events
        self.wTree.signal_autoconnect(self)
        # Add each widget as an attribute of object
        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            # make sure we don't clobber existing attributes
            assert not hasattr(self, name)
            setattr(self, name, w)
