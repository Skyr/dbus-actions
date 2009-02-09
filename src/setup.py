from distutils.core import setup

setup(
    name="dbus-actions",
    version="1.0",
    description="Gnome application hosting small modules reacting on dbus messages",
    author="Stefan Schlott",
    author_email="stefan@ploing.de",
    url="http://stefan.ploing.de/linux/dbus-actions/",
    packages=["dbusactions"],
    data_files=[
        ("/usr/share/dbusactions",["modules","trayicon.png","*.glade","*.schemas"]),
        ("/usr/bin",["dbus-actions.py"])
    ],
)
