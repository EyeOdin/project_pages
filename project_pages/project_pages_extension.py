# Project Pages is a Krita plugin to Compile files into a single project file.
# Copyright ( C ) 2022  Ricardo Jeremias.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# ( at your option ) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#region Import Modules #############################################################

from krita import *
from PyQt5 import Qt, QtWidgets, QtCore, QtGui, uic
from PyQt5.Qt import Qt

#endregion
#region Global Variables ###########################################################

EXTENSION_ID = 'pykrita_project_pages_extension'

#endregion


class ProjectPages_Extension( Extension ):
    """
    Extension Shortcuts.
    """
    SIGNAL_MIRROR_FIX = QtCore.pyqtSignal( str )

    #region Initialize #############################################################

    def __init__( self, parent ):
        super().__init__( parent )
    def setup( self ):
        pass

    #endregion
    #region Actions ################################################################

    def createActions( self, window ):
        # Main Menu
        menu_project_pages = QtWidgets.QMenu( "project_pages_menu", window.qwindow() )
        action_project_pages = window.createAction( "project_pages_menu", "Project Pages", "tools/scripts" )
        action_project_pages.setMenu( menu_project_pages )

        # Mirror Fix
        menu_mirror_fix = QtWidgets.QMenu( "mirror_fix_menu", window.qwindow() )
        action_mirror_fix = window.createAction( "mirror_fix_menu", "Mirror Fix", "tools/scripts/project_pages_menu" )
        action_mirror_fix.setMenu( menu_mirror_fix )

        action_mirror_fix_left  = window.createAction( "project_pages_mirror_fix_left",  "LEFT",  "tools/scripts/project_pages_menu/mirror_fix_menu" )
        action_mirror_fix_right = window.createAction( "project_pages_mirror_fix_right", "RIGHT", "tools/scripts/project_pages_menu/mirror_fix_menu" )
        action_mirror_fix_top   = window.createAction( "project_pages_mirror_fix_top",   "TOP",   "tools/scripts/project_pages_menu/mirror_fix_menu" )
        action_mirror_fix_down  = window.createAction( "project_pages_mirror_fix_down",  "DOWN",  "tools/scripts/project_pages_menu/mirror_fix_menu" )

        action_mirror_fix_left.triggered.connect( lambda: self.MIRROR_FIX_SIGNAL( "LEFT" ) )
        action_mirror_fix_right.triggered.connect( lambda: self.MIRROR_FIX_SIGNAL( "RIGHT" ) )
        action_mirror_fix_top.triggered.connect( lambda: self.MIRROR_FIX_SIGNAL( "TOP" ) )
        action_mirror_fix_down.triggered.connect( lambda: self.MIRROR_FIX_SIGNAL( "DOWN" ) )

    #endregion
    #region Signal #################################################################

    def MIRROR_FIX_SIGNAL( self, mode ):
        self.SIGNAL_MIRROR_FIX.emit( mode )

    #endregion
