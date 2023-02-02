# Project Pages is a Krita plugin to Compile files into a single project file.
# Copyright (C) 2022  Ricardo Jeremias.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#region Imports ####################################################################
# Python Modules
import os
import shutil
import xml
import webbrowser
import zipfile
import winreg
import pathlib
import random
import subprocess
# Krita Module
from krita import *
# PyQt5 Modules
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Project KRA Modules

#endregion
#region Global Variables ###########################################################
DOCKER_NAME = "Project Pages"
project_pages_version = "2023_01_19"

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

#endregion


class ProjectPages_Docker(DockWidget):
    """
    Save multiple files into a single project file
    """

    #region Initialize #############################################################
    def __init__(self):
        super(ProjectPages_Docker, self).__init__()

        # Construct
        self.Variables()
        self.User_Interface()
        self.Connections()
        self.Modules()
        self.Style()
        self.Timer()
        self.Settings()

    def Variables(self):
        # Variables
        self.project_active = False
        self.widget_height = 25
        self.dirty = 5
        self.tn_size = 100

        # Color
        self.tn_color = QColor("#043764")

        # Widgets
        self.mode_index = 0

        # Paths
        self.directory_plugin = None # Plugin Location
        self.project_zip = None # Original ZIP file
        self.project_directory = None # Project UnZIPped directory
        self.project_control = None
        self.project_images = None
        self.project_texts = None
        self.project_trash = None
        self.recent_project = []

        # Index
        self.found_images = []
        self.found_texts = []
        self.index = {
            "image":0,
            "text":0,
            }

        # Document
        self.doc_basename = "page"
        self.doc_width = 2480
        self.doc_height = 3508
        self.doc_colorspace = "RGBA"
        self.doc_bitdepth = "U8"
        self.doc_dpi = 300

        # Guides
        self.guide_horizontal_mirror = False
        self.guide_vertical_mirror = False
        self.guide_horizontal_list = []
        self.guide_vertical_list = []
        self.guide_visible = False
        self.guide_lock = False

        # Templates
        self.doc_template = [
            # Texture
            {"index":"Texture 256", "width":256, "height":256 },
            {"index":"Texture 1024", "width":1024, "height":1024 },
            {"index":"Texture 2048", "width":2048, "height":2048 },
            {"index":"Texture 4096", "width":4096, "height":4096 },
            # Paper
            {"index":"Paper A3", "width":3508, "height":4960 },
            {"index":"Paper A4", "width":2480, "height":3508 },
            {"index":"Paper A5", "width":1754, "height":2480 },
            {"index":"Paper A6", "width":1240, "height":1754 },
            # Screen
            {"index":"Screen 480p SD", "width":640, "height":480 },
            {"index":"Screen 720p HD", "width":1280, "height":720 },
            {"index":"Screen 1080p FHD", "width":1920, "height":1080 },
            {"index":"Screen 1440p QHD", "width":2560, "height":1440 },
            {"index":"Screen 1080p 2k", "width":2048, "height":1080 },
            {"index":"Screen 2160p UHD 4k", "width":3840, "height":2160 },
            {"index":"Screen 4320p FUHD 8k", "width":7680, "height":4320 },
            # Custom (has to be last in the list always)
            {"index":"Custom", "width":None, "height":None },
            ]
    def User_Interface(self):
        # Window
        self.setWindowTitle(DOCKER_NAME)

        # Operating System
        self.OS = str(QSysInfo.kernelType()) # WINDOWS=winnt & LINUX=linux
        if self.OS == 'winnt': # Unlocks icons in Krita for Menu Mode
            QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)

        # Path Name
        self.directory_plugin = str(os.path.dirname(os.path.realpath(__file__)))

        # Widget Docker
        self.layout = uic.loadUi(os.path.normpath(self.directory_plugin + "/project_pages_docker.ui"), QWidget())
        self.setWidget(self.layout)


        # Settings
        self.dialog = uic.loadUi(os.path.normpath(self.directory_plugin + "/project_pages_settings.ui"), QDialog())
        self.dialog.setWindowTitle("Project Pages : Settings")
        self.dialog.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Populate Combobox
        for i in range(0, len( self.doc_template )):
            self.dialog.combo_box_template.addItem( self.doc_template[i]["index"] )
        self.dialog.combo_box_template.setCurrentText( "Paper A4" )
    def Connections(self):
        # Panels
        self.layout.image_list.clicked.connect(self.Text_Load)
        self.layout.image_list.doubleClicked.connect(self.Page_Open)
        self.layout.text_note.textChanged.connect(self.Text_Save)
        # UI
        self.layout.project.clicked.connect(self.Menu_Project)
        self.layout.page.clicked.connect(self.Menu_Page)
        self.layout.index_number.valueChanged.connect(self.Index_Number)
        self.layout.settings.clicked.connect(self.Menu_Settings)

        # Dialog Document
        self.dialog.lineedit_basename.textChanged.connect(self.Document_Basename)
        self.dialog.combo_box_template.currentTextChanged.connect(self.Document_Template)
        self.dialog.size_swap.toggled.connect(lambda: self.Document_Template( self.dialog.combo_box_template.currentText() ) )
        self.dialog.spinbox_width.valueChanged.connect(self.Document_Dim_Width)
        self.dialog.spinbox_height.valueChanged.connect(self.Document_Dim_Height)
        self.dialog.combobox_colorspace.currentTextChanged.connect(self.Document_Color_Space)
        self.dialog.combobox_bitdepth.currentTextChanged.connect(self.Document_Bit_Depth)
        self.dialog.spinbox_dpi.valueChanged.connect(self.Document_DPI)
        # Dialog Guides
        self.dialog.guide_horizontal_mirror.toggled.connect(self.Guide_Horizontal_Mirror)
        self.dialog.guide_vertical_mirror.toggled.connect(self.Guide_Vertical_Mirror)
        self.dialog.guide_horizontal_list.doubleClicked.connect(self.Guide_Set_Horizontal)
        self.dialog.guide_vertical_list.doubleClicked.connect(self.Guide_Set_Vertical)
        self.dialog.guide_visible.toggled.connect(self.Guide_Visible)
        self.dialog.guide_lock.toggled.connect(self.Guide_Lock)
        # Notices
        self.dialog.manual.clicked.connect(self.Menu_Manual)
        self.dialog.license.clicked.connect(self.Menu_License)

        # Event Filter
        self.layout.image_list.installEventFilter(self)
        # self.layout.mode.installEventFilter(self)
    def Modules(self):
        #region Notifier
        self.notifier = Krita.instance().notifier()
        self.notifier.applicationClosing.connect(self.Application_Closing)
        self.notifier.configurationChanged.connect(self.Configuration_Changed)
        self.notifier.imageClosed.connect(self.Image_Closed)
        self.notifier.imageCreated.connect(self.Image_Created)
        self.notifier.imageSaved.connect(self.Image_Saved)
        self.notifier.viewClosed.connect(self.View_Closed)
        self.notifier.viewCreated.connect(self.View_Created)
        self.notifier.windowCreated.connect(self.Window_Created)
        self.notifier.windowIsBeingCreated.connect(self.Window_IsBeingCreated)

        #endregion
    def Style(self):
        # Icons
        self.layout.project.setIcon(Krita.instance().icon('bundle_archive'))
        self.layout.page.setIcon(Krita.instance().icon('zoom-print'))
        self.layout.settings.setIcon(Krita.instance().icon('settings-button'))

        # ToolTips
        self.layout.mode.setToolTip("Mode")
        self.layout.project.setToolTip("Project")
        self.layout.page.setToolTip("Page")
        self.layout.settings.setToolTip("Settings")

        # StyleSheets
        self.layout.progress_bar.setStyleSheet("#progress_bar{background-color: rgba(0, 0, 0, 0);}")
        self.dialog.scrollarea_contents_pages.setStyleSheet("#scrollarea_contents_pages{background-color: rgba(0, 0, 0, 20);}")
        self.dialog.scrollarea_contents_guides.setStyleSheet("#scrollarea_contents_guides{background-color: rgba(0, 0, 0, 20);}")
    def Timer(self):
        if check_timer >= 30:
            self.timer_pulse = QtCore.QTimer(self)
            self.timer_pulse.timeout.connect(self.Krita_to_ProjectPages)
    def Settings(self):
        self.Mode_Index(self.mode_index)

        # Directory Path
        recent_project = str( Krita.instance().readSetting("Project Pages", "recent_project", "") )
        if recent_project == "":
            Krita.instance().writeSetting("Project Pages", "recent_project", "")
        else:
            self.recent_project = eval(recent_project)

    #endregion
    #region Menu ###################################################################
    def Mode_Index(self, index):
        # Variables
        a = 20
        # Pages
        if index == 0:
            # Icon
            # self.layout.mode.setIcon( Krita.instance().icon('all-layers') )
            # Module Containers
            self.layout.group_pages.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            # Height
            self.layout.group_pages.setMaximumHeight(qt_max)
            # Width
            self.layout.project.setMaximumWidth(a)
            self.layout.page.setMaximumWidth(a)

        # update cycle
        if self.mode_index != index: # After a search with null results or reference panel change, this ensure other modes update
            self.mode_index = index
        self.dirty = 5
        # Save
        Krita.instance().writeSetting("Project Pages", "mode_index", str( self.mode_index ))

    def Menu_ImageContext(self, event):
        if self.project_active == True:
            # Selected Items
            sel_items = self.layout.image_list.selectedItems()
            for i in range(0, len(sel_items)):
                sel_items[i] = sel_items[i].text()

            # Menu
            if len(sel_items) > 0:
                cmenu = QMenu(self)
                # Actions
                cmenu_header = cmenu.addSection("Item")
                cmenu_thumbnail = cmenu.addAction("Thumbnail")
                cmenu_delete = cmenu.addAction("Delete")
                # Execute
                position = event.globalPos()
                action = cmenu.exec_(position)
                # Triggers
                if action == cmenu_thumbnail:
                    self.Project_Thumbnail( sel_items[0] )
                elif action == cmenu_delete:
                    self.Page_Delete( sel_items )
    def Menu_Project(self, event):
        # Variables
        project_active = self.project_active
        len_recent = len( self.recent_project )

        # Menu
        cmenu = QMenu(self)
        # Actions
        cmenu_header = cmenu.addSection("Project")
        if project_active == False:
            cmenu_new = cmenu.addAction("New")
            cmenu_open = cmenu.addAction("Open")
            cmenu_recent = cmenu.addMenu("Recent")
            if len_recent >= 1:
                actions = {}
                for i in range(0, len(self.recent_project)):
                    recent = str( os.path.basename( self.recent_project[i] ) )
                    actions[i] = cmenu_recent.addAction( recent )
        if project_active == True:
            cmenu_location = cmenu.addAction("Location")
            cmenu_save = cmenu.addAction("Save")
            cmenu_close = cmenu.addAction("Close")

        # Execute
        geo = self.layout.project.geometry()
        qpoint = geo.bottomLeft()
        position = self.layout.project_buttons.mapToGlobal( qpoint )
        action = cmenu.exec_( position )
        # Triggers
        if project_active == False:
            if action == cmenu_new:
                self.Project_New()
            elif action == cmenu_open:
                self.Project_Open()
            elif len_recent >= 1:
                for i in range( 0, len( self.recent_project ) ):
                    try:
                        if action == actions[i]:
                            path = str( self.recent_project[i] )
                            self.ZIP_Open( path )
                            self.Control_Load()
                            break
                    except:
                        QMessageBox.information(QWidget(), i18n("Warnning"), i18n("message"))

        elif project_active == True:
            if action == cmenu_location:
                self.File_Location(self.project_control)
            elif action == cmenu_save:
                self.ZIP_Save()
            elif action == cmenu_close:
                self.ZIP_Close()
    def Menu_Page(self, event):
        # Variables
        project_active = self.project_active

        # Menu
        cmenu = QMenu(self)
        # Actions
        cmenu_header = cmenu.addSection("Page")
        if project_active == False:
            cmenu_notactive = cmenu.addAction(" ")
        if project_active == True:
            cmenu_new = cmenu.addAction("New")
            cmenu_add = cmenu.addAction("Add")
            cmenu_rename = cmenu.addAction("Rename")
            cmenu_export = cmenu.addAction("Export")

        # Execute
        geo = self.layout.page.geometry()
        qpoint = geo.bottomLeft()
        position = self.layout.project_buttons.mapToGlobal( qpoint )
        action = cmenu.exec_( position )
        # Triggers
        if project_active == False:
            if action == cmenu_notactive:
                pass
        if project_active == True:
            if action == cmenu_new:
                self.Page_New()
            elif action == cmenu_add:
                self.Page_Add()
            elif action == cmenu_rename:
                name, boolean = QtWidgets.QInputDialog.getText(self, 'Project Pages', 'Rename As')
                new_name = name.replace(" ", "_")
                if boolean == True:
                    self.Page_Rename( new_name )
            elif action == cmenu_export:
                file_dialog = QFileDialog(QWidget(self))
                file_dialog.setFileMode(QFileDialog.DirectoryOnly)
                path = file_dialog.getExistingDirectory(self, "Select Export Directory")
                path = os.path.normpath( path )
                if (path != "" and path != "."):
                    self.Page_Export(path)

    def Document_Basename(self, doc_basename):
        self.doc_basename = doc_basename
        Krita.instance().writeSetting("Project Pages", "doc_basename", str( self.doc_basename ))
        self.update()
    def Document_Template(self, current_text):
        swap = self.dialog.size_swap.isChecked()
        for i in range(0, len(self.doc_template)):
            index = self.doc_template[i]["index"]
            if current_text == index:
                # Read
                if swap == False:
                    width = self.doc_template[i]["width"]
                    height = self.doc_template[i]["height"]
                elif swap == True:
                    width = self.doc_template[i]["height"]
                    height = self.doc_template[i]["width"]
                # Widget
                if width != None:
                    self.dialog.spinbox_width.setValue( width )
                if height != None:
                    self.dialog.spinbox_height.setValue( height )
                break
    def Document_Dim_Width(self, doc_width):
        self.doc_width = doc_width
        self.Doc_Custom_Check()
        Krita.instance().writeSetting("Project Pages", "doc_width", str( self.doc_width ))
        self.update()
    def Document_Dim_Height(self, doc_height):
        self.doc_height = doc_height
        self.Doc_Custom_Check()
        Krita.instance().writeSetting("Project Pages", "doc_height", str( self.doc_height ))
        self.update()
    def Document_Color_Space(self, doc_colorspace):
        self.doc_colorspace = doc_colorspace
        Krita.instance().writeSetting("Project Pages", "doc_colorspace", str( self.doc_colorspace ))
        self.update()
    def Document_Bit_Depth(self, doc_bitdepth):
        self.doc_bitdepth = doc_bitdepth
        Krita.instance().writeSetting("Project Pages", "doc_bitdepth", str( self.doc_bitdepth ))
        self.update()
    def Document_DPI(self, doc_dpi):
        self.doc_dpi = doc_dpi
        Krita.instance().writeSetting("Project Pages", "doc_dpi", str( self.doc_dpi ))
        self.update()

    # Dialogs
    def Menu_Mode_Press(self, event):
        # Menu
        cmenu = QMenu(self)
        # Actions
        cmenu_pages = cmenu.addAction("Pages")
        cmenu_guides = cmenu.addAction("Guides")
        # Icons
        cmenu_pages.setIcon( Krita.instance().icon('all-layers') ) # all-layers current-layer duplicatelayer
        cmenu_guides.setIcon( Krita.instance().icon('palette-edit') ) #geometry palette-edit portrait select-all tool_rect_selection

        # Execute
        geo = self.layout.mode.geometry()
        qpoint = geo.bottomLeft()
        position = self.layout.horizontal_buttons.mapToGlobal( qpoint )
        action = cmenu.exec_( position )
        # Triggers
        if action == cmenu_pages:
            self.Mode_Index(0)
        elif action == cmenu_guides:
            self.Mode_Index(1)
    def Menu_Mode_Wheel(self, event):
        delta = event.angleDelta()
        if event.modifiers() == QtCore.Qt.NoModifier:
            delta_y = delta.y()
            value = 0
            if delta_y > 20:
                value = -1
            if delta_y < -20:
                value = 1
            if (value == -1 or value == 1):
                new_index = self.Limit_Range(self.mode_index + value, 0, 1)
                if self.mode_index != new_index:
                    self.Mode_Index( new_index )
    def Menu_Settings(self):
        # Display
        self.dialog.show()
        # Resize Geometry
        screen_zero = QtWidgets.QDesktopWidget().screenGeometry(0) # Size of monitor zero 0
        width = screen_zero.width()
        height = screen_zero.height()
        size = 500
        self.dialog.setGeometry( int(width*0.5-size*0.5), int(height*0.5-size*0.5), int(size), int(size) )
    def Menu_Manual(self):
        url = "https://github.com/EyeOdin/project_pages/wiki"
        webbrowser.open_new(url)
    def Menu_License(self):
        url = "https://github.com/EyeOdin/project_pages/blob/main/LICENSE"
        webbrowser.open_new(url)

    #endregion
    #region Management #############################################################
    def Path_Components(self, path):
        directory = os.path.dirname(path) # dir
        basename = os.path.basename(path) # name.ext
        extension = os.path.splitext(path)[1] # .ext
        n = basename.find(extension)
        name = basename[:n] # name
        return name

    def Check_Active(self):
        check = False
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            active = Krita.instance().activeDocument().fileName()
            for i in range(0, len(self.found_images)): # Project Pages Open
                page_i = self.found_images[i]
                if active == page_i:
                    check = True
        else:
            pass
        return check
    def Check_Documents(self):
        check = True
        documents = Krita.instance().documents()
        for d in range(0, len(documents)):
            doc_d = documents[d].fileName()
            for i in range(0, len(self.found_images)): # Project Pages Open
                page_i = self.found_images[i]
                if doc_d == page_i:
                    check = False
                    break
        return check

    def Items_All(self):
        count = self.layout.image_list.count()
        all_items = []
        for i in range(0, count):
            item = self.layout.image_list.item(i).text()
            all_items.append(item)
        return all_items

    def Pages_Block(self, boolean):
        self.layout.image_list.blockSignals(boolean)
        self.layout.text_note.blockSignals(boolean)
    def Dialog_Block(self, boolean):
        self.dialog.lineedit_basename.blockSignals(boolean)
        self.dialog.combo_box_template.blockSignals(boolean)
        self.dialog.spinbox_width.blockSignals(boolean)
        self.dialog.spinbox_height.blockSignals(boolean)
        self.dialog.combobox_colorspace.blockSignals(boolean)
        self.dialog.combobox_bitdepth.blockSignals(boolean)
        self.dialog.spinbox_dpi.blockSignals(boolean)

    def Limit_Range(self, value, minimum, maximum):
        if value <= minimum:
            value = minimum
        if value >= maximum:
            value = maximum
        return value

    def Animation_Document(self, document):
        animation = document.animationLength() # Problem all documents are created with 101 frames when created
        if animation == 1:
            boolean = False
        else:
            boolean = True
        clip_start = document.fullClipRangeStartTime()
        clip_end = document.fullClipRangeEndTime()
        frames = abs( clip_end - clip_start )
        return boolean, clip_start, clip_end, frames

    def Read_Nodes(self, document):
        # Document
        top_nodes = document.topLevelNodes()

        # Top level Nodes
        new_nodes = []
        for i in range(0, len(top_nodes)):
            new_nodes.append(top_nodes[i])

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
            for i in range(0, len(nodes)):
                try:
                    child_nodes = nodes[i].childNodes()
                    if len(child_nodes) > 0:
                        for cn in range(0, len(child_nodes)):
                            new_nodes.append(child_nodes[cn])
                except:
                    pass

            # cycle control
            if len(new_nodes) == 0:
                check_again = False
            else:
                counter += 1
                node_dic[counter] = new_nodes

        # Return List
        return_list = []
        for i in range(0, len(node_dic)):
            for j in range(0, len(node_dic[i])):
                node = node_dic[i][j]
                return_list.append(node)
        return return_list

    def Doc_Custom_Check(self):
        # Read
        width = self.dialog.spinbox_width.value()
        height = self.dialog.spinbox_height.value()
        # Write
        self.doc_width = width
        self.doc_height = height

        # Index Swap
        self.dialog.combo_box_template.blockSignals(True)
        index = None
        for i in range(0, len(self.doc_template)-1):
            entry = self.doc_template[i]
            if ((width == entry["width"] and height == entry["height"]) or (height == entry["width"] and width == entry["height"])):
                index = i
                break
        if index != None:
            self.dialog.combo_box_template.setCurrentIndex(index)
        else:
            self.dialog.combo_box_template.setCurrentIndex( len(self.doc_template)-1 )
        self.dialog.combo_box_template.blockSignals(False)

    #endregion
    #region Project Pages and Krita ################################################
    def Krita_to_ProjectPages(self):
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            try:
                # Read Document
                ad = Krita.instance().activeDocument()
                guide_visible = ad.guidesVisible()
                guide_lock = ad.guidesLocked()
                guide_horizontal_list = ad.horizontalGuides()
                guide_vertical_list = ad.verticalGuides()

                # Correct lists error range
                for i in range(0, len(guide_horizontal_list)):
                    guide_horizontal_list[i] = round( guide_horizontal_list[i], 2 )
                guide_horizontal_list = sorted(guide_horizontal_list)
                for i in range(0, len(guide_vertical_list)):
                    guide_vertical_list[i] = round( guide_vertical_list[i], 2 )
                guide_vertical_list = sorted(guide_vertical_list)

                # Update Document
                if self.guide_visible != guide_visible:
                    self.Guide_Visible(guide_visible)
                if self.guide_lock != guide_lock:
                    self.Guide_Lock(guide_lock)
                if self.guide_horizontal_list != guide_horizontal_list:
                    self.Guide_Horizontal_List(guide_horizontal_list)
                if self.guide_vertical_list != guide_vertical_list:
                    self.Guide_Vertical_List(guide_vertical_list)
            except:
                pass
        else:
            self.Default_State()
    def Default_State(self):
        if self.guide_visible != False:
            self.Guide_Visible( False )
        if self.guide_lock != False:
            self.Guide_Lock( False )
        if self.guide_horizontal_list != []:
            self.Guide_Horizontal_List( [] )
        if self.guide_vertical_list != []:
            self.Guide_Vertical_List( [] )

    #endregion
    #region Index ##################################################################
    def Index_Range(self, images, texts):
        # Variables
        self.index["image"] = 0
        self.index["text"] = 0

        # Block Signals
        self.layout.index_number.blockSignals(True)
        # Widget
        check = len(images) == len(texts) and len(images) > 0 and len(texts) > 0
        if check == True:
            num = 1
            total = len(images)
            self.layout.index_number.setMinimum( 1 )
            self.layout.index_number.setMaximum( total )
        else:
            num = 0
            total = 0
            self.layout.index_number.setMinimum( 0 )
            self.layout.index_number.setMaximum( 0 )
        self.layout.index_number.setValue( num )
        self.layout.index_number.setSuffix( ":" + str(total) )
        # Block Signals
        self.layout.index_number.blockSignals(False)
    def Index_Number(self, index):
        # Widgets
        self.layout.image_list.setCurrentRow( index - 1 )
        # Update Index
        self.Index_Set()
    def Index_Set(self):
        check_image = len( self.found_images )
        check_text = len( self.found_texts )
        if ( (check_text > 0) and (check_text == check_image) ):
            # Variables
            item = self.layout.image_list.currentItem()
            text = item.text()
            image_name = text.split(".")[0]

            # Search Matching Files
            for i in range(0, len(self.found_texts)):
                path = self.found_texts[i]
                name = self.Path_Components( self.found_texts[i] )
                if image_name == name:
                    # Index
                    self.index["image"] = self.layout.image_list.currentRow() # Widget index
                    self.index["text"] = i # file index
                    # Read Text
                    note = open(path, "r")
                    data = note.read()
                    note.close()
                    # Widget
                    self.layout.text_note.clear()
                    self.layout.text_note.setText( str(data) )
                    break

    #endregion
    #region Panels #################################################################
    def Text_Load(self):
        if self.project_active == True:
            # Update Index
            self.Index_Set()
            # Index
            index = int( self.index["image"] ) + 1
            total = ":" + str( len(self.found_images) )
            self.layout.index_number.blockSignals(True)
            self.layout.index_number.setValue( index )
            self.layout.index_number.setSuffix( total )
            self.layout.index_number.blockSignals(False)
    def Text_Save(self):
        if self.project_active == True:
            text_block = self.layout.text_note.toPlainText()
            file_txt = self.found_texts[ self.index["text"] ]
            note = open(file_txt, "w")
            note.write( text_block )
            note.close()

    #endregion
    #region Project ################################################################
    def Project_New(self):
        file_dialog = QFileDialog(QWidget(self))
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        path = file_dialog.getExistingDirectory(self, "Select Project Directory")
        path = os.path.normpath( path )
        if (path != "" and path != "."):
            name, boolean = QtWidgets.QInputDialog.getText(self, 'Project Pages', 'Select Project Name')
            if boolean == True:
                self.ZIP_New( path, name + ".project_pages" )
    def Project_Open(self):
        file_dialog = QFileDialog( QWidget(self) )
        file_dialog.setFileMode( QFileDialog.AnyFile )
        project_zip = file_dialog.getOpenFileName( self, "Select Project {} File".format(file_extension.upper()), "", str("*."+file_extension) )
        project_zip = os.path.normpath( project_zip[0] )
        if ( project_zip != "" and project_zip != "." and self.project_zip != project_zip ):
            self.ZIP_Open( project_zip )
    def Project_Recent_Add(self, path):
        if path not in self.recent_project:
            limit = 10
            length = len(self.recent_project)
            if length > limit:
                self.recent_project.pop(0)
                self.recent_project.append( path )
            else:
                self.recent_project.append( path )
            Krita.instance().writeSetting("Project Pages", "recent_project", str( self.recent_project ))
    def Project_Recent_Minus(self, path):
        if path in self.recent_project:
            index = self.recent_project.index(path)
            self.recent_project.pop(index)
            Krita.instance().writeSetting("Project Pages", "recent_project", str( self.recent_project ))
    def Project_Thumbnail(self, name):
        if self.project_active == True:
            image_path = os.path.normpath( self.project_directory + "\\IMAGES\\" + name )
            qimage = QPixmap(image_path)
            if qimage.isNull() == False:
                qimage = qimage.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                qimage.save(self.project_thumbnail)
                self.ZIP_Save()

    #endregion
    #region ZIP ####################################################################
    def ZIP_New(self, path, name):
        if self.project_active == False:
            # Paths
            project_directory = os.path.normpath( os.path.join(path , name) )
            project_zip = os.path.normpath( project_directory + "." + file_extension )

            exists = (os.path.exists(project_directory)) and (os.path.exists(project_zip))
            if exists == False:
                # Recent Projects
                self.Project_Recent_Add(project_zip)

                # Paths
                self.project_zip = project_zip
                self.project_directory = os.path.normpath( project_directory )
                self.project_control = os.path.normpath( os.path.join(project_directory, "control.eo") )
                self.project_thumbnail = os.path.normpath( os.path.join(project_directory, "thumbnail.png") )
                self.project_images = os.path.normpath( os.path.join(project_directory, "IMAGES") )
                self.project_texts = os.path.normpath( os.path.join(project_directory, "TEXTS") )
                self.project_trash = os.path.normpath( os.path.join(project_directory, "TRASH") )

                # Create Project Folders
                mode = 0o666
                os.mkdir( self.project_directory, mode )
                os.mkdir( self.project_images, mode )
                os.mkdir( self.project_texts, mode )
                os.mkdir( self.project_trash, mode )
                # Create Project TXT
                file = open( self.project_control, "w" )
                file.write( "project_pages" )
                # Create Thumbnail
                qimage = QImage(self.tn_size, self.tn_size, QImage.Format_RGBA8888)
                qimage.fill(self.tn_color)
                qimage.save(self.project_thumbnail)

                # Create File ZIP
                shutil.make_archive( self.project_directory, 'zip', self.project_directory ) # Creates the ZIP

                # Update
                self.layout.path_text.setText(os.path.basename(self.project_zip))
                self.project_active = True
                self.Files_List()

                # Control
                self.Control_Save()
            else:
                self.File_Conflict( project_directory )
        else:
            pass
    def ZIP_Open(self, project_zip):
        if self.project_active == False:
            # Close Previous Project
            self.ZIP_Close()

            # Variables
            basename = os.path.basename(project_zip)
            name = basename.split(".")[0] + "." + basename.split(".")[1]
            parent = os.path.dirname(project_zip)
            # Paths
            project_directory = os.path.normpath( os.path.join(parent, name) )
            project_zip = os.path.normpath( project_zip )

            # Filename is Open
            exists = os.path.exists(project_directory)
            if exists == False:
                # Check if it is a valid Project_Pages ZIP file
                valid = False
                if zipfile.is_zipfile(project_zip):
                    # Open Zip
                    archive = zipfile.ZipFile(project_zip, "r")
                    name_list = archive.namelist()

                    # Structure Verification
                    check_structure = False
                    item = 0
                    for i in range(0, len(structure)):
                        if structure[i] in name_list:
                            item += 1
                    check_structure = item == len(structure)
                    # Valid
                    if check_structure == True:
                        valid = True

                # Open the Valid ZIP file
                if valid == True:
                    # Recent Projects
                    self.Project_Recent_Add(project_zip)

                    # Variables
                    self.project_active = True
                    self.project_zip = project_zip
                    self.project_directory = project_directory
                    self.project_control = os.path.normpath( os.path.join(project_directory, "control.eo") )
                    self.project_thumbnail = os.path.normpath( os.path.join(project_directory, "thumbnail.png") )
                    self.project_images = os.path.normpath( os.path.join(project_directory, "IMAGES") )
                    self.project_texts = os.path.normpath( os.path.join(project_directory, "TEXTS") )
                    self.project_trash = os.path.normpath( os.path.join(project_directory, "TRASH") )

                    # Display
                    self.layout.path_text.setText(basename)

                    # Unzip Project
                    shutil.unpack_archive(self.project_zip, self.project_directory)

                    # Update
                    self.Files_List()
                    self.Index_Range(self.found_images, self.found_texts)

                    # Control
                    self.Control_Load()
                else:
                    self.Project_Recent_Minus(project_zip)
                    QMessageBox.information(QWidget(), i18n("Warnning"), i18n("Error : Invalid File"))
            else:
                self.File_Conflict( project_directory )
        else:
            pass
    def ZIP_Save(self):
        if self.project_active == True:
            shutil.make_archive(self.project_directory, 'zip', self.project_directory)
            self.Files_List()
        else:
            pass
    def ZIP_Close(self):
        if self.project_active == True:
            # Ask user if Project Folder should be deleted
            boolean = QMessageBox.question(self,"Project Pages", "Delete Project Folder?", QMessageBox.Yes,QMessageBox.No,)
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
            self.layout.image_list.clear()
            self.layout.text_note.clear()
            self.Index_Range(self.found_images, self.found_texts)
            self.layout.path_text.setText("")
        else:
            pass
    def ZIP_Exit(self, project_directory):
        if (self.project_active == True and os.path.isdir(project_directory) == True):
            try:
                shutil.rmtree(project_directory)
            except:
                pass
        else:
            pass

    #endregion
    #region Pages ##################################################################
    def Page_New(self):
        if self.project_active == True:
            # Taken Names
            taken_names = []
            count = self.layout.image_list.count()
            for i in range(0, count):
                text = self.layout.image_list.item(i).text()
                taken_names.append( text )

            # Check with Taken Names
            limit = len(self.found_images) + 10
            for i in range(1, limit):
                name = self.doc_basename + "_" + str(i).zfill(4)
                check_name = name + ".kra"
                if check_name not in taken_names:
                    # Paths
                    file_img = os.path.normpath( self.project_images + "\\" + name + ".kra" )
                    file_txt = os.path.normpath( self.project_texts + "\\" + name + ".eo" )

                    # Texts
                    note = open(file_txt, "w")
                    note.write("")
                    note.close()

                    # Image
                    new_document = Krita.instance().createDocument(
                        self.doc_width, self.doc_height,
                        self.doc_basename,
                        self.doc_colorspace, self.doc_bitdepth, "", self.doc_dpi
                        )
                    Krita.instance().activeWindow().addView( new_document ) # shows it in the application
                    new_document.setFullClipRangeStartTime(0)
                    new_document.setFullClipRangeEndTime(0) # Ensures Animation Length to reflect Animation size on start
                    Krita.instance().action('add_new_paint_layer').trigger() # create a layer to paint
                    Krita.instance().activeDocument().saveAs( file_img ) # save file to project folder

                    break

        # Update
        self.Page_Update()
    def Page_Add(self):
        if self.project_active == True:
            # Filter
            filter_images = "Images ( "
            count = len(file_image)
            for i in range(0, count):
                item = file_image[i]
                if item != "*.zip":
                    filter_images += str(file_image[i]) + " "
            filter_images += ")"

            # Open Files
            file_dialog = QFileDialog( QWidget(self) )
            file_dialog.setFileMode( QFileDialog.AnyFile )
            source = file_dialog.getOpenFileNames( self, "Select Files", "", filter_images )
            source = list( source[0] )
            for i in range(0, len(source)):
                source_i = source[i]
                if ( source_i != "" and source_i != "." and source_i not in self.found_images ):
                    # Variables
                    destination = self.project_images
                    # Copy Image
                    shutil.copy(source_i, destination)
                    # Create Text
                    name = self.Path_Components(source_i)
                    file_txt = os.path.normpath( self.project_texts + "\\" + name + ".eo" )
                    note = open(file_txt, "w")
                    note.write("")
                    note.close()
 
        # Update
        self.Page_Update()
    def Page_Open(self):
        if self.project_active == True:
            # Item
            basename = self.layout.image_list.currentItem().text()
            path = os.path.normpath( os.path.join(self.project_images, basename) )

            # Create Document
            document = Krita.instance().openDocument( path )
            Krita.instance().activeWindow().addView( document )


            # Animation Correction
            return_list = self.Read_Nodes( document )
            animation = False
            for i in range(0, len(return_list)):
                animation = return_list[i].animated()
                if animation == True:
                    break
            if animation == False:
                document.setFullClipRangeStartTime(0)
                document.setFullClipRangeEndTime(0)
    def Page_Rename(self, new_name):
        if self.project_active == True:
            # Check if documents are closed
            closed = self.Check_Documents()
            if closed == True:
                # All Items
                all_items = self.Items_All()

                # Compose Old Paths
                for i in range(0, len(all_items)):
                    # Parsing
                    item_i = all_items[i]
                    splited = item_i.split(".")
                    basename_i = splited[0]
                    image_ext = splited[1]
                    num = str(i+1).zfill(4)
                    # Path OLD
                    old_image  = os.path.normpath( self.project_images + "\\" + item_i )
                    old_backup = os.path.normpath( self.project_images + "\\" + item_i + "~" )
                    old_text   = os.path.normpath( self.project_texts  + "\\" + basename_i + ".eo" )
                    # Path NEW
                    new_image  = os.path.normpath( self.project_images + "\\" + new_name + "_" + num + "." + image_ext )
                    new_backup = os.path.normpath( self.project_images + "\\" + new_name + "_" + num + "." + image_ext + "~" )
                    new_text   = os.path.normpath( self.project_texts  + "\\" + new_name + "_" + num + ".eo" )

                    # Image File
                    try:
                        exists = os.path.exists( new_image )
                        if (old_image != new_image and exists == False):
                            os.rename( old_image, new_image )
                    except:
                        pass
                    # Backup File
                    try:
                        exists = os.path.exists( new_backup )
                        if (old_backup != new_backup and exists == False):
                            os.rename( old_backup, new_backup )
                    except:
                        pass
                    # Text File
                    try:
                        exists = os.path.exists( new_text )
                        if (old_text != new_text and exists == False):
                            os.rename( old_text, new_text )
                    except:
                        pass
            else:
                QMessageBox.information(QWidget(), i18n("Warnning"), i18n("Close all Project Pages from canvas to run"))

        # Update
        self.Page_Update()
    def Page_Export(self, export_path):
        if self.project_active == True:
            # Check if documents are closed
            closed = self.Check_Documents()
            if closed == True:
                # All Items
                all_items = self.Items_All()

                # Start
                row = self.layout.image_list.currentRow()
                self.Pages_Block(True)
                Krita.instance().setBatchmode(True)

                # Export Document
                for i in range(0, len(all_items)):
                    # Paths
                    name_i = all_items[i]
                    extension = name_i.split(".")[-1]
                    basename_i = name_i.replace( "." + extension, "" )

                    # Widget
                    self.layout.image_list.setCurrentRow( i )
                    self.layout.text_note.setText( "Exporting : " + str(name_i) )

                    # Path
                    image_path = os.path.normpath( os.path.join( self.project_images, name_i ) )
                    
                    # Document
                    document = Krita.instance().openDocument( image_path )
                    width = document.width()
                    height = document.height()
                    # Animation
                    if image_path.endswith(".kra") == True:
                        boolean, clip_start, clip_end, frames = self.Animation_Document(document)
                        for anim in range(clip_start, clip_end+1):
                            document.setCurrentTime( anim )
                            document.waitForDone()
                            if boolean == False:
                                save_path = os.path.normpath( export_path + "\\" + basename_i + ".png" )
                            else:
                                save_path = os.path.normpath( export_path + "\\" + basename_i + "_f" + str(anim).zfill(4) + ".png" )
                            qimage = document.thumbnail(width, height)
                            qimage.save( save_path )
                            document.waitForDone()
                    else:
                        save_path = os.path.normpath( export_path + "\\" + basename_i + ".png" )
                        qimage = document.thumbnail(width, height)
                        qimage.save( save_path )
                        document.waitForDone()
                    document.close()

                # End
                self.layout.text_note.clear()
                Krita.instance().setBatchmode(False)
                self.Pages_Block(False)
                self.layout.image_list.setCurrentRow( row )
            else:
                QMessageBox.information(QWidget(), i18n("Warnning"), i18n("Close all Project Pages from canvas to run"))

        # Update
        self.Page_Update()
    def Page_Delete(self, lista):
        if self.project_active == True:
            # Delete
            for i in range(0, len(lista)):
                # Parsing
                item_i = lista[i]
                basename_i = (item_i.split("."))[0]
                # Variables
                path_image  = os.path.normpath( self.project_images + "\\" + item_i )
                path_backup = os.path.normpath( self.project_images + "\\" + item_i + "~" )
                path_text   = os.path.normpath( self.project_texts  + "\\" + basename_i + ".eo" )

                # Image File
                try:
                    shutil.move( path_image, self.project_trash, copy_function = shutil.copytree )
                except:
                    pass
                # Backup File
                try:
                    shutil.move( path_backup, self.project_trash, copy_function = shutil.copytree )
                except:
                    pass
                # Text File
                try:
                    shutil.move( path_text, self.project_trash, copy_function = shutil.copytree )
                except:
                    pass

        # Update
        self.Files_List()
        self.Index_Range(self.found_images, self.found_texts)
    def Page_Update(self):
        self.Files_List()
        self.Index_Range(self.found_images, self.found_texts)

    #endregion
    #region Files ##################################################################
    def Files_List(self):
        if self.project_active == True:
            # Directory Images
            self.dir_image = QDir( self.project_images )
            self.dir_image.setSorting(QDir.LocaleAware)
            self.dir_image.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
            self.dir_image.setNameFilters(file_image)
            images = self.dir_image.entryInfoList()
            # Found Images
            self.found_images = []
            for i in range(0, len(images)):
                image_i = os.path.normpath( images[i].filePath() )
                self.found_images.append( image_i )

            # Directory Texts
            self.dir_text = QDir( self.project_texts )
            self.dir_text.setSorting(QDir.LocaleAware)
            self.dir_text.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
            self.dir_text.setNameFilters(file_text)
            texts = self.dir_text.entryInfoList()
            # Found Texts
            self.found_texts = []
            for i in range(0, len(texts)):
                text_i = os.path.normpath( texts[i].filePath() )
                self.found_texts.append( text_i )

            # Directory Texts
            self.dir_trash = QDir( self.project_trash )
            self.dir_trash.setSorting(QDir.LocaleAware)
            self.dir_trash.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
            trash = self.dir_trash.entryInfoList()
            # Found Trash
            qfile = QFile()
            self.found_trash = []
            for i in range(0, len(trash)):
                # Rename Trash ( avoid name conflicts )
                trash_i = os.path.normpath( trash[i].filePath() )
                boolean = os.path.basename( trash_i ).startswith( "[ Trash_" )
                if boolean == False:
                    basename = str( os.path.basename( trash_i ) )
                    trash_tag = "[ Trash_{number} ] ".format( number=str(i).zfill(4) )
                    new_name = os.path.normpath( self.project_trash + "\\" + trash_tag + basename )
                    qfile.rename(trash_i, new_name)
                else:
                    new_name = trash_i
                self.found_trash.append( str(new_name) )

        # Update
        self.Thumbnail_Redraw()
    def Thumbnail_Redraw(self):
        # Starting Empty
        self.layout.image_list.clear()

        # Images List Draw
        if (self.project_active == True and len(self.found_images) > 0):
            for i in range(0, len(self.found_images)):
                # Variables
                path = self.found_images[i]
                basename = os.path.basename( path )

                # Create Items
                item = QListWidgetItem( basename )
                size = 100
                # Thumbnail
                bg = QPixmap( size, size )
                bg.fill( self.color_alpha )
                pix = QPixmap(path).scaled( size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation )
                # Variables
                w = pix.width()
                h = pix.height()
                px = (size*0.5) - (w*0.5)
                py = (size*0.5) - (h*0.5)
                # Composed Image
                painter = QPainter( bg )
                painter.drawPixmap( px, py, pix )
                painter.end()
                # Item
                qicon = QIcon( bg )
                item.setIcon( qicon )
                self.layout.image_list.addItem( item )

    def File_Conflict(self, path):
        QMessageBox.information(QWidget(), i18n("Warnning"), i18n("Error : Name Conflict"))
        self.File_Location(path) # Shows the File that is causing conflict
    def File_Location(self, project_directory):
        kernel = str(QSysInfo.kernelType()) # WINDOWS=winnt & LINUX=linux
        if kernel == "winnt": # Windows
            FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
            subprocess.run([FILEBROWSER_PATH, '/select,', os.path.normpath(project_directory)])
        elif kernel == "linux": # Linux
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(project_directory)))
        elif okernels == "darwin": # MAC
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(project_directory)))
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(project_directory)))

    #endregion
    #region Guides #################################################################
    def Guide_Horizontal_Mirror(self, boolean):
        self.guide_horizontal_mirror = boolean
        if boolean == True:
            # String
            self.dialog.guide_horizontal_mirror.setText("Horizontal : Mirror")
            # document
            height = Krita.instance().activeDocument().height()
            h2 = height * 0.5
            mirror = set()
            # Cycle
            for i in range(0, len(self.guide_horizontal_list)):
                # Entry
                entry = self.guide_horizontal_list[i]
                mirror.add( entry )
                # Reflect
                delta = abs(entry - h2)
                if entry < h2:
                    reflect = h2 + delta
                    mirror.add( reflect )
                elif entry > h2:
                    reflect = h2 - delta
                    mirror.add( reflect )
                elif entry == h2:
                    pass
                # Set
            mirror = sorted( list( mirror ) )
            self.guide_horizontal_list = mirror.copy()
        else:
            self.dialog.guide_horizontal_mirror.setText("Horizontal")

        # Lists
        self.Guide_Horizontal_List(self.guide_horizontal_list)
    def Guide_Vertical_Mirror(self, boolean):
        self.guide_vertical_mirror = boolean
        if boolean == True:
            # String
            self.dialog.guide_vertical_mirror.setText("Vertical : Mirror")
            # document
            width = Krita.instance().activeDocument().width()
            w2 = width * 0.5
            mirror = set()
            # Cycle
            for i in range(0, len(self.guide_vertical_list)):
                # Entry
                entry = self.guide_vertical_list[i]
                mirror.add( entry )
                # Reflect
                delta = abs(entry - w2)
                if entry < w2:
                    reflect = w2 + delta
                    mirror.add( reflect )
                elif entry > w2:
                    reflect = w2 - delta
                    mirror.add( reflect )
                elif entry == w2:
                    pass
                # Set
            mirror = sorted( list( mirror ) )
            self.guide_vertical_list = mirror.copy()
        else:
            self.dialog.guide_vertical_mirror.setText("Vertical")

        # Lists
        self.Guide_Vertical_List(self.guide_vertical_list)

    def Guide_Horizontal_List(self, lista):
        self.dialog.guide_horizontal_list.clear()
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            # Variables
            len_guide = len(self.guide_horizontal_list)
            len_lista = len(lista)

            # Changed
            diff = None
            if len_guide <= len_lista:
                for i in range(0, len_lista):
                    if lista[i] not in self.guide_horizontal_list:
                        diff = i

            # Mirror
            if self.guide_horizontal_mirror == True:
                # Variables
                height = Krita.instance().activeDocument().height()
                h2 = height * 0.5
                meio = len(lista) * 0.5

                # Cycle
                for i in range(0, len_lista):
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
                                lista.append(invert)
                                break
                        if len_guide > len_lista: # Subtract
                            if invert not in lista:
                                lista.pop(i)
                                break
                lista.sort()

            # Prepare for next Cycle
            self.guide_horizontal_list = lista.copy()
            # Apply to Krita
            Krita.instance().activeDocument().setHorizontalGuides( self.guide_horizontal_list )

            # Widget List
            for i in range(0, len_lista):
                entry = lista[i]
                item = QListWidgetItem( str(entry) )
                self.dialog.guide_horizontal_list.addItem( item )
            if diff != None:
                self.dialog.guide_horizontal_list.setCurrentRow( diff )
        else:
            self.guide_horizontal_list = []
    def Guide_Vertical_List(self, lista):
        self.dialog.guide_vertical_list.clear()
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            # Variables
            len_guide = len(self.guide_vertical_list)
            len_lista = len(lista)

            # Changed
            diff = None
            if len_guide <= len_lista:
                for i in range(0, len_lista):
                    if lista[i] not in self.guide_vertical_list:
                        diff = i

            # Mirror
            if self.guide_vertical_mirror == True:
                # Variables
                width = Krita.instance().activeDocument().width()
                w2 = width * 0.5
                meio = len(lista) * 0.5

                # Cycle
                for i in range(0, len_lista):
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
                                lista.append(invert)
                                break
                        if len_guide > len_lista: # Subtract
                            if invert not in lista:
                                lista.pop(i)
                                break
                lista.sort()

            # Prepare for next Cycle
            self.guide_vertical_list = lista.copy()
            # Apply to Krita
            Krita.instance().activeDocument().setVerticalGuides( self.guide_vertical_list )

            # Widget List
            for i in range(0, len_lista):
                entry = lista[i]
                item = QListWidgetItem( str(entry) )
                self.dialog.guide_vertical_list.addItem( item )
            if diff != None:
                self.dialog.guide_vertical_list.setCurrentRow( diff )
        else:
            self.guide_vertical_list = []

    def Guide_Set_Horizontal(self):
        # Variables
        row = self.dialog.guide_horizontal_list.currentRow()
        item = self.dialog.guide_horizontal_list.item( row )
        height = Krita.instance().activeDocument().height()

        # Item
        if item is not None:
            # Inpute Request
            title = "Guide = {0}".format( item.text() )
            number, ok = QInputDialog.getDouble( self.dialog, "Input Guide Value", title, float(item.text()) )
            number = self.Limit_Range( number, 0, height )
            if ok == True:
                # Apply Item
                item = self.dialog.guide_horizontal_list.item( row )
                item.setText( str(number) )
                # Apply changed Guide to Krita
                lista = self.guide_horizontal_list.copy()
                lista[row] = number
                Krita.instance().activeDocument().setHorizontalGuides(lista)
    def Guide_Set_Vertical(self):
        # Variables
        row = self.dialog.guide_vertical_list.currentRow()
        item = self.dialog.guide_vertical_list.item( row )
        width = Krita.instance().activeDocument().width()

        # Item
        if item is not None:
            # Inpute Request
            title = "Guide = {0}".format( item.text() )
            number, ok = QInputDialog.getDouble( self.dialog, "Input Guide Value", title, float(item.text()) )
            number = self.Limit_Range( number, 0, width )
            if ok == True:
                # Apply Item
                item = self.dialog.guide_vertical_list.item( row )
                item.setText( str(number) )
                # Apply changed Guide to Krita
                lista = self.guide_vertical_list.copy()
                lista[row] = number
                Krita.instance().activeDocument().setVerticalGuides(lista)

    def Guide_Visible(self, boolean):
        self.guide_visible = boolean
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            Krita.instance().activeDocument().setGuidesVisible(boolean)
            self.dialog.guide_visible.setChecked(boolean)
        else:
            self.dialog.guide_visible.setChecked(False)
    def Guide_Lock(self, boolean):
        self.guide_lock = boolean
        if ((self.canvas() is not None) and (self.canvas().view() is not None)):
            Krita.instance().activeDocument().setGuidesLocked(boolean)
            self.dialog.guide_lock.setChecked(boolean)
        else:
            self.dialog.guide_lock.setChecked(False)

    #endregion
    #region Control ################################################################
    def Control_Load(self):
        if self.project_active == True:
            try:
                # Read File
                file = open(self.project_control, "r")
                data = file.readlines()

                # Parsing
                plugin = str(data[0]).replace("\n", "", 1)
                if plugin  == "project_pages":
                    # Widgets
                    self.Dialog_Block(True)

                    # Cycle
                    for i in range(0, len(data)):
                        data_i = data[i]
                        # Document
                        if data_i.startswith("doc_basename=") == True:
                            self.doc_basename   = str(data_i).replace("doc_basename=", "", 1).replace("\n", "", 1)
                            self.dialog.lineedit_basename.setText( self.doc_basename )

                        if data_i.startswith("doc_template=") == True:
                            self.doc_template   = eval( str(data_i).replace("doc_template=", "", 1).replace("\n", "", 1) )
                            self.dialog.combo_box_template.setCurrentText( self.doc_template["index"] )

                        if data_i.startswith("doc_width=") == True:
                            self.doc_width      = eval( str(data_i).replace("doc_width=", "", 1).replace("\n", "", 1) )
                            self.dialog.spinbox_width.setValue( self.doc_width )

                        if data_i.startswith("doc_height=") == True:
                            self.doc_height     = eval( str(data_i).replace("doc_height=", "", 1).replace("\n", "", 1) )
                            self.dialog.spinbox_height.setValue( self.doc_height )

                        if data_i.startswith("doc_colorspace=") == True:
                            self.doc_colorspace = str(data_i).replace("doc_colorspace=", "", 1).replace("\n", "", 1)
                            self.dialog.combobox_colorspace.setCurrentText( self.doc_colorspace )

                        if data_i.startswith("doc_bitdepth=") == True:
                            self.doc_bitdepth   = str(data_i).replace("doc_bitdepth=", "", 1).replace("\n", "", 1)
                            self.dialog.combobox_bitdepth.setCurrentText( self.doc_bitdepth )

                        if data_i.startswith("doc_dpi=") == True:
                            self.doc_dpi        = eval( str(data_i).replace("doc_dpi=", "", 1).replace("\n", "", 1) )
                            self.dialog.spinbox_dpi.setValue( self.doc_dpi )

                        # Guides
                        if data_i.startswith("guide_horizontal_list=") == True:
                            self.guide_horizontal_list = eval(data_i).replace("guide_horizontal_list=", "", 1).replace("\n", "", 1)
                            Krita.instance().activeDocument().setHorizontalGuides( self.guide_horizontal_list )

                        if data_i.startswith("guide_vertical_list=") == True:
                            self.guide_vertical_list = eval( str(data_i).replace("guide_vertical_list=", "", 1).replace("\n", "", 1) )
                            Krita.instance().activeDocument().setVerticalGuides( self.guide_vertical_list )

                    # Widgets
                    self.Dialog_Block(False)
            except:
                pass
    def Control_Save(self):
        if self.project_active == True:
            try:
                # Widget
                temp_index = self.dialog.combo_box_template.currentIndex()

                # Data to be Saved
                data = (
                    # Plugin
                    "project_pages\n"+
                    # Document
                    "doc_basename="+str( self.doc_basename )+"\n"+
                    "doc_template="+str( self.doc_template[temp_index] )+"\n"+
                    "doc_width="+str( self.doc_width )+"\n"+
                    "doc_height="+str( self.doc_height )+"\n"+
                    "doc_colorspace="+str( self.doc_colorspace )+"\n"+
                    "doc_bitdepth="+str( self.doc_bitdepth )+"\n"+
                    "doc_dpi="+str( self.doc_dpi )+"\n"+
                    # Guides
                    "guide_horizontal_list="+str( self.guide_horizontal_list )+"\n"+
                    "guide_vertical_list="+str( self.guide_vertical_list )+"\n"+
                    ""
                    )

                # Save to TXT file
                file = open(self.project_control, "w")
                file.write(data)
            except:
                pass

    #endregion
    #region Notifier ###############################################################
    def Application_Closing(self):
        pass
    def Configuration_Changed(self):
        pass
    def Image_Closed(self):
        self.Thumbnail_Redraw()
    def Image_Created(self):
        self.Thumbnail_Redraw()
    def Image_Saved(self):
        # Zip File
        check = self.Check_Active()
        if check == True:
            self.Control_Save()
            self.ZIP_Save()
        # Display
        self.Thumbnail_Redraw()
    def View_Closed(self):
        self.Thumbnail_Redraw()
    def View_Created(self):
        self.Thumbnail_Redraw()
    def Window_Created(self):
        pass
    def Window_IsBeingCreated(self):
        pass

    #endregion
    #region Window #################################################################
    def Window_Connect(self):
        # Window
        self.window = Krita.instance().activeWindow()
        if self.window != None:
            self.window.activeViewChanged.connect(self.View_Changed)
            self.window.themeChanged.connect(self.Theme_Changed)
            self.window.windowClosed.connect(self.Window_Closed)

    def View_Changed(self):
        pass
    def Theme_Changed(self):
        theme = QApplication.palette().color(QPalette.Window).value()
        if theme > 128:
            self.color1 = QColor("#191919")
            self.color2 = QColor("#e5e5e5")
        else:
            self.color1 = QColor("#e5e5e5")
            self.color2 = QColor("#191919")
        self.color_alpha = QColor(0, 0, 0, 0)
    def Window_Closed(self):
        self.ZIP_Exit( self.project_directory )

    #endregion
    #region Widget Events ##########################################################
    def showEvent(self, event):
        # Window
        self.Window_Connect()
        self.Theme_Changed()
        # QTimer
        if check_timer >= 30:
            self.timer_pulse.start(check_timer)
    def resizeEvent(self, event):
        pass
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        pass
    def closeEvent(self, event):
        self.ZIP_Exit( self.project_directory )

    def eventFilter(self, source, event):
        # Image List
        if (event.type() == QEvent.ContextMenu and source is self.layout.image_list):
            self.Menu_ImageContext(event)
            return True

        # Mode
        if (event.type() == QEvent.MouseButtonPress and source is self.layout.mode):
            self.Menu_Mode_Press(event)
            return True
        if (event.type() == QEvent.Wheel and source is self.layout.mode):
            self.Menu_Mode_Wheel(event)
            return True

        return super().eventFilter(source, event)

    #endregion
    #region Change Canvas ##########################################################
    def canvasChanged(self, canvas):
        pass

    #endregion
    #region Notes ##################################################################
    """
    # Label Message
    self.layout.label.setText("message")

    # Pop Up Message
    QMessageBox.information(QWidget(), i18n("Warnning"), i18n("message"))

    # Log Viewer Message
    QtCore.qDebug("value = " + str(value))
    QtCore.qDebug("message")
    QtCore.qWarning("message")
    QtCore.qCritical("message")
    """

    #endregion
