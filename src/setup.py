import os, fnmatch
from distutils.core import setup


def opj(*args):
    path = os.path.join(*args)
    return os.path.normpath(path)


def find_data_files(srcdir, *wildcards, **kw):
    # get a list of all files under the srcdir matching wildcards,
    # returned in a format to be used for install_data
    def walk_helper(arg, dirname, files):
        if '.svn' in dirname:
            return
        names = []
        lst, wildcards = arg
        for wc in wildcards:
            wc_name = opj(dirname, wc)
            for f in files:
                filename = opj(dirname, f)

                if fnmatch.fnmatch(filename, wc_name) and not os.path.isdir(filename):
                    names.append(filename)
        if names:
            lst.append( (dirname, names ) )

    file_list = []
    recursive = kw.get('recursive', True)
    if recursive:
        os.path.walk(srcdir, walk_helper, (file_list, wildcards))
    else:
        walk_helper((file_list, wildcards),
                    srcdir,
                    [os.path.basename(f) for f in glob.glob(opj(srcdir, '*'))])
    return file_list


modulefiles=[]
for m in find_data_files("modules","*.*"):
    path="/usr/share/dbusactions/"+m[0]
    modulefiles.append((path,m[1]))

setup(
    name="dbus-actions",
    version="1.0.1",
    description="Gnome application hosting small modules reacting on dbus messages",
    author="Stefan Schlott",
    author_email="stefan@ploing.de",
    url="http://stefan.ploing.de/linux/dbus-actions/",
    packages=["dbusactions"],
    data_files=modulefiles +
    [
        ("/usr/share/dbusactions",["trayicon.png","configwindow.glade","dbus-actions.schemas"]),
    ],
    scripts = ["dbus-actions.py"],
)
