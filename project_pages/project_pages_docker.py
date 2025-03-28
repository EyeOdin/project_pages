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


#region Imports

# Python Modules
import os
import shutil
import xml
import webbrowser
import zipfile
import pathlib
import random
import subprocess
import datetime
# Krita Module
from krita import *
# PyQt5 Modules
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Project Pages Modules
from .project_pages_extension import ProjectPages_Extension

#endregion
#region Global Variables

# Plugin
DOCKER_NAME = "Project Pages"
project_pages_version = "2025_03_16"

# Project
file_extension = "zip"
structure = ["control.eo", "thumbnail.png", "IMAGES/", "TEXTS/", "TRASH/"]

# File Formats
file_image = [
    "*.kra",
    "*.krz",
    "*.ora",
    "*.bmp",
    "*.gif",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.pbm",
    "*.pgm",
    "*.ppm",
    "*.xbm",
    "*.xpm",
    "*.tiff",
    "*.psd",
    "*.webp",
    "*.svg",
    "*.svgz",
    "*.zip",
    ]
file_text = [
    "*.txt",
    "*.eo",
    ]

# Variables
check_timer = 1000
qt_max = 16777215

# time constants
segundo = 1 # null
minuto = 60 # seconds
hora = 60 # minutes
dia = 24 # hours
mes = 30.4167 # days
ano = 12 # moths
sec_segundo = segundo
sec_minuto = minuto * sec_segundo
sec_hora = hora * sec_minuto
sec_dia = dia * sec_hora
sec_mes = mes * sec_dia
sec_ano = ano * sec_mes

#endregion


