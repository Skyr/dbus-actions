#!/usr/bin/env python

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
    logger.setLevel(logging.DEBUG)
    # Parse params
    parser = OptionParser()
    parser.add_option("-d", "--deactivate-modules", dest="deactivateModules", action="store_true",
                  help="Deactivate all modules on startup", default=False)
    (options, args) = parser.parse_args()
    # Main loop
    main=Tray(options.deactivateModules)
    gtk.main()
