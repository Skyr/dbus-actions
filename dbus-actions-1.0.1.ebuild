# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit distutils

DESCRIPTION="Gnome application hosting small modules reacting on dbus messages"
HOMEPAGE="http://stefan.ploing.de/linux/dbus-actions/"
SRC_URI="http://stefan.ploing.de/dist/dbus-actions/${P}.tar.gz"

LICENSE="GPL2"
SLOT="0"
KEYWORDS="x86"
IUSE=""

DEPEND="dev-python/pygobject
	dev-python/pygtk
	dev-python/dbus-python
	dev-python/gnome-python
	dev-python/gnome-python-extras"
RDEPEND=""