class ProjectPages_Docker( DockWidget ):

    #region Initialize

    def __init__( self ):
        super( ProjectPages_Docker, self ).__init__()

        # Construct
        self.User_Interface()
        self.Variables()
        self.Connections()
        self.Modules()
        self.Style()
        self.Timer()
        self.Extension()
        self.Settings()
        self.Plugin_Load()

    def User_Interface( self ):
        # Window
        self.setWindowTitle( DOCKER_NAME )

        # Operating System
        self.OS = str( QSysInfo.kernelType() ) # WINDOWS=winnt & LINUX=linux
        if self.OS == 'winnt': # Unlocks icons in Krita for Menu Mode
            QApplication.setAttribute( Qt.AA_DontShowIconsInMenus, False )

        # Path Name
        self.directory_plugin = str( os.path.dirname( os.path.realpath( __file__ ) ) )

        # Widget Docker
        self.layout = uic.loadUi( os.path.abspath( os.path.join( self.directory_plugin, "project_pages_docker.ui" ) ), QWidget( self ) )
        self.setWidget( self.layout )

        # Settings
        self.dialog = uic.loadUi( os.path.abspath( os.path.join( self.directory_plugin, "project_pages_settings.ui" ) ), QDialog( self ) )
        self.dialog.setWindowTitle( "Project Pages : Settings" )
    def Variables( self ):
        # Variables
        self.project_active = False
        self.project_auto_save = False
        self.thumbnail_size = 100
        self.note_textwrap = False

        # Color
        self.color_alpha = QColor( 0, 0, 0, 0 )
        self.color_thumbnail = QColor( "#043764" )

        # Paths
        self.project_zip = None # Original ZIP file
        self.project_directory = None # Project UnZIPped directory
        self.project_control = None
        self.project_images = None
        self.project_texts = None
        self.project_trash = None
        self.project_recent = []

        # Index
        self.found_images = []
        self.found_texts = []
        self.found_index = { "image" : 0, "text" : 0 }

        # Information
        self.work_hours = 0

        # Document
        self.doc_basename = "page"
        self.doc_template = [
            # Texture
            { "index" : "Texture 256",          "width":256,  "height":256 },
            { "index" : "Texture 1024",         "width":1024, "height":1024 },
            { "index" : "Texture 2048",         "width":2048, "height":2048 },
            { "index" : "Texture 4096",         "width":4096, "height":4096 },
            # Paper
            { "index" : "Paper A3",             "width":3508, "height":4960 },
            { "index" : "Paper A4",             "width":2480, "height":3508 },
            { "index" : "Paper A5",             "width":1754, "height":2480 },
            { "index" : "Paper A6",             "width":1240, "height":1754 },
            # Screen
            { "index" : "Screen 480p SD",       "width":640,  "height":480 },
            { "index" : "Screen 720p HD",       "width":1280, "height":720 },
            { "index" : "Screen 1080p FHD",     "width":1920, "height":1080 },
            { "index" : "Screen 1440p QHD",     "width":2560, "height":1440 },
            { "index" : "Screen 1080p 2k",      "width":2048, "height":1080 },
            { "index" : "Screen 2160p UHD 4k",  "width":3840, "height":2160 },
            { "index" : "Screen 4320p FUHD 8k", "width":7680, "height":4320 },
            # Custom ( has to be last in the list always )
            { "index" : "Custom",               "width":None, "height":None },
            ]
        self.doc_width = 2480
        self.doc_height = 3508
        self.doc_swap = False
        self.doc_colorspace = "RGBA"
        self.doc_bitdepth = "U8"
        self.doc_dpi = 300
        self.doc_gh = ""
        self.doc_gv = ""

        # Guides
        self.guide_horizontal_mirror = False
        self.guide_vertical_mirror = False
        self.guide_horizontal_list = []
        self.guide_vertical_list = []
        self.guide_ruler = False
        self.guide_snap = False
        self.guide_visible = False
        self.guide_lock = False

        # Layers
        self.layer_space = False
        self.layer_replace = False
        self.layer_prefix = False
        self.layer_suffix = False
        self.layer_string = {
            "space" : "",
            "replace_old" : "",
            "replace_new" : "",
            "prefix_folder" : "",
            "prefix_layer" : "",
            "suffix_folder" : "",
            "suffix_layer" : "",
            }

        # System
        self.sow_project = False
        self.sow_dockers = False

        # Export
        self.export_width_state = False
        self.export_height_state = False
        self.export_width_value = 1000
        self.export_height_value = 1000
    def Connections( self ):
        # Panels
        self.layout.project_list.doubleClicked.connect( self.Project_Open )
        self.layout.page_list.currentItemChanged.connect( self.Text_Load )
        self.layout.page_list.doubleClicked.connect( self.Page_Open )
        self.layout.text_note.textChanged.connect( self.Text_Save )
        # UI
        self.layout.export_selection.clicked.connect( self.Export_Selection )
        self.layout.page_index.valueChanged.connect( self.Index_Number )
        self.layout.settings.clicked.connect( self.Menu_Settings )

        # Dialog
        self.dialog.tab_widget.tabBarClicked.connect( self.Menu_Tabs )

        # Dialog Template
        self.dialog.note_textwrap.toggled.connect( self.Note_TextWrap )
        self.dialog.doc_basename.textChanged.connect( self.Document_Basename )
        self.dialog.doc_template.currentTextChanged.connect( self.Document_Template )
        self.dialog.doc_width.valueChanged.connect( self.Document_Dim_Width )
        self.dialog.doc_height.valueChanged.connect( self.Document_Dim_Height )
        self.dialog.doc_swap.toggled.connect( self.Document_Dim_Swap )
        self.dialog.doc_colorspace.currentTextChanged.connect( self.Document_Color_Space )
        self.dialog.doc_bitdepth.currentTextChanged.connect( self.Document_Bit_Depth )
        self.dialog.doc_dpi.valueChanged.connect( self.Document_DPI )
        self.dialog.doc_gh.textChanged.connect( self.Document_GH_List )
        self.dialog.doc_gv.textChanged.connect( self.Document_GV_List )
        self.dialog.pushbutton_gh.clicked.connect( self.Document_GH_Import )
        self.dialog.pushbutton_gv.clicked.connect( self.Document_GV_Import )
        # Dialog Information
        self.dialog.info_title.textChanged.connect( self.Information_Save )
        self.dialog.info_abstract.textChanged.connect( self.Information_Save )
        self.dialog.info_keyword.textChanged.connect( self.Information_Save )
        self.dialog.info_subject.textChanged.connect( self.Information_Save )
        self.dialog.info_license.textChanged.connect( self.Information_Save )
        self.dialog.info_language.textChanged.connect( self.Information_Save )
        self.dialog.info_description.textChanged.connect( self.Information_Save )
        self.dialog.menu_money_rate.valueChanged.connect( self.Money_Rate )
        self.dialog.menu_money_total.valueChanged.connect( self.Money_Total )
        self.dialog.info_contact.itemClicked.connect( self.Information_Copy )
        # Dialog Guides
        self.dialog.guide_horizontal_mirror.toggled.connect( self.Guide_Horizontal_Mirror )
        self.dialog.guide_vertical_mirror.toggled.connect( self.Guide_Vertical_Mirror )
        self.dialog.guide_horizontal_list.doubleClicked.connect( self.Guide_Set_Horizontal )
        self.dialog.guide_vertical_list.doubleClicked.connect( self.Guide_Set_Vertical )
        self.dialog.guide_ruler.toggled.connect( self.Guide_Ruler )
        self.dialog.guide_snap.toggled.connect( self.Guide_Snap )
        self.dialog.guide_visible.toggled.connect( self.Guide_Visible )
        self.dialog.guide_lock.toggled.connect( self.Guide_Lock )
        # Dialog Layers
        self.dialog.layer_space.toggled.connect( self.Layer_Space )
        self.dialog.layer_replace.toggled.connect( self.Layer_Replace )
        self.dialog.layer_prefix.toggled.connect( self.Layer_Prefix )
        self.dialog.layer_suffix.toggled.connect( self.Layer_Suffix )
        self.dialog.replace_space.textChanged.connect( self.Rename_Strings )
        self.dialog.replace_old.textChanged.connect( self.Rename_Strings )
        self.dialog.replace_new.textChanged.connect( self.Rename_Strings )
        self.dialog.prefix_folder.textChanged.connect( self.Rename_Strings )
        self.dialog.prefix_layer.textChanged.connect( self.Rename_Strings )
        self.dialog.suffix_folder.textChanged.connect( self.Rename_Strings )
        self.dialog.suffix_layer.textChanged.connect( self.Rename_Strings )
        self.dialog.rename_report.doubleClicked.connect( self.Layer_Select )
        self.dialog.rename_layers.clicked.connect( self.Layer_Rename )
        # Dialog System
        self.dialog.sow_project.toggled.connect( self.ShowOnWelcome_Project )
        self.dialog.sow_dockers.toggled.connect( self.ShowOnWelcome_Dockers )
        # Export
        self.dialog.export_width_state.toggled.connect( self.Export_Width_State )
        self.dialog.export_width_value.valueChanged.connect( self.Export_Width_Value )
        self.dialog.export_height_state.toggled.connect( self.Export_Height_State )
        self.dialog.export_height_value.valueChanged.connect( self.Export_Height_Value )
        # Notices
        self.dialog.manual.clicked.connect( self.Menu_Manual )
        self.dialog.license.clicked.connect( self.Menu_License )

        # Event Filter
        self.layout.project_list.installEventFilter( self )
        self.layout.page_list.installEventFilter( self )
        self.layout.mode.installEventFilter( self )
    def Modules( self ):
        self.notifier = Krita.instance().notifier()
        self.notifier.applicationClosing.connect( self.Application_Closing )
        self.notifier.configurationChanged.connect( self.Configuration_Changed )
        self.notifier.imageClosed.connect( self.Image_Closed )
        self.notifier.imageCreated.connect( self.Image_Created )
        self.notifier.imageSaved.connect( self.Image_Saved )
        self.notifier.viewClosed.connect( self.View_Closed )
        self.notifier.viewCreated.connect( self.View_Created )
        self.notifier.windowCreated.connect( self.Window_Created )
        self.notifier.windowIsBeingCreated.connect( self.Window_IsBeingCreated )
    def Style( self ):
        # QIcons
        self.qicon_project = Krita.instance().icon( 'bundle_archive' )
        self.qicon_page = Krita.instance().icon( 'zoom-print' )
        self.qicon_export = Krita.instance().icon( 'document-export' )
        qicon_settings = Krita.instance().icon( 'settings-button' )

        # Widget
        self.layout.mode.setIcon( self.qicon_project )
        self.layout.export_selection.setIcon( self.qicon_export )
        self.layout.settings.setIcon( qicon_settings )

        # ToolTips
        self.layout.mode.setToolTip( "ZIP" )
        self.layout.active_project.setToolTip( "Active Project" )
        self.layout.page_index.setToolTip( "Page Index" )
        self.layout.settings.setToolTip( "Settings" )

        # StyleSheets
        self.layout.progress_bar.setStyleSheet( "#progress_bar{background-color: rgba( 0, 0, 0, 0 );}" )
        self.dialog.scroll_area_contents_template.setStyleSheet( "#scroll_area_contents_template{background-color: rgba( 0, 0, 0, 20 );}" )
        self.dialog.scroll_area_contents_information.setStyleSheet( "#scroll_area_contents_information{background-color: rgba( 0, 0, 0, 20 );}" )
        self.dialog.scroll_area_contents_guides.setStyleSheet( "#scroll_area_contents_guides{background-color: rgba( 0, 0, 0, 20 );}" )
        self.dialog.scroll_area_contents_layers.setStyleSheet( "#scroll_area_contents_layers{background-color: rgba( 0, 0, 0, 20 );}" )
        self.dialog.scroll_area_contents_system.setStyleSheet( "#scroll_area_contents_system{background-color: rgba( 0, 0, 0, 20 );}" )
        self.dialog.progress_bar.setStyleSheet( "#progress_bar{background-color: rgba( 0, 0, 0, 0 );}" )

        # Populate Combobox
        for i in range( 0, len( self.doc_template ) ):
            self.dialog.doc_template.addItem( self.doc_template[i]["index"] )
        self.dialog.doc_template.setCurrentText( "Paper A4" )
    def Timer( self ):
        if check_timer >= 30:
            self.timer_pulse = QtCore.QTimer( self )
            self.timer_pulse.timeout.connect( self.Krita_to_ProjectPages )
    def Extension( self ):
        # Install Extension for Docker
        extension = ProjectPages_Extension( parent = Krita.instance() )
        Krita.instance().addExtension( extension )
    def Settings( self ):
        # Directory Path
        project_recent = self.Set_Read( "EVAL", "project_recent", self.project_recent )
        for i in range( 0, len( project_recent ) ):
            path = project_recent[i]
            exists = os.path.exists( path )
            if exists == True:
                self.project_recent.append( path )

        # Note
        self.note_textwrap = self.Set_Read( "EVAL", "note_textwrap", self.note_textwrap )

        # Rename Strings
        self.layer_string = self.Set_Read( "EVAL", "layer_string", self.layer_string )

        # Show on Welcome
        self.sow_project = self.Set_Read( "EVAL", "sow_project", self.sow_project )
        self.sow_dockers = self.Set_Read( "EVAL", "sow_dockers", self.sow_dockers )

        # Export
        self.export_width_state = self.Set_Read( "EVAL", "export_width_state", self.export_width_state )
        self.export_height_state = self.Set_Read( "EVAL", "export_height_state", self.export_height_state )
        self.export_width_value = self.Set_Read( "INT", "export_width_value", self.export_width_value )
        self.export_height_value = self.Set_Read( "INT", "export_height_value", self.export_height_value )
    def Plugin_Load( self ):
        try:
            self.Loader()
        except Exception as e:
            self.Message_Warnning( "ERROR", f"Load\n{ e }" )
            self.Variables()
            self.Loader()

    def Loader( self ):
        # Directory Path
        self.Project_Thumbnail( self.project_recent )

        # Note Text Wrap
        self.dialog.note_textwrap.setChecked( self.note_textwrap )

        # Rename Strings
        self.Rename_LOAD( self.layer_string )

        # Show on Welcome
        self.dialog.sow_project.setChecked( self.sow_project )
        self.dialog.sow_dockers.setChecked( self.sow_dockers )

        # Export
        self.Export_Load_Block( True )
        self.dialog.export_width_state.setChecked( self.export_width_state )
        self.dialog.export_height_state.setChecked( self.export_height_state )
        self.dialog.export_width_value.setValue( self.export_width_value )
        self.dialog.export_height_value.setValue( self.export_height_value )
        self.Export_Load_Block( False )
    def Set_Read( self, mode, entry, default ):
        setting = Krita.instance().readSetting( "Project Pages", entry, "" )
        if setting == "":
            read = default
        else:
            try:
                if mode == "EVAL":
                    read = eval( setting )
                elif mode == "STR":
                    read = str( setting )
                elif mode == "INT":
                    read = int( setting )
            except:
                read = default
        Krita.instance().writeSetting( "Project Pages", entry, str( read ) )
        return read

    #endregion
    #region Menu

    # Context Menus
    def Menu_ProjectContext( self, event ):
        #region Variables

        # Variables
        project_active = self.project_active
        # Selected Items
        count = self.layout.project_list.count()
        select_item = self.layout.project_list.selectedItems()
        select_length = len( select_item )
        for i in range( 0, select_length ):
            select_item[i] = select_item[i].text()

        #endregion
        #region Menu

        # Menu
        qmenu = QMenu( self )
        qmenu_header = qmenu.addSection( "Project" )
        action_open = qmenu.addAction( "Open" )
        action_save = qmenu.addAction( "Save" )
        action_location = qmenu.addAction( "Location" )
        qmenu.addSeparator()
        action_new = qmenu.addAction( "New" )
        action_import = qmenu.addAction( "Import" )
        action_search = qmenu.addAction( "Search" )
        qmenu.addSeparator()
        action_clear = qmenu.addAction( "Clear" )
        action_close = qmenu.addAction( "Close" )

        # Disable
        if ( project_active == True or select_length == 0 ):
            action_open.setEnabled( False )
        if project_active == False:
            action_save.setEnabled( False )
        if select_length == 0:
            action_location.setEnabled( False )
        if project_active == True:
            action_new.setEnabled( False )
            action_import.setEnabled( False )
            action_search.setEnabled( False )
        if ( project_active == True or select_length == 0 ):
            action_clear.setEnabled( False )
        if project_active == False:
            action_close.setEnabled( False )

        #endregion
        #region Actions

        # Execute
        position = event.globalPos()
        action = qmenu.exec_( position )

        # Triggers
        if action == action_open:
            # self.Project_Recent_Open( select_item[0] )
            self.Project_Open()
        if action == action_save:
            self.ZIP_Save()
        if action == action_location:
            index = self.layout.project_list.currentRow()
            path = self.project_recent[index]
            self.File_Location( path, "SELECT" )
        if action == action_new:
            self.Project_New()
        if action == action_import:
            self.Project_Import()
        if action == action_search:
            self.Project_Search()
        if action == action_clear:
            self.Project_Recent_Clear( select_item[0] )
        if action == action_close:
            self.ZIP_Close()

        #endregion
    def Menu_PageContext( self, event ):
        if self.project_active == True:
            #region Variable

            # Selected Items
            select_item = self.layout.page_list.selectedItems()
            select_length = len( select_item )
            for i in range( 0, select_length ):
                select_item[i] = select_item[i].text()
            # All Items are Closed Check
            closed = self.Items_Closed()

            #endregion
            #region Menu

            # Menu
            qmenu = QMenu( self )
            action_header = qmenu.addSection( "Page" )
            action_open = qmenu.addAction( "Open" )
            action_new = qmenu.addAction( "New" )
            action_import = qmenu.addAction( "Import" )
            action_search = qmenu.addAction( "Search" )
            menu_batch = qmenu.addMenu( "Batch" )
            action_rename = menu_batch.addAction( "Rename" )
            action_export = menu_batch.addAction( "Export" )
            action_thumbnail = qmenu.addAction( "Thumbnail" )
            action_trash = qmenu.addAction( "Trash" )

            # Disable
            if select_length == 0:
                action_open.setEnabled( False )
            if closed == False:
                menu_batch.setEnabled( False )
                action_rename.setEnabled( False )
                action_export.setEnabled( False )
            if select_length == 0:
                action_thumbnail.setEnabled( False )
                action_trash.setEnabled( False )

            #endregion
            #region Action

            # Execute
            position = event.globalPos()
            action = qmenu.exec_( position )

            # Triggers
            if action == action_open:
                self.Page_Open()
            if action == action_new:
                self.Page_New()
            if action == action_import:
                self.Page_Import()
            if action == action_search:
                self.Page_Search()
            if action == action_rename:
                self.Page_Rename()
            if action == action_export:
                self.Page_Export()
            if action == action_thumbnail:
                self.Page_Project_Thumbnail( select_item[0] )
            if action == action_trash:
                self.Page_Trash( select_item )

            #endregion
    def Menu_DirectoryContext( self, event ):
        if self.project_active == True:
            # Folder
            directory = self.project_directory
            dirfiles = os.listdir( directory )
            fullpaths = map( lambda name: os.path.abspath( os.path.join( directory, name ) ), dirfiles )
            folders = []
            folders.append( self.project_directory )
            for f in fullpaths:
                if os.path.isdir( f ):
                    folders.append( f )
            if len( folders ) > 0:
                folders.sort()

            # Actions
            qmenu = QMenu( self )
            actions = {}
            for i in range( 0, len( folders ) ):
                child = str( os.path.basename( folders[i] ) )
                actions[i] = qmenu.addAction( child )

            # Execute
            geo = self.layout.mode.geometry()
            qpoint = geo.bottomLeft()
            position = self.layout.footer_widget.mapToGlobal( qpoint )
            action = qmenu.exec_( position )

            # Triggers
            for i in range( 0, len( folders ) ):
                if action == actions[i]:
                    path = str( folders[i] )
                    self.File_Location( path, "OPEN" )
                    break

    # Note
    def Note_TextWrap( self, boolean ):
        self.note_textwrap = boolean
        if boolean == False:
            self.layout.text_note.setLineWrapMode( QTextEdit.NoWrap )
        if boolean == True:
            self.layout.text_note.setLineWrapMode( QTextEdit.WidgetWidth )
        Krita.instance().writeSetting( "Project Pages", "note_textwrap", str( self.note_textwrap ) )

    # Page Template
    def Document_Basename( self, doc_basename ):
        self.doc_basename = doc_basename
        Krita.instance().writeSetting( "Project Pages", "doc_basename", str( self.doc_basename ) )
        self.Control_Save()
        self.update()
    def Document_Template( self, current_text ):
        for i in range( 0, len( self.doc_template ) ):
            index = self.doc_template[i]["index"]
            if current_text == index:
                # Read
                if self.doc_swap == False:
                    width = self.doc_template[i]["width"]
                    height = self.doc_template[i]["height"]
                elif self.doc_swap == True:
                    width = self.doc_template[i]["height"]
                    height = self.doc_template[i]["width"]
                # Widget
                if width != None:
                    self.dialog.doc_width.setValue( width )
                if height != None:
                    self.dialog.doc_height.setValue( height )
                break
    def Document_Dim_Width( self, doc_width ):
        self.doc_width = doc_width
        self.Doc_Custom_Check()
        self.Control_Save()
        self.update()
    def Document_Dim_Height( self, doc_height ):
        self.doc_height = doc_height
        self.Doc_Custom_Check()
        self.Control_Save()
        self.update()
    def Document_Dim_Swap( self, doc_swap ):
        self.doc_swap = doc_swap
        self.Document_Template( self.dialog.doc_template.currentText() )
        Krita.instance().writeSetting( "Project Pages", "doc_swap", str( self.doc_swap ) )
        self.Control_Save()
        self.update()
    def Document_Color_Space( self, doc_colorspace ):
        self.doc_colorspace = doc_colorspace
        Krita.instance().writeSetting( "Project Pages", "doc_colorspace", str( self.doc_colorspace ) )
        self.Control_Save()
        self.update()
    def Document_Bit_Depth( self, doc_bitdepth ):
        self.doc_bitdepth = doc_bitdepth
        Krita.instance().writeSetting( "Project Pages", "doc_bitdepth", str( self.doc_bitdepth ) )
        self.Control_Save()
        self.update()
    def Document_DPI( self, doc_dpi ):
        self.doc_dpi = doc_dpi
        Krita.instance().writeSetting( "Project Pages", "doc_dpi", str( self.doc_dpi ) )
        self.Control_Save()
        self.update()
    def Document_GH_List( self, doc_gh ):
        self.doc_gh = self.string_lista( doc_gh )
        Krita.instance().writeSetting( "Project Pages", "doc_gh", str( self.doc_gh ) )
        self.Control_Save()
        self.update()
    def Document_GV_List( self, doc_gv ):
        self.doc_gv = self.string_lista( doc_gv )
        Krita.instance().writeSetting( "Project Pages", "doc_gv", str( self.doc_gv ) )
        self.Control_Save()
        self.update()
    def Document_GH_Import( self, pushbutton_gh ):
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            gh = self.guide_string( self.dialog.guide_horizontal_list )
            self.dialog.doc_gh.setText( gh )
    def Document_GV_Import( self, pushbutton_gv ):
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            gv = self.guide_string( self.dialog.guide_vertical_list )
            self.dialog.doc_gv.setText( gv )

    # System
    def ShowOnWelcome_Project( self, sow_project ):
        self.sow_project = sow_project
        try:self.setProperty( "ShowOnWelcomePage", sow_project )
        except:pass
        Krita.instance().writeSetting( "Project Pages", "sow_project", str( self.sow_project ) )
    def ShowOnWelcome_Dockers( self, sow_dockers ):
        self.sow_dockers = sow_dockers
        Krita.instance().writeSetting( "Project Pages", "sow_dockers", str( self.sow_dockers ) )
    def Welcome_Dockers( self ):
        # Project Pages
        if self.sow_project == True:
            try:self.setProperty( "ShowOnWelcomePage", True )
            except:pass
        # Dockers
        if self.sow_dockers == True:
            dockers = Krita.instance().dockers()
            for d in dockers:
                try:d.setProperty( "ShowOnWelcomePage", True )
                except:pass

    # Tabs
    def Menu_Tabs( self ):
        self.Information_Read()

    # Dialogs
    def Menu_Settings( self ):
        # Display
        self.dialog.show()
        # Resize Geometry
        qmw = Krita.instance().activeWindow().qwindow()
        px = qmw.x()
        py = qmw.y()
        w2 = qmw.width() * 0.5
        h2 = qmw.height() * 0.5
        size = 500
        self.dialog.setGeometry( int( px + w2 - size * 0.5 ), int( py + h2 - size * 0.5 ), int( size ), int( size ) )
    def Menu_Manual( self ):
        url = "https://github.com/EyeOdin/project_pages/wiki"
        webbrowser.open_new( url )
    def Menu_License( self ):
        url = "https://github.com/EyeOdin/project_pages/blob/main/LICENSE"
        webbrowser.open_new( url )
    def Dialog_Block( self, boolean ):
        # Document Template
        self.dialog.doc_basename.blockSignals( boolean )
        self.dialog.doc_template.blockSignals( boolean )
        self.dialog.doc_width.blockSignals( boolean )
        self.dialog.doc_height.blockSignals( boolean )
        self.dialog.doc_swap.blockSignals( boolean )
        self.dialog.doc_colorspace.blockSignals( boolean )
        self.dialog.doc_bitdepth.blockSignals( boolean )
        self.dialog.doc_dpi.blockSignals( boolean )
        # Guides
        self.dialog.doc_gh.blockSignals( boolean )
        self.dialog.doc_gv.blockSignals( boolean )
        self.dialog.pushbutton_gh.blockSignals( boolean )
        self.dialog.pushbutton_gv.blockSignals( boolean )

    #endregion
    #region Management

    def Message_Log( self, operation, message ):
        string = f"Project Pages | { operation } { message }"
        try:QtCore.qDebug( string )
        except:pass
    def Message_Warnning( self, operation, message ):
        string = f"Project Pages | { operation } { message }"
        QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( string ) )
    def Message_Float( self, operation, message, icon ):
        ki = Krita.instance()
        string = f"Project Pages | { operation } { message }"
        try:ki.activeWindow().activeView().showFloatingMessage( string, ki.icon( icon ), 5000, 0 )
        except:pass

    def Limit_Range( self, value, minimum, maximum ):
        if value <= minimum:
            value = minimum
        if value >= maximum:
            value = maximum
        return value
    def Limit_Loop( self, index, limit ):
        if index > limit:
            index = 0
        return index

    def Path_Components( self, path ):
        directory = os.path.dirname( path ) # dir
        basename = os.path.basename( path ) # name.ext
        extension = os.path.splitext( path )[1] # .ext
        n = basename.find( extension )
        name = basename[:n] # name
        return name

    def Check_Active( self ):
        check = False
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            active = os.path.abspath( Krita.instance().activeDocument().fileName() )
            for i in range( 0, len( self.found_images ) ): # Project Pages Open
                page_i = os.path.abspath( self.found_images[i] )
                if active == page_i:
                    check = True
                    break
        return check
    def Check_Documents( self ):
        check = True
        documents = Krita.instance().documents()
        for d in range( 0, len( documents ) ):
            doc_d = os.path.abspath( documents[d].fileName() )
            for i in range( 0, len( self.found_images ) ): # Project Pages Open
                page_i = os.path.abspath( self.found_images[i] )
                if doc_d == page_i:
                    check = False
                    break
        return check

    def Items_All( self ):
        count = self.layout.page_list.count()
        all_items = []
        for i in range( 0, count ):
            item = self.layout.page_list.item( i ).text()
            all_items.append( item )
        return all_items

    def Read_Nodes( self, document ):
        # Document
        top_nodes = document.topLevelNodes()

        # Top level Nodes
        new_nodes = []
        for i in range( 0, len( top_nodes ) ):
            new_nodes.append( top_nodes[i] )

        # Variables
        check_again = True
        counter = 0
        node_dic = {
        0 : new_nodes,
        }
        # Infinite Cycle
        while check_again == True:
            # layer read
            new_nodes = []
            nodes = node_dic[counter]
            # Layer Level
            for i in range( 0, len( nodes ) ):
                try:
                    child_nodes = nodes[i].childNodes()
                    if len( child_nodes ) > 0:
                        for cn in range( 0, len( child_nodes ) ):
                            new_nodes.append( child_nodes[cn] )
                except:
                    pass

            # cycle control
            if len( new_nodes ) == 0:
                check_again = False
            else:
                counter += 1
                node_dic[counter] = new_nodes

        # Return List
        return_list = []
        for i in range( 0, len( node_dic ) ):
            for j in range( 0, len( node_dic[i] ) ):
                node = node_dic[i][j]
                return_list.append( node )
        return return_list
    def Doc_Custom_Check( self ):
        # Read
        width = self.dialog.doc_width.value()
        height = self.dialog.doc_height.value()
        # Write
        self.doc_width = width
        self.doc_height = height

        # Index Swap
        self.dialog.doc_template.blockSignals( True )
        index = None
        for i in range( 0, len( self.doc_template )-1 ):
            entry = self.doc_template[i]
            if ( ( width == entry["width"] and height == entry["height"] ) or ( height == entry["width"] and width == entry["height"] ) ):
                index = i
                break
        if index != None:
            self.dialog.doc_template.setCurrentIndex( index )
        else:
            self.dialog.doc_template.setCurrentIndex( len( self.doc_template )-1 )
        self.dialog.doc_template.blockSignals( False )
    def Items_Closed( self ):
        # Variables
        closed = True

        # Documents Read
        documents = Krita.instance().documents()
        doc_list = []
        for d in range( 0, len( documents ) ):
            name = os.path.basename( documents[d].fileName() )
            doc_list.append( name )
        # All Items Read
        count = self.layout.page_list.count()
        all_items = []
        for i in range( 0, count ):
            item = self.layout.page_list.item( i ).text()
            all_items.append( item )

        # Check
        closed = True
        for i in range( 0, len( doc_list ) ):
            for j in range( 0, len( all_items ) ):
                if doc_list[i] == all_items[j]:
                    closed = False
                    break
        return closed

    def string_lista( self, string ):
        string = string.replace( " ", "" )
        splits = string.split( "," )
        lista = []
        for i in range( 0, len( splits ) ):
            try:
                number = float( splits[i] )
                lista.append( number )
            except:
                pass
        return lista
    def guide_string( self, widget ):
        count = widget.count()
        guide = ""
        for i in range( 0, count ):
            item_i = widget.item( i )
            text = item_i.text() + ", "
            guide += text
        guide = guide[0:-2]
        return guide

    def Resize_Print( self, event ):
        # Used doing a photoshoot
        width = self.width()
        height = self.height()
        QtCore.qDebug( "size = " + str( width ) + " x "  + str( height ) )

    def Print_Path( self ):
        QtCore.qDebug( "---------------------" )
        QtCore.qDebug( f"project_zip       = { self.project_zip }" )
        QtCore.qDebug( f"project_directory = { self.project_directory }" )
        QtCore.qDebug( f"project_control   = { self.project_control }" )
        QtCore.qDebug( f"project_images    = { self.project_images }" )
        QtCore.qDebug( f"project_texts     = { self.project_texts }" )
        QtCore.qDebug( f"project_trash     = { self.project_trash }" )
        QtCore.qDebug( f"project_recent    = { self.project_recent }" )

    #endregion
    #region Project Pages and Krita

    def Krita_to_ProjectPages( self ):
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            try:
                # Read Document
                ad = Krita.instance().activeDocument()
                guide_horizontal_list = ad.horizontalGuides()
                guide_vertical_list = ad.verticalGuides()
                guide_ruler = Krita.instance().action( "view_ruler" ).isChecked()
                guide_snap = Krita.instance().action( "view_snap_to_guides" ).isChecked()
                guide_visible = ad.guidesVisible()
                guide_lock = ad.guidesLocked()

                # Correct lists error range
                for i in range( 0, len( guide_horizontal_list ) ):
                    guide_horizontal_list[i] = round( guide_horizontal_list[i], 2 )
                guide_horizontal_list = sorted( guide_horizontal_list )
                for i in range( 0, len( guide_vertical_list ) ):
                    guide_vertical_list[i] = round( guide_vertical_list[i], 2 )
                guide_vertical_list = sorted( guide_vertical_list )

                # Update Document
                if self.guide_horizontal_list != guide_horizontal_list:
                    self.Guide_Horizontal_List( guide_horizontal_list )
                if self.guide_vertical_list != guide_vertical_list:
                    self.Guide_Vertical_List( guide_vertical_list )
                if self.guide_ruler != guide_ruler:
                    self.Guide_Ruler( guide_ruler )
                if self.guide_snap != guide_snap:
                    self.Guide_Snap( guide_snap )
                if self.guide_visible != guide_visible:
                    self.Guide_Visible( guide_visible )
                if self.guide_lock != guide_lock:
                    self.Guide_Lock( guide_lock )
            except:
                pass
        else:
            self.Default_State()
    def Default_State( self ):
        if self.guide_horizontal_list != []:
            self.Guide_Horizontal_List( [] )
        if self.guide_vertical_list != []:
            self.Guide_Vertical_List( [] )
        if self.guide_ruler != False:
            self.Guide_Ruler( False )
        if self.guide_snap != False:
            self.Guide_Snap( False )
        if self.guide_visible != False:
            self.Guide_Visible( False )
        if self.guide_lock != False:
            self.Guide_Lock( False )

    #endregion
    #region Index

    def Index_Range( self, images, texts ):
        # Variables
        self.found_index["image"] = 0
        self.found_index["text"] = 0

        # Block Signals
        self.layout.page_index.blockSignals( True )
        # Widget
        check = len( images ) == len( texts ) and len( images ) > 0 and len( texts ) > 0
        if check == True:
            num = 1
            total = len( images )
            self.layout.page_index.setMinimum( 1 )
            self.layout.page_index.setMaximum( total )
        else:
            num = 0
            total = 0
            self.layout.page_index.setMinimum( 0 )
            self.layout.page_index.setMaximum( 0 )
        self.layout.page_index.setValue( num )
        self.layout.page_index.setSuffix( f":{ total }" )
        # Block Signals
        self.layout.page_index.blockSignals( False )
    def Index_Number( self, index ):
        # Widgets
        self.layout.page_list.setCurrentRow( index - 1 )
        # Update Index
        self.Index_Set()
    def Index_Set( self ):
        check_image = len( self.found_images )
        check_text = len( self.found_texts )
        item = self.layout.page_list.currentItem()
        if ( item != None and check_image > 0 and check_text > 0 ):
            text = item.text()
            image_name = text.split( "." )[0]

            # Search Matching Files
            for i in range( 0, len( self.found_texts ) ):
                path = self.found_texts[i]
                name = self.Path_Components( self.found_texts[i] )
                if image_name == name:
                    # Index
                    self.found_index["image"] = self.layout.page_list.currentRow() # Widget index
                    self.found_index["text"] = i # file index
                    # Read Text
                    with open( path, "r" ) as note:
                        data = note.read()
                        note.close()
                        # Widget
                        self.layout.text_note.clear()
                        self.layout.text_note.setText( str( data ) )
                        break

    #endregion
    #region Panels

    def Text_Load( self ):
        if self.project_active == True:
            # Update Index
            self.Index_Set()
            # Index
            index = int( self.found_index["image"] ) + 1
            total = ":" + str( len( self.found_images ) )
            self.layout.page_index.blockSignals( True )
            self.layout.page_index.setValue( index )
            self.layout.page_index.setSuffix( total )
            self.layout.page_index.blockSignals( False )
    def Text_Save( self ):
        if ( self.project_active == True and len( self.found_texts ) > 0 ):
            text_block = self.layout.text_note.toPlainText()
            file_txt = self.found_texts[ self.found_index["text"] ]
            note = open( file_txt, "w" )
            note.write( text_block )
            note.close()

    #endregion
    #region Project

    def Project_New( self ):
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        path = file_dialog.getExistingDirectory( self, "Select Project Directory" )
        if ( path != "" and path != "." ):
            name, boolean = QtWidgets.QInputDialog.getText( self, 'Project Pages', 'Select Project Name' )
            if boolean == True:
                self.ZIP_New( path, f"{ name }.project_pages" )
    def Project_Import( self ):
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.AnyFile )
        path = file_dialog.getOpenFileName( self, f"Select Project { file_extension.upper() } File", "", f"*.{ file_extension }" )[0]
        if ( path != "" and path != "." and self.project_zip != path ):
            self.ZIP_Open( path )
    def Project_Open( self ):
        index = self.layout.project_list.currentRow()
        item = self.project_recent[index]
        self.ZIP_Open( item )
        self.Project_Recent_Add( item )
    def Project_Search( self ):
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        path = file_dialog.getExistingDirectory( self, "Select Search Directory" )
        if ( path != "" and path != "." ):
            self.File_Search( path, "PROJECT" )

    def Project_Recent_Add( self, path ):
        # List Limit
        limit = 100
        length = len( self.project_recent )
        if length > limit:
            self.project_recent.pop( -1 )
        # Insert Path to List
        if path in self.project_recent:
            self.project_recent.remove( path )
        self.project_recent.insert( 0, path )
        # Update
        self.Project_Thumbnail( self.project_recent )
        Krita.instance().writeSetting( "Project Pages", "project_recent", str( self.project_recent ) )
    def Project_Recent_Minus( self, path ):
        # Minus from List
        if path in self.project_recent:
            index = self.project_recent.index( path )
            self.project_recent.pop( index )
        # Update
        self.Project_Thumbnail( self.project_recent )
        Krita.instance().writeSetting( "Project Pages", "project_recent", str( self.project_recent ) )
    def Project_Recent_Clear( self, project_item ):
        for i in range( 0, len( self.project_recent ) ):
            name = os.path.basename( self.project_recent[i] ).replace( ".project_pages.zip", "" )
            if name == project_item:
                path = self.project_recent[i]
                self.Project_Recent_Minus( path )
                break
        self.Project_Thumbnail( self.project_recent )
        Krita.instance().writeSetting( "Project Pages", "project_recent", str( self.project_recent ) )

    def Project_Thumbnail( self, project_recent ):
        # Clean Previous
        self.layout.project_list.clear()

        # Items
        for i in range( 0, len( project_recent ) ):
            # Variables
            path = project_recent[i]
            basename = os.path.basename( path ).replace( ".project_pages.zip", "" )
            # Create Items
            item = QListWidgetItem( basename )
            size = 100
            # Thumbnail
            bg = QPixmap( size, size )
            bg.fill( self.color_alpha )
            # Zip File Thumbnail
            if zipfile.is_zipfile( path ):
                name = "thumbnail.png"
                archive = zipfile.ZipFile( path, "r" )
                data = archive.open( name ).read()
                qpixmap = QPixmap()
                qpixmap.loadFromData( data )
                if qpixmap.isNull() == False:
                    # Scale
                    pix = qpixmap.scaled( size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation )
                    # Variable
                    w = pix.width()
                    h = pix.height()
                    px = int( ( size*0.5 ) - ( w*0.5 ) )
                    py = int( ( size*0.5 ) - ( h*0.5 ) )
                    # Composed Image
                    painter = QPainter( bg )
                    painter.drawPixmap( px, py, pix )
                    painter.end()
                    # Item
                    qicon = QIcon( bg )
                    item.setIcon( qicon )
                    self.layout.project_list.addItem( item )

    #endregion
    #region ZIP operations

    def ZIP_New( self, path, name ):
        if self.project_active == False:
            # Paths
            project_directory = os.path.abspath( os.path.join( path , name ) )
            project_zip = project_directory + "." + file_extension

            exists = ( os.path.exists( project_directory ) ) and ( os.path.exists( project_zip ) )
            if exists == False:
                # Recent Projects
                self.Project_Recent_Add( project_zip )

                # Paths
                self.project_zip = os.path.abspath ( project_zip )
                self.project_directory = project_directory
                self.project_control = os.path.abspath( os.path.join( project_directory, "control.eo" ) )
                self.project_thumbnail = os.path.abspath( os.path.join( project_directory, "thumbnail.png" ) )
                self.project_images = os.path.abspath( os.path.join( project_directory, "IMAGES" ) )
                self.project_texts = os.path.abspath( os.path.join( project_directory, "TEXTS" ) )
                self.project_trash = os.path.abspath( os.path.join( project_directory, "TRASH" ) )

                # Create Project Folders
                os.mkdir( self.project_directory )
                os.mkdir( self.project_images )
                os.mkdir( self.project_texts )
                os.mkdir( self.project_trash )

                # Create Project TXT
                file = open( self.project_control, "w" )
                file.write( "project_pages" )
                # Create Thumbnail
                qimage = QImage( self.thumbnail_size, self.thumbnail_size, QImage.Format_RGBA8888 )
                qimage.fill( self.color_thumbnail )
                qimage.save( self.project_thumbnail )

                # Create File ZIP
                shutil.make_archive( self.project_directory, 'zip', self.project_directory ) # Creates the ZIP

                # Update
                project_displayname = os.path.basename( self.project_zip )
                self.layout.active_project.setText( project_displayname.replace( ".project_pages.zip", "" ) )
                self.dialog.label_project_active.setText( project_displayname )
                self.project_active = True
                self.File_List()

                # Thumbnails
                self.Project_Thumbnail( self.project_recent )

                # Widgets
                self.layout.page_list.setEnabled( True )
                self.layout.text_note.setEnabled( True )

                # Control
                self.Control_Save()
                self.ZIP_Save()
            else:
                self.File_Conflict( project_directory )
    def ZIP_Open( self, project_zip ):
        if self.project_active == False:
            # Variables
            basename = os.path.basename( project_zip )
            name = basename.replace( ".project_pages.zip", ".temp" )
            parent = os.path.dirname( project_zip )

            # Paths
            project_zip = os.path.abspath( project_zip )
            project_directory = os.path.abspath( os.path.join( parent, name ) )

            # Filename is Open
            exists = os.path.exists( project_directory )
            if exists == False:
                # Check if it is a valid Project_Pages ZIP file
                valid = False
                if zipfile.is_zipfile( project_zip ):
                    # Open Zip
                    archive = zipfile.ZipFile( project_zip, "r" )
                    name_list = archive.namelist()
                    # Structure Verification
                    check_structure = False
                    item = 0
                    for i in range( 0, len( structure ) ):
                        if structure[i] in name_list:
                            item += 1
                    check_structure = item == len( structure )
                    # Valid
                    if check_structure == True:
                        valid = True

                # Open the Valid ZIP file
                if valid == True:
                    # Recent Projects
                    self.Project_Recent_Add( project_zip )

                    # Variables
                    self.project_active = True
                    self.project_zip = project_zip
                    self.project_directory = project_directory
                    self.project_control = os.path.abspath( os.path.join( project_directory, "control.eo" ) )
                    self.project_thumbnail = os.path.abspath( os.path.join( project_directory, "thumbnail.png" ) )
                    self.project_images = os.path.abspath( os.path.join( project_directory, "IMAGES" ) )
                    self.project_texts = os.path.abspath( os.path.join( project_directory, "TEXTS" ) )
                    self.project_trash = os.path.abspath( os.path.join( project_directory, "TRASH" ) )

                    # Display
                    self.layout.active_project.setText( basename.replace( ".project_pages.zip", "" ) )
                    self.dialog.label_project_active.setText( basename )

                    # Unzip Project
                    shutil.unpack_archive( self.project_zip, self.project_directory )

                    # Update
                    self.File_List()
                    self.Index_Range( self.found_images, self.found_texts )

                    # Control
                    self.Control_Load()

                    # Thumbnails
                    self.Project_Thumbnail( self.project_recent )

                    # Widgets
                    self.layout.page_list.setEnabled( True )
                    self.layout.text_note.setEnabled( True )
                else:
                    self.Project_Recent_Minus( project_zip )
                    self.Message_Warnning( "ERROR", "Invalid File\nSuggestion : Import files into a new project" )
            else:
                self.File_Conflict( project_directory )
    def ZIP_Save( self ):
        if self.project_active == True:
            destination = self.project_zip.replace( ".zip", "" ) # Zip is added with the archive format
            shutil.make_archive( destination, 'zip', self.project_directory )
            self.File_List()
            self.Message_Float( "SAVE", "Complete", "document-save" )
    def ZIP_Close( self ):
        if self.project_active == True:
            # Ask user if Project Folder should be deleted
            string = "Delete Temporary Project Folder ?\n\nThis will not affect your project ZIP file\n"
            boolean = QMessageBox.question( self, "Project Pages", string, QMessageBox.Yes, QMessageBox.No )
            if boolean == QMessageBox.Yes:
                self.ZIP_Exit( self.project_directory )

            # Update variables
            self.project_active = False
            self.project_zip = None
            self.project_directory = None
            self.project_control = None
            self.project_images = None
            self.project_texts = None
            self.project_trash = None
            self.found_images = []
            self.found_texts = []

            # Update widgets
            self.layout.page_list.clear()
            self.layout.text_note.clear()
            self.Index_Range( self.found_images, self.found_texts )
            # Text Display
            self.layout.active_project.setText( "" )
            self.dialog.label_project_active.setText( "" )
            # Enabled
            self.layout.page_list.setEnabled( False )
            self.layout.text_note.setEnabled( False )
    def ZIP_Exit( self, project_directory ):
        if ( self.project_active == True and os.path.isdir( project_directory ) == True ):
            try:shutil.rmtree( project_directory )
            except:pass

    #endregion
    #region Pages

    def Page_New( self ):
        if self.project_active == True:
            # Taken Names
            taken_names = []
            count = self.layout.page_list.count()
            for i in range( 0, count ):
                text = self.layout.page_list.item( i ).text()
                taken_names.append( text )

            # Check with Taken Names
            limit = len( self.found_images ) + 10
            for i in range( 1, limit ):
                name = self.doc_basename + "_" + str( i ).zfill( 4 )
                check_name = name + ".kra"
                if check_name not in taken_names:
                    # Paths
                    file_img = os.path.abspath( os.path.join( self.project_images, f"{ name }.kra" ) )
                    file_txt = os.path.abspath( os.path.join( self.project_texts, f"{ name }.eo" ) )

                    # Texts
                    note = open( file_txt, "w" )
                    note.write( "" )
                    note.close()

                    # Image
                    new_document = Krita.instance().createDocument(
                        self.doc_width, self.doc_height,
                        self.doc_basename,
                        self.doc_colorspace, self.doc_bitdepth, "", self.doc_dpi
                        )
                    Krita.instance().activeWindow().addView( new_document ) # shows it in the application
                    new_document.setFullClipRangeStartTime( 0 )
                    new_document.setFullClipRangeEndTime( 0 ) # Ensures Animation Length to reflect Animation size on start
                    Krita.instance().action( 'add_new_paint_layer' ).trigger() # create a layer to paint
                    Krita.instance().activeDocument().saveAs( file_img ) # save file to project folder

                    # Guide
                    Krita.instance().activeDocument().setHorizontalGuides( list( self.doc_gh ) )
                    Krita.instance().activeDocument().setVerticalGuides( list( self.doc_gv ) )

                    break

        # Update
        self.Page_Update()
    def Page_Import( self ):
        if self.project_active == True:
            # Extensions to Search
            lista = file_image.copy()
            lista.remove( "*.zip" )
            string = ""
            for i in range( 0, len( lista ) ):
                string += f"{ lista[i] } "
            string = string[:-1]
            filter_images = f"Images ( { string } )"

            # Open Files
            file_dialog = QFileDialog( QWidget( self ) )
            file_dialog.setFileMode( QFileDialog.AnyFile )
            source = file_dialog.getOpenFileNames( self, "Select Files", "", filter_images )
            source = list( source[0] )
            for item in source:
                if ( item != "" and item != "." and item not in self.found_images ):
                    self.Page_Source( item )
        # Update
        self.Page_Update()
    def Page_Source( self, source ):
        # Variables
        destination = self.project_images
        # Copy Image
        shutil.copy( source, destination )
        # Create Text
        name = self.Path_Components( source )
        file_txt = os.path.abspath( os.path.join( self.project_texts, f"{ name }.eo" ) )
        note = open( file_txt, "w" )
        note.write( "" )
        note.close()
    def Page_Search( self ):
        # Select Folder
        file_dialog = QFileDialog( QWidget( self ) )
        file_dialog.setFileMode( QFileDialog.DirectoryOnly )
        directory = file_dialog.getExistingDirectory( self, "Select Search Directory" )
        if ( directory != "" and directory != "." ):
            self.File_Search( directory, "PAGE" )
    def Page_Open( self ):
        if self.project_active == True:
            # Item
            basename = self.layout.page_list.currentItem().text()
            path = os.path.abspath( os.path.join( self.project_images, basename ) )

            # Create Document
            document = Krita.instance().openDocument( path )
            Krita.instance().activeWindow().addView( document )

            # Animation Correction
            return_list = self.Read_Nodes( document )
            animation = False
            for i in range( 0, len( return_list ) ):
                animation = return_list[i].animated()
                if animation == True:
                    break
            if animation == False:
                document.setFullClipRangeStartTime( 0 )
                document.setFullClipRangeEndTime( 0 )
    def Page_Rename( self ):
        if self.project_active == True:
            # Dialog
            name, boolean = QtWidgets.QInputDialog.getText( self, 'Project Pages', 'Rename As' )
            new_name = name.replace( " ", "_" )
            if boolean == True:
                # Check if documents are closed
                closed = self.Check_Documents()
                if closed == True:
                    # All Items
                    all_items = self.Items_All()

                    # Compose Old Paths
                    for i in range( 0, len( all_items ) ):
                        # Parsing
                        item_i = all_items[i]
                        splited = item_i.split( "." )
                        basename_i = splited[0]
                        image_ext = splited[1]
                        num = str( i+1 ).zfill( 4 )
                        # Path OLD
                        old_image  = os.path.abspath( os.path.join( self.project_images, item_i ) )
                        old_backup = os.path.abspath( os.path.join( self.project_images, f"{ item_i }~" ) )
                        old_text   = os.path.abspath( os.path.join( self.project_texts,  f"{ basename_i }.eo" ) )
                        # Path NEW
                        new_image  = os.path.abspath( os.path.join( self.project_images, f"{ new_name }_{ num }.{ image_ext }" ) )
                        new_backup = os.path.abspath( os.path.join( self.project_images, f"{ new_name }_{ num }.{ image_ext }~" ) )
                        new_text   = os.path.abspath( os.path.join( self.project_texts,  f"{ new_name }_{ num }.eo" ) )

                        # Image File
                        try:
                            exists = os.path.exists( new_image )
                            if ( old_image != new_image and exists == False ):
                                os.rename( old_image, new_image )
                        except:
                            pass
                        # Backup File
                        try:
                            exists = os.path.exists( new_backup )
                            if ( old_backup != new_backup and exists == False ):
                                os.rename( old_backup, new_backup )
                        except:
                            pass
                        # Text File
                        try:
                            exists = os.path.exists( new_text )
                            if ( old_text != new_text and exists == False ):
                                os.rename( old_text, new_text )
                        except:
                            pass
                else:
                    self.Page_Conflict()

        # Update
        self.Page_Update()
    def Page_Export( self ):
        if self.project_active == True:
            # Dialog
            file_dialog = QFileDialog( QWidget( self ) )
            file_dialog.setFileMode( QFileDialog.DirectoryOnly )
            export_path = file_dialog.getExistingDirectory( self, "Select Export Directory" )
            if ( export_path != "" and export_path != "." ):

                # Check if documents are closed
                closed = self.Check_Documents()
                if closed == True:
                    # All Items
                    all_items = self.Items_All()
                    limit = len( all_items )

                    # Progress Bar
                    self.layout.progress_bar.setMaximum( limit )
                    self.layout.progress_bar.setValue( 0 )

                    # Start
                    row = self.layout.page_list.currentRow()
                    self.Pages_Block( True )
                    Krita.instance().setBatchmode( True )

                    # Export Document
                    index = 0
                    for i in range( 0, len( all_items ) ):
                        # Progress Bar
                        self.layout.progress_bar.setValue( i + 1 )
                        QApplication.processEvents()

                        # Paths
                        item = all_items[i]
                        extension = item.split( "." )[-1]
                        basename_i = item.replace( f".{ extension }", "" )

                        # Widget
                        self.layout.page_list.setCurrentRow( i )
                        self.layout.text_note.setText( f"Exporting : { item }" )

                        # Path
                        image_path = os.path.abspath( os.path.join( self.project_images, item ) )

                        # Animation
                        if image_path.endswith( ".kra" ) == True:
                            # Document
                            document = Krita.instance().openDocument( image_path )
                            width = document.width()
                            height = document.height()
                            boolean, clip_start, clip_end = self.Animation_Document( document )
                            for anim in range( clip_start, clip_end + 1 ):
                                document.setCurrentTime( anim )
                                document.waitForDone()
                                if boolean == False:
                                    save_path = os.path.abspath( os.path.join( export_path, f"{ basename_i }.png" ) )
                                else:
                                    save_path = os.path.abspath( os.path.join( export_path, f"{ basename_i }_f{ str( anim ).zfill( 4 ) }.png" ) )
                                qimage = document.thumbnail( width, height )
                                qimage.save( save_path )
                                document.waitForDone()
                            document.close()
                        else:
                            save_path = os.path.abspath( os.path.join( export_path, f"{ basename_i }.png" ) )
                            qpixmap = QPixmap( image_path )
                            qpixmap.save( save_path )

                        # Cycle
                        index = self.Limit_Loop( index + 1, limit )

                    # Progress Bar
                    self.layout.progress_bar.setMaximum( limit )
                    self.layout.progress_bar.setValue( 0 )

                    # End
                    self.layout.text_note.clear()
                    Krita.instance().setBatchmode( False )
                    self.Pages_Block( False )

                    # Previous Select
                    self.layout.page_list.setCurrentRow( row )
                else:
                    self.Page_Conflict()

        # Update
        self.Page_Update()
    def Page_Project_Thumbnail( self, name ):
        if ( self.project_active == True and name != None ):
            # File
            temp_ip = os.path.abspath( os.path.join( self.project_directory, "IMAGES" ) )
            image_path = os.path.abspath( os.path.join( temp_ip, name ) )
            qreader = QImageReader( image_path )
            if qreader.canRead() == True:
                qimage = qreader.read()

            # Document
            ad = Krita.instance().activeDocument()
            if ad != None:
                file_name = os.path.basename( ad.fileName() )
                if name == file_name:
                    select = ad.selection()
                    if select != None:
                        qimage = ad.thumbnail( QRect( select.x(), select.y(), select.width(), select.height() ) )
                    else:
                        qimage = ad.thumbnail( ad.width(), ad.height() )

            if qimage.isNull() == False:
                qimage = qimage.scaled( 500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation )
                qimage.save( self.project_thumbnail )
                self.ZIP_Save()

        # Display Update
        self.Project_Thumbnail( self.project_recent )
    def Page_Trash( self, lista ):
        # Variables
        count = len( lista )
        limit = 50
        if count == 1:
            message = "Trash Page ?\n"
        elif count > 1:
            message = "Trash Pages ?\n"
        for i in range( 0, count ):
            if i <= limit:
                message += str( lista[i] ) + "\n"
            else:
                message += "...\n"
                break
        message = message[:-1]

        # Confirmation
        confirm = QMessageBox.question( self,"Project Pages", message, QMessageBox.Yes,QMessageBox.No, )

        # Delete
        if confirm == QMessageBox.Yes and self.project_active == True:
            # Delete
            for i in range( 0, len( lista ) ):
                # Parsing
                item_i = lista[i]
                basename_i = ( item_i.split( "." ) )[0]
                # Variables
                path_image  = os.path.abspath( os.path.join( self.project_images, item_i ) )
                path_backup = os.path.abspath( os.path.join( self.project_images, f"{ item_i }~" ) )
                path_text   = os.path.abspath( os.path.join( self.project_texts,  f"{ basename_i }.eo" ) )

                # Image File
                try:shutil.move( path_image, self.project_trash, copy_function = shutil.copytree )
                except:pass
                # Backup File
                try:shutil.move( path_backup, self.project_trash, copy_function = shutil.copytree )
                except:pass
                # Text File
                try:shutil.move( path_text, self.project_trash, copy_function = shutil.copytree )
                except:pass

        # Update
        self.Page_Update()
    def Page_Update( self ):
        self.File_List()
        self.Index_Range( self.found_images, self.found_texts )

    def Pages_Block( self, boolean ):
        self.layout.page_list.blockSignals( boolean )
        self.layout.text_note.blockSignals( boolean )
    def Animation_Document( self, document ):
        # Read
        animation = document.animationLength() # Problem all documents are created with 101 frames when created
        clip_start = document.fullClipRangeStartTime()
        clip_end = document.fullClipRangeEndTime()
        # Calculation
        if animation == 1:
            boolean = False
        else:
            boolean = True
        # Return
        return boolean, clip_start, clip_end

    def Page_Conflict( self ):
        self.Message_Warnning( "ERROR", "Edit conflict\nClose all active pages from canvas to run" )

    def Page_Thumbnail( self ):
        # Starting Empty
        self.layout.page_list.clear()

        # Images List Draw
        if ( self.project_active == True and len( self.found_images ) > 0 ):
            for i in range( 0, len( self.found_images ) ):
                # Variables
                path = self.found_images[i]
                basename = os.path.basename( path )

                # Create Items
                item = QListWidgetItem( basename )
                size = 100
                # Thumbnail
                bg = QPixmap( size, size )
                bg.fill( self.color_alpha )
                pix = QPixmap( path ).scaled( size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation )
                # Variables
                w = pix.width()
                h = pix.height()
                px = int( ( size * 0.5 ) - ( w * 0.5 ) )
                py = int( ( size * 0.5 ) - ( h * 0.5 ) )
                # Composed Image
                painter = QPainter( bg )
                painter.drawPixmap( px, py, pix )
                painter.end()
                # Item
                qicon = QIcon( bg )
                item.setIcon( qicon )
                self.layout.page_list.addItem( item )

    #endregion
    #region Files

    def File_List( self ):
        if self.project_active == True:
            # Directory Images
            self.dir_image = QDir( self.project_images )
            self.dir_image.setSorting( QDir.LocaleAware )
            self.dir_image.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
            self.dir_image.setNameFilters( file_image )
            images = self.dir_image.entryInfoList()
            # Found Images
            self.found_images = []
            for i in range( 0, len( images ) ):
                image_i = images[i].filePath()
                if image_i.endswith( "-autosave.kra" ) == False: # Ignore autosaves
                    self.found_images.append( image_i )

            # Directory Texts
            self.dir_text = QDir( self.project_texts )
            self.dir_text.setSorting( QDir.LocaleAware )
            self.dir_text.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
            self.dir_text.setNameFilters( file_text )
            texts = self.dir_text.entryInfoList()
            # Found Texts
            self.found_texts = []
            for i in range( 0, len( texts ) ):
                text_i = texts[i].filePath()
                self.found_texts.append( text_i )

            # Directory Texts
            self.dir_trash = QDir( self.project_trash )
            self.dir_trash.setSorting( QDir.LocaleAware )
            self.dir_trash.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
            trash = self.dir_trash.entryInfoList()
            # Found Trash
            qfile = QFile()
            self.found_trash = []
            for i in range( 0, len( trash ) ):
                # Rename Trash ( avoid name conflicts )
                trash_i = trash[i].filePath()
                boolean = os.path.basename( trash_i ).startswith( "[ Trash_" )
                if boolean == False:
                    basename = str( os.path.basename( trash_i ) )
                    trash_tag = "[ Trash_{number} ] ".format( number=str( i ).zfill( 4 ) )
                    new_name = os.path.abspath( os.path.join( self.project_trash, trash_tag + basename ) )
                    qfile.rename( trash_i, new_name )
                else:
                    new_name = trash_i
                self.found_trash.append( str( new_name ) )

        if ( len( self.found_images ) == 0 and len( self.found_texts ) == 0 ):
            self.layout.text_note.clear()

        # Update
        self.Page_Thumbnail()
    def File_Conflict( self, path ):
        self.Message_Warnning( "ERROR", "Namespace conflict\nFolder with same name already exists" )
        self.File_Location( path, "SELECT" ) # Shows the File that is causing conflict
    def File_Location( self, project_directory, mode ):
        kernel = str( QSysInfo.kernelType() ) # WINDOWS=winnt & LINUX=linux
        if kernel == "winnt": # Windows
            if mode == "OPEN":
                operation = "/open,"
            if mode == "SELECT":
                operation = "/select,"
            FILEBROWSER_PATH = os.path.abspath( os.path.join( os.getenv( 'WINDIR' ), 'explorer.exe' ) )
            subprocess.run( [ FILEBROWSER_PATH, operation, project_directory ] )
        elif kernel == "linux": # Linux
            QDesktopServices.openUrl( QUrl.fromLocalFile( os.path.dirname( project_directory ) ) )
        elif kernel == "darwin": # MAC
            QDesktopServices.openUrl( QUrl.fromLocalFile( os.path.dirname( project_directory ) ) )
        else:
            QDesktopServices.openUrl( QUrl.fromLocalFile( os.path.dirname( project_directory ) ) )
    def File_Search( self, path, mode ):
        # Variables
        limit = 5

        # UI
        self.Message_Warnning( "SEARCH", "Start" )
        # Progress Bar
        self.layout.progress_bar.setMaximum( limit )
        self.layout.progress_bar.setValue( 0 )

        # Items
        item = []
        if mode == "PROJECT":
            files = QtCore.QDirIterator( path, ["*.project_pages.zip"], flags=QDirIterator.Subdirectories )
        elif mode == "PAGE":
            filter_images = file_image.copy()
            filter_images.remove( "*.zip" )
            files = QtCore.QDirIterator( path, file_image, flags=QDirIterator.Subdirectories )

        # Iterator
        index = 0
        while files.hasNext():
            # Progress Bar
            self.layout.progress_bar.setValue( index )
            QApplication.processEvents()
            # Search
            item = os.path.abspath( files.next() )
            if mode == "PROJECT":
                if item not in self.project_recent:
                    self.Project_Recent_Add( item )
            elif mode == "PAGE":
                if item not in self.found_images:
                    self.Page_Source( item )
            self.Message_Log( "IMPORT", f"file { item }" )
            # Cycle
            index = self.Limit_Loop( index + 1, limit )

        # Update
        if mode == "PROJECT":
            self.Project_Thumbnail( self.project_recent )
            Krita.instance().writeSetting( "Project Pages", "project_recent", str( self.project_recent ) )
        elif mode == "PAGE":
            self.Page_Update()
            self.Page_Thumbnail()
        self.Message_Warnning( "SEARCH", "Finish" )

        # Progress Bar
        self.layout.progress_bar.setMaximum( limit )
        self.layout.progress_bar.setValue( 0 )

   #endregion
    #region Information

    def Information_Block_Signals( self, boolean ):
        # Signals
        self.dialog.info_title.blockSignals( boolean )
        self.dialog.info_abstract.blockSignals( boolean )
        self.dialog.info_keyword.blockSignals( boolean )
        self.dialog.info_subject.blockSignals( boolean )
        self.dialog.info_license.blockSignals( boolean )
        self.dialog.info_language.blockSignals( boolean )
        self.dialog.info_description.blockSignals( boolean )

    def Information_Read( self ):
        # Block Signals
        self.Information_Block_Signals( True )

        # Variables
        file_name = ""
        file_version = ""
        self.info = {
            # Header
            'title': "",
            'abstract': "",
            'keyword': "",
            'subject': "",
            'license': "",
            'language': "",
            'description': "",
            # Time
            'date': "",
            'creation-date': "",
            'editing-cycles': "",
            'editing-time': "",
            # Author
            'initial-creator': "",
            'full-name': "",
            'creator-first-name': "",
            'creator-last-name': "",
            'initial': "",
            'author-title': "",
            'position': "",
            'company': "",
            }
        t_editing_cycles = ""
        t_editing_time = ""
        d_date = ""
        d_creation_date = ""
        delta_creation = ""
        creator_fl_name = ""
        self.contact = []


        # Active Document is Open
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # XML from active document
            try:
                # Active Document
                ki = Krita.instance()
                ad = ki.activeDocument()
                text = ad.documentInfo()

                # XML Data
                ET = xml.etree.ElementTree
                root = ET.fromstring( text )
                for r in root:
                    for i in r:
                        tag = i.tag.replace( "{http://www.calligra.org/DTD/document-info}", "" )
                        text = i.text
                        self.info[tag] = text
                        # Contacts
                        if tag == "contact":
                            self.contact.append( text )

                # Calculations
                path = ad.fileName()
                file_name = str( os.path.basename( path ) )
                d_date = self.display_date( self.info["date"] )
                d_creation_date = self.display_date( self.info["creation-date"] )
                t_editing_cycles = self.time_to_string( self.cycles_to_time( self.info["editing-cycles"] ) )
                t_editing_time = self.time_to_string( self.cycles_to_time( self.info["editing-time"] ) )
                if d_creation_date != "":
                    delta_creation = self.time_delta(
                        int( d_creation_date[0:4] ),
                        int( d_creation_date[5:7] ),
                        int( d_creation_date[8:10] ),
                        int( d_creation_date[11:13] ),
                        int( d_creation_date[14:16] ),
                        int( d_creation_date[17:19] ),
                        int( d_date[0:4] ),
                        int( d_date[5:7] ),
                        int( d_date[8:10] ),
                        int( d_date[11:13] ),
                        int( d_date[14:16] ),
                        int( d_date[17:19] ),
                        )
                creator_fl_name = self.info["creator-first-name"] + " " + self.info["creator-last-name"]
                self.Money_Cost( self.cycle_to_hour( self.info["editing-time"] ) ) # Edit time avoids idle inflation cost
            except:
                self.Money_Rate( 0 )

            # Krita Version from KRA file save
            try:
                target = "maindoc.xml"
                if zipfile.is_zipfile( path ):
                    archive = zipfile.ZipFile( path, "r" )
                    archive_open = archive.open( target )
                    ET = xml.etree.ElementTree
                    tree = ET.parse( archive_open )
                    root = tree.getroot()
                    attrib = root.attrib
                    file_version = attrib["kritaVersion"]
            except:
                file_version = "unknown"
        else:
            self.Money_Rate( 0 )

        # Document
        self.dialog.docname_string.setText( file_name )
        self.dialog.docversion_string.setText( file_version )
        # Header
        self.dialog.info_title.setText( self.info["title"] )
        self.dialog.info_abstract.setText( self.info["abstract"] ) # Description is Abstract inside Krita
        self.dialog.info_keyword.setText( self.info["keyword"] )
        self.dialog.info_subject.setText( self.info["subject"] )
        self.dialog.info_license.setText( self.info["license"] )
        self.dialog.info_language.setText( self.info["language"] )
        self.dialog.info_description.setText( self.info["description"] ) # Abstract is Description inside Krita
        # Time
        self.dialog.info_date.setText( d_date )
        self.dialog.info_creation.setText( d_creation_date + delta_creation )
        self.dialog.info_edit_cycles.setText( str( self.info["editing-cycles"] ) + str( t_editing_cycles ) )
        self.dialog.info_edit_time.setText( str( self.info["editing-time"] ) + str( t_editing_time ) )
        # Author
        self.dialog.info_creator.setText( self.info["initial-creator"] )
        self.dialog.info_nick_name.setText( self.info["full-name"] )
        self.dialog.info_full_name.setText( creator_fl_name )
        self.dialog.info_initials.setText( self.info["initial"] )
        self.dialog.info_author_title.setText( self.info["author-title"] )
        self.dialog.info_position.setText( self.info["position"] )
        self.dialog.info_company.setText( self.info["company"] )
        self.dialog.info_contact.clear()
        for i in range( 0, len( self.contact ) ):
            self.dialog.info_contact.addItem( str( self.contact[i] ) )

        # Block Signals
        self.Information_Block_Signals( False )
    def Information_Save( self ):
        # Active Document is Open
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            new_title = str( self.dialog.info_title.text() )
            new_abstract = str( self.dialog.info_abstract.toPlainText() ) # Abstract is Description inside Krita
            new_keyword = str( self.dialog.info_keyword.text() )
            new_subject = str( self.dialog.info_subject.text() )
            new_license = str( self.dialog.info_license.text() )
            new_language = str( self.dialog.info_language.text() )
            new_description = str( self.dialog.info_description.text() )  # Description is Abstract inside Krita

            contacts = ""
            for i in range( 0, len( self.contact ) ):
                contacts += f"<contact>{ self.contact[i] }</contact>\n"

            info_string = ( f"<?xml version='1.0' encoding='UTF-8'?>\n"
                f"<!DOCTYPE document-info PUBLIC '-//KDE//DTD document-info 1.1//EN' 'http://www.calligra.org/DTD/document-info-1.1.dtd'>\n"
                f"<document-info xmlns='http://www.calligra.org/DTD/document-info'>\n"
                f" <about>\n"
                f"  <title>{ new_title }</title>\n"
                f"  <description>{ new_description }</description>\n"
                f"  <subject>{ new_subject }</subject>\n"
                f"  <abstract><![CDATA[{ new_abstract }]]></abstract>\n"
                f"  <keyword>{ new_keyword }</keyword>\n"
                f"  <initial-creator>{ self.info['initial-creator'] }</initial-creator>\n"
                f"  <language>{ new_language }</language>\n"
                f"  <license>{ new_license }</license>\n"
                f" </about>\n"
                f" <author>\n"
                f"  <full-name>{ self.info['full-name'] }</full-name>\n"
                f"  <creator-first-name>{ self.info['creator-first-name'] }</creator-first-name>\n"
                f"  <creator-last-name>{ self.info['creator-last-name'] }</creator-last-name>\n"
                f"  <initial>{ self.info['initial'] } </initial>\n"
                f"  <author-title>{ self.info['author-title'] }</author-title>\n"
                f"  <position>{ self.info['position'] }</position>\n"
                f"  <company>{ self.info['company'] }</company>\n"
                f"  { contacts }\n"
                f" </author>\n"
                f"</document-info>" )
            text = Krita.instance().activeDocument().setDocumentInfo( info_string )

            # Reconstruct Items
            self.dialog.info_contact.clear()
            for i in range( 0, len( self.contact ) ):
                self.dialog.info_contact.addItem( str( self.contact[i] ) )
    def Information_Copy( self, item ):
        contact = item.text()
        if contact != "":
            QApplication.clipboard().setText( contact )

    def cycles_to_time( self, cycles ):
        # Variables
        year = 0
        month = 0
        day = 0
        hour = 0
        minute = 0
        second = 0
        # Checks
        if ( cycles != "" and cycles != 0 and cycles != None ):
            cycles = int( cycles )
            while cycles >= sec_ano:
                year += 1
                cycles -= sec_ano
            while cycles >= sec_mes:
                month += 1
                cycles -= sec_mes
            while cycles >= sec_dia:
                day += 1
                cycles -= sec_dia
            while cycles >= sec_hora:
                hour += 1
                cycles -= sec_hora
            while cycles >= sec_minuto:
                minute += 1
                cycles -= sec_minuto
            second = int( cycles )
        # Return
        time = [ year, month, day, hour, minute, second ]
        return time
    def time_to_string( self, time ):
        # Variables
        aa = time[0]
        mo = time[1]
        dd = time[2]
        hh = time[3]
        mi = time[4]
        ss = time[5]
        # string constants
        suffix = ""
        seconds = ""
        minutes = ""
        hours = ""
        days = ""
        months = ""
        years = ""
        # strings
        if ( aa>0 or mo>0 or dd>0 or hh>0 or mi>0 or ss>0 ):
            suffix = " >> "
        if aa > 0:
            years = str( aa ).zfill( 1 ) + "Y "
        if mo > 0:
            months = str( mo ).zfill( 2 ) + "M "
        if dd > 0:
            days = str( dd ).zfill( 2 ) + "D "
        if hh > 0:
            hours = str( hh ).zfill( 2 ) + "h "
        if mi > 0:
            minutes = str( mi ).zfill( 2 ) + "m "
        if ss > 0:
            seconds = str( ss ).zfill( 2 ) + "s"
        # string missing
        if ( mo==0 and aa>0 ):
            months = "00M "
        if ( dd==0 and ( aa>0 or mo>0 ) ):
            days = "00D "
        if ( hh==0 and ( aa>0 or mo>0 or dd>0 ) ):
            hours = "00h "
        if ( mi==0 and ( aa>0 or mo>0 or dd>0 or hh>0 ) ):
            minutes = "00m "
        if ( ss==0 and ( aa>0 or mo>0 or dd>0 or hh>0 or ss>0 ) ):
            seconds = "00s"
        # return
        string = suffix + years + months + days + hours + minutes + seconds
        return string
    def display_date( self, date ):
        if ( date != "" and date != None ):
            numbers = date.replace( "T", " " )
            string = numbers
        else:
            string = ""
        return string
    def time_delta( self, year1, month1, day1, hour1, minute1, second1, year2, month2, day2, hour2, minute2, second2 ):
        date_start = datetime.datetime( year1, month1, day1, hour1, minute1, second1 )
        date_now = datetime.datetime( year2, month2, day2, hour2, minute2, second2 )
        delta = ( date_now - date_start )
        string = self.time_to_string( self.cycles_to_time( ( delta.days * 86400 ) + delta.seconds ) )
        return string

    def cycle_to_hour( self, cycles ):
        # Variables
        hour = 0
        # Checks
        if ( cycles != "" and cycles != 0 and cycles != None ):
            cycles = int( cycles )
            while cycles >= sec_hora:
                hour += 1
                cycles -= sec_hora
            resto = cycles / sec_hora
            work_hours = hour + resto
        else:
            work_hours = 0
        return work_hours
    def Money_Cost( self, work_hours ):
        # Variables
        self.work_hours = work_hours
        rate = self.dialog.menu_money_rate.value()
        # Calculations
        total = rate * self.work_hours
        # Signals
        self.Money_Block_Signals( True )
        self.dialog.menu_money_total.setValue( total )
        self.Money_Block_Signals( False )
    def Money_Rate( self, rate ):
        total = rate * self.work_hours
        # Signals
        self.Money_Block_Signals( True )
        self.dialog.menu_money_total.setValue( total )
        self.Money_Block_Signals( False )
    def Money_Total( self, total ):
        if self.work_hours > 0:
            rate = total / self.work_hours
        else:
            rate = 0
        # Signals
        self.Money_Block_Signals( True )
        self.dialog.menu_money_rate.setValue( rate )
        self.Money_Block_Signals( False )
    def Money_Block_Signals( self, boolean ):
        self.dialog.menu_money_rate.blockSignals( boolean )
        self.dialog.menu_money_total.blockSignals( boolean )

    #endregion
    #region Layers

    def Layer_Space( self, boolean ):
        self.layer_space = boolean
    def Layer_Replace( self, boolean ):
        self.layer_replace = boolean
    def Layer_Prefix( self, boolean ):
        self.layer_prefix = boolean
    def Layer_Suffix( self, boolean ):
        self.layer_suffix = boolean

    def Rename_LOAD( self, dictionary ):
        # Widgets
        self.Rename_Block( True )

        self.dialog.replace_space.setText( dictionary["space"] )
        self.dialog.replace_old.setText( dictionary["replace_old"] )
        self.dialog.replace_new.setText( dictionary["replace_new"] )
        self.dialog.prefix_folder.setText( dictionary["prefix_folder"] )
        self.dialog.prefix_layer.setText( dictionary["prefix_layer"] )
        self.dialog.suffix_folder.setText( dictionary["suffix_folder"] )
        self.dialog.suffix_layer.setText( dictionary["suffix_layer"] )

        # Widgets
        self.Rename_Block( False )
    def Rename_Strings( self ):
        # Read
        space = self.dialog.replace_space.text()
        replace_old = self.dialog.replace_old.text()
        replace_new = self.dialog.replace_new.text()
        prefix_folder = self.dialog.prefix_folder.text()
        prefix_layer = self.dialog.prefix_layer.text()
        suffix_folder = self.dialog.suffix_folder.text()
        suffix_layer = self.dialog.suffix_layer.text()
        # Variable
        self.layer_string = {
            "space" : space,
            "replace_old" : replace_old,
            "replace_new" : replace_new,
            "prefix_folder" : prefix_folder,
            "prefix_layer" : prefix_layer,
            "suffix_folder" : suffix_folder,
            "suffix_layer" : suffix_layer,
            }
        # Save
        Krita.instance().writeSetting( "Project Pages", "layer_string", str( self.layer_string ) )

    def Layer_Select( self, index ):
        if ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
            item = self.dialog.rename_report.item( index.row() )
            node_name = item.text()
            if ( node_name != "" and node_name != "SUCCESS" ):
                ad = Krita.instance().activeDocument()
                node_i = ad.nodeByName( node_name )
                if node_i != None: # Avoids instant Krita Crash
                    ad.setActiveNode( node_i )
                else:
                    self.Message_Warnning( "LAYER", "Solved namespace conflict\n" )
                    self.Layer_Rename()
    def Layer_Rename( self ):
        self.dialog.rename_report.clear()
        if ( self.canvas() is not None ) and ( self.canvas().view() is not None ):

            node_list = self.Read_Nodes( Krita.instance().activeDocument() )
            node_repetition = self.Repeated_Names( node_list )

            if len( node_repetition ) == 0:
                self.String_Change( node_list, node_repetition )
                self.dialog.rename_report.addItem( "SUCCESS" )
        else:
            pass

    def Repeated_Names( self, node_list ):
        # Names of nodes
        names = []
        for i in range( 0, len( node_list ) ):
            names.append( node_list[i].name() )

        # Verify repetition
        repetition = []
        for i in range( 0, len( names ) ):
            name_i = names[i]
            number = names.count( name_i )
            if ( ( number > 1 ) and ( name_i not in repetition ) ):
                repetition.append( name_i )

        # Print Repeated
        if len( repetition ) > 0:
            for i in range( 0, len( repetition ) ):
                self.dialog.rename_report.addItem( str( repetition[i] ) )

        return repetition
    def String_Change( self, node_list, repetition ):
        for i in range( 0, len( node_list ) ):
            # Variables
            node_i = node_list[i]
            type_i = node_i.type()
            name_i = node_i.name()
            new_name = name_i
            # Modifications to String
            if name_i not in repetition:
                if self.layer_space == True:
                    new_name = new_name.replace( " ", self.layer_string["space"] )
                if self.layer_replace == True:
                    new_name = new_name.replace( self.layer_string["replace_old"], self.layer_string["replace_new"] )
                if self.layer_prefix == True:
                    if ( type_i == "grouplayer" and name_i.startswith( self.layer_string["prefix_folder"] ) == False ):
                        new_name = self.layer_string["prefix_folder"] + new_name
                    if ( type_i == "paintlayer" and name_i.startswith( self.layer_string["prefix_layer"] ) == False ):
                        new_name = self.layer_string["prefix_layer"] + new_name
                if self.layer_suffix == True:
                    if ( type_i == "grouplayer" and name_i.endswith( self.layer_string["suffix_folder"] ) == False ):
                        new_name = new_name + self.layer_string["suffix_folder"]
                    if ( type_i == "paintlayer" and name_i.endswith( self.layer_string["suffix_layer"] ) == False ):
                        new_name = new_name + self.layer_string["suffix_layer"]

                # Rename Node
                if name_i != new_name:
                    node_i.setName( new_name )
    def Rename_Block( self, boolean ):
        self.dialog.replace_space.blockSignals( boolean )
        self.dialog.replace_old.blockSignals( boolean )
        self.dialog.replace_new.blockSignals( boolean )
        self.dialog.prefix_folder.blockSignals( boolean )
        self.dialog.prefix_layer.blockSignals( boolean )
        self.dialog.suffix_folder.blockSignals( boolean )
        self.dialog.suffix_layer.blockSignals( boolean )

    #endregion
    #region Guides

    def Guide_Horizontal_Mirror( self, boolean ):
        self.guide_horizontal_mirror = boolean
        if ( boolean == True and ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # Widget
            self.dialog.guide_horizontal_mirror.setChecked( boolean )
            self.dialog.guide_horizontal_mirror.setText( "Horizontal : Mirror" )
            # document
            height = Krita.instance().activeDocument().height()
            h2 = height * 0.5
            guide_mirror = set()
            # Cycle
            for i in range( 0, len( self.guide_horizontal_list ) ):
                # Entry
                entry = self.guide_horizontal_list[i]
                guide_mirror.add( entry )
                # Reflect
                delta = abs( entry - h2 )
                if entry < h2:
                    reflect = h2 + delta
                    guide_mirror.add( reflect )
                elif entry > h2:
                    reflect = h2 - delta
                    guide_mirror.add( reflect )
                elif entry == h2:
                    pass
                # Set
            guide_mirror = sorted( list( guide_mirror ) )
            self.guide_horizontal_list = guide_mirror.copy()
        else:
            self.dialog.guide_horizontal_mirror.setChecked( False )
            self.dialog.guide_horizontal_mirror.setText( "Horizontal" )

        # Lists
        self.Guide_Horizontal_List( self.guide_horizontal_list )
    def Guide_Vertical_Mirror( self, boolean ):
        self.guide_vertical_mirror = boolean
        if ( boolean == True and ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # Widget
            self.dialog.guide_vertical_mirror.setChecked( boolean )
            self.dialog.guide_vertical_mirror.setText( "Vertical : Mirror" )
            # document
            width = Krita.instance().activeDocument().width()
            w2 = width * 0.5
            guide_mirror = set()
            # Cycle
            for i in range( 0, len( self.guide_vertical_list ) ):
                # Entry
                entry = self.guide_vertical_list[i]
                guide_mirror.add( entry )
                # Reflect
                delta = abs( entry - w2 )
                if entry < w2:
                    reflect = w2 + delta
                    guide_mirror.add( reflect )
                elif entry > w2:
                    reflect = w2 - delta
                    guide_mirror.add( reflect )
                elif entry == w2:
                    pass
                # Set
            guide_mirror = sorted( list( guide_mirror ) )
            self.guide_vertical_list = guide_mirror.copy()
        else:
            self.dialog.guide_vertical_mirror.setChecked( False )
            self.dialog.guide_vertical_mirror.setText( "Vertical" )

        # Lists
        self.Guide_Vertical_List( self.guide_vertical_list )

    def Guide_Horizontal_List( self, lista ):
        self.dialog.guide_horizontal_list.clear()
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # Variables
            len_guide = len( self.guide_horizontal_list )
            len_lista = len( lista )

            # Changed
            diff = None
            if len_guide <= len_lista:
                for i in range( 0, len_lista ):
                    if lista[i] not in self.guide_horizontal_list:
                        diff = i

            # Mirror
            if self.guide_horizontal_mirror == True:
                # Variables
                height = Krita.instance().activeDocument().height()
                h2 = height * 0.5
                meio = len( lista ) * 0.5

                # Cycle
                for i in range( 0, len_lista ):
                    if lista[i] != h2:
                        # Variables
                        index = len_lista - 1 - i
                        delta1 = lista[i] - h2
                        delta2 = lista[index] - h2
                        invert = h2 - delta1
                        # State
                        if len_guide == len_lista: # Equal
                            if delta1 != delta2:
                                if self.guide_horizontal_list[i] != lista[i]:
                                    lista[index] = self.Limit_Range( h2 - delta1, 0, height )
                        if len_guide < len_lista: # Add
                            if invert not in lista:
                                lista.append( invert )
                                break
                        if len_guide > len_lista: # Subtract
                            if invert not in lista:
                                lista.pop( i )
                                break
                lista.sort()

            # Prepare for next Cycle
            self.guide_horizontal_list = lista.copy()
            # Apply to Krita
            Krita.instance().activeDocument().setHorizontalGuides( self.guide_horizontal_list )

            # Widget List
            for i in range( 0, len_lista ):
                entry = lista[i]
                item = QListWidgetItem( str( entry ) )
                self.dialog.guide_horizontal_list.addItem( item )
            if diff != None:
                self.dialog.guide_horizontal_list.setCurrentRow( diff )
        else:
            self.guide_horizontal_list = []
    def Guide_Vertical_List( self, lista ):
        self.dialog.guide_vertical_list.clear()
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # Variables
            len_guide = len( self.guide_vertical_list )
            len_lista = len( lista )

            # Changed
            diff = None
            if len_guide <= len_lista:
                for i in range( 0, len_lista ):
                    if lista[i] not in self.guide_vertical_list:
                        diff = i

            # Mirror
            if self.guide_vertical_mirror == True:
                # Variables
                width = Krita.instance().activeDocument().width()
                w2 = width * 0.5
                meio = len( lista ) * 0.5

                # Cycle
                for i in range( 0, len_lista ):
                    if lista[i] != w2:
                        # Variables
                        index = len_lista - 1 - i
                        delta1 = lista[i] - w2
                        delta2 = lista[index] - w2
                        invert = w2 - delta1
                        # State
                        if len_guide == len_lista: # Equal
                            if delta1 != delta2:
                                if self.guide_vertical_list[i] != lista[i]:
                                    lista[index] = self.Limit_Range( w2 - delta1, 0, width )
                        if len_guide < len_lista: # Add
                            if invert not in lista:
                                lista.append( invert )
                                break
                        if len_guide > len_lista: # Subtract
                            if invert not in lista:
                                lista.pop( i )
                                break
                lista.sort()

            # Prepare for next Cycle
            self.guide_vertical_list = lista.copy()
            # Apply to Krita
            Krita.instance().activeDocument().setVerticalGuides( self.guide_vertical_list )

            # Widget List
            for i in range( 0, len_lista ):
                entry = lista[i]
                item = QListWidgetItem( str( entry ) )
                self.dialog.guide_vertical_list.addItem( item )
            if diff != None:
                self.dialog.guide_vertical_list.setCurrentRow( diff )
        else:
            self.guide_vertical_list = []

    def Guide_Set_Horizontal( self ):
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # Variables
            row = self.dialog.guide_horizontal_list.currentRow()
            item = self.dialog.guide_horizontal_list.item( row )
            height = Krita.instance().activeDocument().height()

            # Item
            if item is not None:
                # Inpute Request
                title = "Guide = {0}".format( item.text() )
                number, ok = QInputDialog.getDouble( self.dialog, "Input Guide Value", title, float( item.text() ) )
                number = self.Limit_Range( number, 0, height )
                if ok == True:
                    # Apply Item
                    item = self.dialog.guide_horizontal_list.item( row )
                    item.setText( str( number ) )
                    # Apply changed Guide to Krita
                    lista = self.guide_horizontal_list.copy()
                    lista[row] = number
                    Krita.instance().activeDocument().setHorizontalGuides( lista )
    def Guide_Set_Vertical( self ):
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # Variables
            row = self.dialog.guide_vertical_list.currentRow()
            item = self.dialog.guide_vertical_list.item( row )
            width = Krita.instance().activeDocument().width()

            # Item
            if item is not None:
                # Inpute Request
                title = "Guide = {0}".format( item.text() )
                number, ok = QInputDialog.getDouble( self.dialog, "Input Guide Value", title, float( item.text() ) )
                number = self.Limit_Range( number, 0, width )
                if ok == True:
                    # Apply Item
                    item = self.dialog.guide_vertical_list.item( row )
                    item.setText( str( number ) )
                    # Apply changed Guide to Krita
                    lista = self.guide_vertical_list.copy()
                    lista[row] = number
                    Krita.instance().activeDocument().setVerticalGuides( lista )

    def Guide_Ruler( self, boolean ):
        self.guide_ruler = boolean
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            state = Krita.instance().action( "view_ruler" ).isChecked()
            if boolean != state:
                Krita.instance().action( 'view_ruler' ).trigger()
            self.dialog.guide_ruler.setChecked( boolean )
        else:
            self.dialog.guide_ruler.setChecked( False )
    def Guide_Snap( self, boolean ):
        self.guide_snap = boolean
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            state = Krita.instance().action( "view_snap_to_guides" ).isChecked()
            if boolean != state:
                Krita.instance().action( 'view_snap_to_guides' ).trigger()
            self.dialog.guide_snap.setChecked( boolean )
        else:
            self.dialog.guide_snap.setChecked( False )
    def Guide_Visible( self, boolean ):
        self.guide_visible = boolean
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            Krita.instance().activeDocument().setGuidesVisible( boolean )
            self.dialog.guide_visible.setChecked( boolean )
        else:
            self.dialog.guide_visible.setChecked( False )
    def Guide_Lock( self, boolean ):
        self.guide_lock = boolean
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            Krita.instance().activeDocument().setGuidesLocked( boolean )
            self.dialog.guide_lock.setChecked( boolean )
        else:
            self.dialog.guide_lock.setChecked( False )

    #endregion
    #region Export Selection

    def Export_Load_Block( self, boolean ):
        self.dialog.export_width_state.blockSignals( boolean )
        self.dialog.export_height_state.blockSignals( boolean )
    def Export_Width_Block( self ):
        # Variables
        self.export_width_state = False
        self.export_height_state = False
        # User Insterface
        self.dialog.export_width_state.blockSignals( True )
        self.dialog.export_width_state.setChecked( False)
        self.dialog.export_width_state.blockSignals( False )
    def Export_Height_Block( self ):
        # Variables
        self.export_width_state = False
        self.export_height_state = False
        # User Interface
        self.dialog.export_height_state.blockSignals( True )
        self.dialog.export_height_state.setChecked( False)
        self.dialog.export_height_state.blockSignals( False )

    def Export_Width_State( self, state ):
        # Variables
        self.Export_Height_Block()
        self.export_width_state = state
        # Save
        Krita.instance().writeSetting( "Project Pages", "export_width_state", str( self.export_width_state ) )
        Krita.instance().writeSetting( "Project Pages", "export_height_state", str( self.export_height_state ) )
    def Export_Height_State( self, state ):
        # Variables
        self.Export_Width_Block()
        self.export_height_state = state
        # Save
        Krita.instance().writeSetting( "Project Pages", "export_width_state", str( self.export_width_state ) )
        Krita.instance().writeSetting( "Project Pages", "export_height_state", str( self.export_height_state ) )

    def Export_Width_Value( self, value ):
        # Variables
        self.export_width_value = value
        # Save
        Krita.instance().writeSetting( "Project Pages", "export_width_value", str( self.export_width_value ) )
    def Export_Height_Value( self, value ):
        # Variables
        self.export_height_value = value
        # Save
        Krita.instance().writeSetting( "Project Pages", "export_height_value", str( self.export_height_value ) )

    def Export_Selection( self ):
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # File
            file_dialog = QFileDialog( QWidget( self ) )
            file_dialog.setFileMode( QFileDialog.FileMode.AnyFile )
            save_path = file_dialog.getSaveFileName( self, "Export Location", "", "*.png" )[0]

            # Run the Export
            if save_path != None:
                self.Export_RUN( save_path )
    def Export_RUN( self, save_path ):
        # Read
        ki = Krita.instance()
        ad = ki.activeDocument()
        node = ad.activeNode()
        adw = ad.width()
        adh = ad.height()

        # Selection
        ss = ad.selection()
        if ss == None: # Create a selection
            px = 0
            py = 0
            pw = ad.width()
            ph = ad.height()
        else: # Custom
            px = ss.x()
            py = ss.y()
            pw = ss.width()
            ph = ss.height()

        # QImage
        qimage_thumbnail = ad.thumbnail( adw, adh )
        qimage_selection = qimage_thumbnail.copy( int( px ), int( py ), int( pw ), int( ph ) )
        mode = Qt.SmoothTransformation
        if ( self.export_width_state == True and self.export_height_state == False ):
            qimage_scale = qimage_selection.scaledToWidth( int( self.export_width_value ), mode )
        elif ( self.export_width_state == False and self.export_height_state == True ):
            qimage_scale = qimage_selection.scaledToHeight( int( self.export_height_value ), mode )
        else:
            qimage_scale = qimage_selection
        qimage_scale.save( save_path )

    #endregion
    #region Control

    def Control_Load( self ):
        if self.project_active == True:
            # Read File
            with open( self.project_control, "r" ) as control:
                data = control.readlines()

                # Parsing
                if data[0].startswith( "project_pages" ) == True:
                    # Widgets
                    self.Dialog_Block( True )

                    # Cycle
                    for i in range( 0, len( data ) ):
                        # Variables
                        line = data[i]
                        if line.endswith( "\n" ) == True:
                            line = line[:-1]
                        item = line.split( "=" )

                        # Document
                        if item[0] == "doc_basename":
                            try:
                                self.doc_basename = str( item[1] )
                                self.dialog.doc_basename.setText( self.doc_basename )
                            except:
                                self.dialog.doc_basename.setText( "page" )
                        if item[0] == "doc_width":
                            try:
                                self.doc_width = eval( item[1] )
                                self.dialog.doc_width.setValue( self.doc_width )
                            except:
                                self.dialog.doc_width.setValue( 2480 )
                        if item[0] == "doc_height":
                            try:
                                self.doc_height = eval( item[1] )
                                self.dialog.doc_height.setValue( self.doc_height )
                            except:
                                self.dialog.doc_height.setValue( 3508 )
                        if item[0] == "doc_swap":
                            try:
                                self.doc_swap = eval( item[1] )
                                self.dialog.doc_swap.setChecked( self.doc_swap )
                            except:
                                self.dialog.doc_swap.setChecked( False )
                        if item[0] == "doc_colorspace":
                            try:
                                self.doc_colorspace = str( item[1] )
                                self.dialog.doc_colorspace.setCurrentText( self.doc_colorspace )
                            except:
                                self.dialog.doc_colorspace.setCurrentText( "RGBA" )
                        if item[0] == "doc_bitdepth":
                            try:
                                self.doc_bitdepth = str( item[1] )
                                self.dialog.doc_bitdepth.setCurrentText( self.doc_bitdepth )
                            except:
                                self.dialog.doc_bitdepth.setCurrentText( "U8" )
                        if item[0] == "doc_dpi":
                            try:
                                self.doc_dpi = eval( item[1] )
                                self.dialog.doc_dpi.setValue( self.doc_dpi )
                            except:
                                self.dialog.doc_dpi.setValue( 300 )

                        # Guides
                        if item[0] == "doc_gh":
                            try:
                                self.doc_gh = eval( item[1] )
                                self.dialog.doc_gh.setText( str( self.doc_gh ).replace( "[", "" ).replace( "]", "" ) ) # Variable is list Text is not
                            except:
                                self.dialog.doc_gh.setText( "" )
                        if item[0] == "doc_gv":
                            try:
                                self.doc_gv = eval( item[1] )
                                self.dialog.doc_gv.setText( str( self.doc_gv ).replace( "[", "" ).replace( "]", "" ) ) # Variable is list Text is not
                            except:
                                self.dialog.doc_gv.setText( "" )

                    # Widgets
                    self.Doc_Custom_Check() # Updates Template Dropbox with W,H as input
                    self.Dialog_Block( False )
    def Control_Save( self ):
        if ( self.project_active == True and self.project_control != None ):
            # Data to be Saved
            data = (
                # Plugin
                "project_pages\n"+
                # Document Template
                f"doc_basename={ self.doc_basename }\n" +
                f"doc_width={ self.doc_width }\n" +
                f"doc_height={ self.doc_height }\n" +
                f"doc_swap={ self.doc_swap }\n" +
                f"doc_colorspace={ self.doc_colorspace }\n" +
                f"doc_bitdepth={ self.doc_bitdepth }\n" +
                f"doc_dpi={ self.doc_dpi }\n" +
                # Guides Template
                f"doc_gh={ self.doc_gh }\n" +
                f"doc_gv={ self.doc_gv }\n"
                )

            # Save to EO file
            with open( self.project_control, "w" ) as control:
                control.write( data )

    #endregion
    #region Notifier

    # Notifier
    def Application_Closing( self ):
        pass
    def Configuration_Changed( self ):
        pass
    def Image_Closed( self ):
        self.Page_Thumbnail()
    def Image_Created( self ):
        self.Page_Thumbnail()
    def Image_Saved( self ):
        # Zip File
        check = self.Check_Active()
        if check == True:
            self.Control_Save()
            self.ZIP_Save()
        # Display
        self.Page_Thumbnail()
    def View_Closed( self ):
        self.Page_Thumbnail()
    def View_Created( self ):
        self.Page_Thumbnail()
    def Window_Created( self ):
        # Module
        self.window = Krita.instance().activeWindow()
        # Signals
        self.window.activeViewChanged.connect( self.View_Changed )
        self.window.themeChanged.connect( self.Theme_Changed )
        self.window.windowClosed.connect( self.Window_Closed )
        # Start Position
        self.Theme_Changed()
    def Window_IsBeingCreated( self ):
        pass

    # Window
    def View_Changed( self ):
        pass
    def Theme_Changed( self ):
        theme = QApplication.palette().color( QPalette.Window ).value()
        if theme > 128:
            self.color1 = QColor( "#191919" )
            self.color2 = QColor( "#e5e5e5" )
        else:
            self.color1 = QColor( "#e5e5e5" )
            self.color2 = QColor( "#191919" )
    def Window_Closed( self ):
        self.ZIP_Exit( self.project_directory )

    #endregion
    #region Widget Events

    def showEvent( self, event ):
        # Dockers
        self.Welcome_Dockers()

        # QTimer
        if check_timer >= 30:
            self.timer_pulse.start( check_timer )

        # Splitter Geometry
        self.layout.splitter.moveSplitter( int( self.layout.main.width() * 0.5 ), 1 )
    def resizeEvent( self, event ):
        # self.Resize_Print( event )
        pass
    def enterEvent( self, event ):
        pass
    def leaveEvent( self, event ):
        pass
    def closeEvent( self, event ):
        self.ZIP_Exit( self.project_directory )

    def eventFilter( self, source, event ):
        # Project List
        if ( event.type() == QEvent.ContextMenu and source is self.layout.project_list ):
            self.Menu_ProjectContext( event )
            return True
        # Page List
        if ( event.type() == QEvent.ContextMenu and source is self.layout.page_list ):
            self.Menu_PageContext( event )
            return True

        # Mode
        if ( event.type() == QEvent.MouseButtonPress and source is self.layout.mode ):
            self.Menu_DirectoryContext( event )
            return True

        return super().eventFilter( source, event )

    def canvasChanged( self, canvas ):
        self.dialog.rename_report.clear()
        self.Krita_to_ProjectPages()
        self.Menu_Tabs()

    #endregion
    #region Notes

    """
    # Label Message
    self.layout.label.setText( "message" )

    # Pop Up Message
    QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( "message" ) )

    # Log Viewer Message
    QtCore.qDebug( f"value = { value }" )
    QtCore.qDebug( "message" )
    QtCore.qWarning( "message" )
    QtCore.qCritical( "message" )

    qmainwindow = Krita.instance().activeWindow().qwindow()
    if qmainwindow != None:
        stacked_widget = qmainwindow.centralWidget()
        count = stacked_widget.count()
        index = stacked_widget.currentIndex()
        var = index - 1
        if var <= 0 : var = 0
        if var >= count : var = count
        stacked_widget.setCurrentIndex( var )

    """
    #endregion

"""
New:
- Exporter Button on UI
- Exporter has width and height limit controls

Bug:
- When resizing the canvas the guides suffer a offset before the entire document is updated by Krita. ( Krita fixed it ? )

"""
