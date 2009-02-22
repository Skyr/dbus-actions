#!/usr/bin/env python

# DBus-Actions - a tray application containing modules listening to dbus events
# Copyright (C) 2009 by Stefan Schlott
# Published under the GNU Public License V2 (GPL-2)


import logging 
try:
    import pygtk
    pygtk.require("2.0")
except:
    sys.exit(1)
from optparse import OptionParser
import gtk
from dbusactions.module import Module
from dbusactions.main import Tray


if __name__ == "__main__":
    logger=logging.getLogger("Module")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.ERROR)
    # Parse params
    parser = OptionParser()
    parser.add_option("-d", "--deactivate-modules", dest="deactivateModules", action="store_true",
                  help="Deactivate all modules on startup", default=False)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="Enable debug output", default=False)
    (options, args) = parser.parse_args()
    if options.verbose:
        logger.setLevel(logging.DEBUG)
    # Main loop
    main=Tray(options.deactivateModules)
    gtk.main()
