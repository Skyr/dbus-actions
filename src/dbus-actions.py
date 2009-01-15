#!/usr/bin/env python

import logging 
try:
    import pygtk
    pygtk.require("2.0")
except:
    sys.exit(1)
import gtk
from dbusactions.module import Module
from dbusactions.main import Tray


if __name__ == "__main__":
    logger=logging.getLogger("Module")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    # Main loop
    main=Tray()
    gtk.main()
