# Project Pages is a Krita plugin to Compile KRA files into a single project file.
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
# Krita Module
from krita import *
# PyQt5 Modules
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Project KRA Modules

#endregion
#region Global Variables ###########################################################
DOCKER_NAME = "Project Pages"
project_pages_version = "2023_01_19"

file_extension = "zip"
structure = ["control.eo", "IMAGES/", "TEXTS/", "TRASH/"]

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

#endregion


class ProjectPages_Docker(DockWidget):
    """
    Save multiple images into a single project file
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
        self.Settings()

    def Variables(self):
        # Variables
        self.project_active = False

        # Paths
        self.directory_plugin = None # Plugin Location
        self.project_zip = None # Original ZIP file
        self.project_directory = None # Project UnZIPped directory
        self.project_images = None
        self.project_texts = None
        self.project_trash = None

        # Index
        self.found_images = []
        self.found_texts = []
        self.index = {
            "image":0,
            "text":0,
            }

        # Document
        self.doc_basename = "page"
        self.doc_width = 1920
        self.doc_height = 1080
        self.doc_colorspace = "RGBA"
        self.doc_bitdepth = "U8"
        self.doc_dpi = 300
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
    def Connections(self):
        # Panels
        self.layout.image_list.clicked.connect(self.Text_Load)
        self.layout.image_list.doubleClicked.connect(self.Insert_Document)
        self.layout.text_note.textChanged.connect(self.Text_Save)
        # UI
        self.layout.project.clicked.connect(self.Menu_Project)
        self.layout.page.clicked.connect(self.Menu_Page)
        self.layout.index_number.valueChanged.connect(self.Index_Number)
        self.layout.settings.clicked.connect(self.Menu_Settings)

        # Dialog
        self.dialog.lineedit_basename.textChanged.connect(self.Document_Basename)
        self.dialog.spinbox_width.valueChanged.connect(self.Document_Dim_Width)
        self.dialog.spinbox_height.valueChanged.connect(self.Document_Dim_Height)
        self.dialog.combobox_colorspace.currentTextChanged.connect(self.Document_Color_Space)
        self.dialog.combobox_bitdepth.currentTextChanged.connect(self.Document_Bit_Depth)
        self.dialog.spinbox_dpi.valueChanged.connect(self.Document_DPI)
        # Notices
        self.dialog.manual.clicked.connect(self.Menu_Manual)
        self.dialog.license.clicked.connect(self.Menu_License)
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
        #region Menus
        self.menu_project = Project_Options(self.layout.project)
        self.menu_project.SIGNAL_PROJECT.connect(self.Menu_Project)

        self.menu_page = Page_Options(self.layout.page)
        self.menu_page.SIGNAL_PAGE.connect(self.Menu_Page)
        #endregion
    def Style(self):
        # Icons
        self.layout.project.setIcon(Krita.instance().icon('bundle_archive'))
        self.layout.page.setIcon(Krita.instance().icon('zoom-print'))
        self.layout.settings.setIcon(Krita.instance().icon('settings-button'))

        # ToolTips
        self.layout.project.setToolTip("Project")
        self.layout.page.setToolTip("Page")
        self.layout.settings.setToolTip("Settings")

        # StyleSheets
        self.layout.progress_bar.setStyleSheet("#progress_bar{background-color: rgba(0, 0, 0, 0);}")
    def Settings(self):
        pass

    #endregion
    #region Menu ###################################################################
    def Menu_Project(self, SIGNAL_PROJECT):
        case = SIGNAL_PROJECT
        if case == "NEW":
            self.Project_New()
        if case == "OPEN":
            self.Project_Open()
        if case == "SAVE":
            self.ZIP_Save()
        if case == "CLOSE":
            self.ZIP_Close()
    def Menu_Page(self, SIGNAL_PAGE):
        case = SIGNAL_PAGE
        if case == "NEW":
            self.Page_New()
        if case == "ADD":
            self.Page_Add()
        if case == "DELETE":
            self.Page_Delete()

    #endregion
    #region Menu Signals ###########################################################
    def Document_Basename(self, doc_basename):
        self.doc_basename = doc_basename
        Krita.instance().writeSetting("Project Pages", "doc_basename", str( self.doc_basename ))
        self.update()
    def Document_Dim_Width(self, doc_width):
        self.doc_width = doc_width
        Krita.instance().writeSetting("Project Pages", "doc_width", str( self.doc_width ))
        self.update()
    def Document_Dim_Height(self, doc_height):
        self.doc_height = doc_height
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

            # Search Matching File
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

    #endregion
    #region ZIP ####################################################################
    def ZIP_New(self, path, name):
        if self.project_active == False:
            # Close Previous Project
            self.ZIP_Close()

            # Paths
            project_directory = os.path.normpath( os.path.join(path , name) )
            project_zip = os.path.normpath( project_directory + "." + file_extension )

            exists = (os.path.exists(project_directory)) and (os.path.exists(project_zip))
            if exists == False:
                # Paths
                self.project_zip = project_zip
                self.project_directory = os.path.normpath( project_directory )
                control = os.path.normpath( os.path.join(project_directory, "control.eo") )
                self.project_images = os.path.normpath( os.path.join(project_directory, "IMAGES") )
                self.project_texts = os.path.normpath( os.path.join(project_directory, "TEXTS") )
                self.project_trash = os.path.normpath( os.path.join(project_directory, "TRASH") )

                # Create Project Folders
                mode = 0o666
                os.mkdir( self.project_directory, mode )
                os.mkdir( self.project_images, mode )
                os.mkdir( self.project_texts, mode )
                os.mkdir( self.project_trash, mode )
                # Create Project Files
                file = open( control, "w" )
                file.write( "project_pages" )

                # Create File ZIP
                shutil.make_archive( self.project_directory, 'zip', self.project_directory ) # Creates the ZIP

                # Update
                self.layout.path_text.setText(os.path.basename(self.project_zip))
                self.project_active = True
                self.Files_List()
            else:
                QMessageBox.information(QWidget(), i18n("Warnning"), i18n("Error : Name Conflict"))
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
                    # Variables
                    self.project_active = True
                    # Variables
                    self.project_zip = project_zip
                    self.project_directory = project_directory
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
                else:
                    QMessageBox.information(QWidget(), i18n("Warnning"), i18n("Error : Invalid File"))
            else:
                QMessageBox.information(QWidget(), i18n("Warnning"), i18n("Error : Name Conflict"))
    def ZIP_Save(self):
        # Save Creates/Overwrites the ZIP file
        if self.project_active == True:
            shutil.make_archive(self.project_directory, 'zip', self.project_directory)
            self.Files_List()
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
    def ZIP_Exit(self, project_directory):
        if (self.project_active == True and os.path.isdir(project_directory) == True):
            try:
                shutil.rmtree(project_directory)
            except:
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
                    Krita.instance().action('add_new_paint_layer').trigger() # create a layer to paint
                    Krita.instance().activeDocument().saveAs( file_img ) # save file to project folder

                    break

            # Update
            self.Files_List()
            self.Index_Range(self.found_images, self.found_texts)
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
                    destination = os.path.normpath( self.project_images )
                    # Copy Image
                    shutil.copy(source_i, destination)
                    # Create Text
                    name = self.Path_Components(source_i)
                    file_txt = os.path.normpath( self.project_texts + "\\" + name + ".eo" )
                    note = open(file_txt, "w")
                    note.write("")
                    note.close()

            # Update
            self.Files_List()
            self.Index_Range(self.found_images, self.found_texts)
    def Page_Delete(self):
        if self.project_active == True:
            # path
            item = self.layout.image_list.currentItem()
            if item != None:
                image = item.text()
                text = str( os.path.splitext(image)[0] ) + ".eo"
                if (image != "" and image != None):
                    # Image File
                    try:
                        path_image = os.path.normpath( os.path.join( self.project_images, image ) )
                        shutil.move( path_image, self.project_trash, copy_function = shutil.copytree )
                    except:
                        pass
                    # Backup Image
                    try:
                        path_backup = os.path.normpath( os.path.join( self.project_images, image+"~" ) )
                        shutil.move( path_backup, self.project_trash, copy_function = shutil.copytree )
                    except:
                        pass
                    # Text File
                    try:
                        path_text = os.path.normpath( os.path.join( self.project_texts, text ) )
                        shutil.move( path_text, self.project_trash, copy_function = shutil.copytree )
                    except:
                        pass

                    # Update
                    self.Files_List()
                    self.Index_Range(self.found_images, self.found_texts)

    def Insert_Document(self):
        # Item
        basename = self.layout.image_list.currentItem().text()
        path = os.path.normpath( os.path.join(self.project_images, basename) )

        # Create Document
        document = Krita.instance().openDocument( path )
        Application.activeWindow().addView( document )

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
        if (self.project_active == True and len(self.found_images) > 0):
            # Images List Draw
            self.layout.image_list.clear()
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
    def resizeEvent(self, event):
        pass
    def enterEvent(self, event):
        pass
    def leaveEvent(self, event):
        pass
    def closeEvent(self, event):
        self.ZIP_Exit( self.project_directory )

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

    #region Testing ################################################################
    """
    def Start(self):
        self.file_01 = os.path.normpath("C:\\Users\\EyeOd\\Desktop\\project KRA test\\file_01.kra")
        self.file_02 = os.path.normpath("C:\\Users\\EyeOd\\Desktop\\project KRA test\\file_02.kra")
        self.f1 = Krita.instance().openDocument(self.file_01)
        self.f2 = Krita.instance().openDocument(self.file_02)

        self.view = Krita.instance().activeWindow().addView(self.f1)

    def Doc_1(self):
        QtCore.qDebug( "----------------------------")
        QtCore.qDebug( "self.f1 = " + str( self.f1 ) )
        QtCore.qDebug( "self.f2 = " + str( self.f2 ) )

        # Krita.instance().activeWindow().showView(self.view)

        self.f1 = Krita.instance().openDocument(self.file_01)
        Krita.instance().activeWindow().activeView().setDocument(self.f1)

    def Doc_2(self):
        QtCore.qDebug( "----------------------------")
        QtCore.qDebug( "self.f1 = " + str( self.f1 ) )
        QtCore.qDebug( "self.f2 = " + str( self.f2 ) )

        # Krita.instance().activeWindow().showView(self.v2)

        self.f2 = Krita.instance().openDocument(self.file_02)
        Krita.instance().activeWindow().activeView().setDocument(self.f2)

    def Close(self):
        pass
    def View(self):
        window = Krita.instance().windows()
        view = Krita.instance().views()

        QtCore.qDebug( "----------------------------")
        QtCore.qDebug( "window = " + str( window ) )
        QtCore.qDebug( "view = " + str( view ) )
    """
    #endregion


class Project_Options(QWidget):
    SIGNAL_PROJECT = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(Project_Options, self).__init__(parent)
        # Variables
        self.widget_height = 25
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    def mousePressEvent(self, event):
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            # Menu
            cmenu = QMenu(self)
            # Actions
            cmenu_header = cmenu.addSection("Project")
            cmenu_new = cmenu.addAction("New")
            cmenu_open = cmenu.addAction("Open")
            cmenu_save = cmenu.addAction("Save")
            cmenu_close = cmenu.addAction("Close")

            # Execute
            position = self.mapToGlobal( QPoint( self.x(), self.y()+self.widget_height ) )
            action = cmenu.exec_(position)
            # Triggers
            if action == cmenu_new:
                self.SIGNAL_PROJECT.emit("NEW")
            elif action == cmenu_open:
                self.SIGNAL_PROJECT.emit("OPEN")
            elif action == cmenu_save:
                self.SIGNAL_PROJECT.emit("SAVE")
            elif action == cmenu_close:
                self.SIGNAL_PROJECT.emit("CLOSE")


class Page_Options(QWidget):
    SIGNAL_PAGE = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(Page_Options, self).__init__(parent)
        # Variables
        self.widget_height = 25
    def sizeHint(self):
        return QtCore.QSize(5000,5000)

    def mousePressEvent(self, event):
        if (event.buttons() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.NoModifier):
            # Menu
            cmenu = QMenu(self)
            # Actions
            cmenu_header = cmenu.addSection("Page")
            cmenu_new = cmenu.addAction("New")
            cmenu_add = cmenu.addAction("Add")
            cmenu_delete = cmenu.addAction("Delete")

            # Execute
            position = self.mapToGlobal( QPoint( self.x(), self.y()+self.widget_height ) )
            action = cmenu.exec_(position)
            # Triggers
            if action == cmenu_new:
                self.SIGNAL_PAGE.emit("NEW")
            elif action == cmenu_add:
                self.SIGNAL_PAGE.emit("ADD")
            elif action == cmenu_delete:
                self.SIGNAL_PAGE.emit("DELETE")


"""
To Do:
- Rename with new order of the QlistWidget

- See items in trash
- control.eo unused? what is it for?
- pages with same name conflict. Page Add might add a page with prexisting name

- One view for all documents? Is it even worth it? or just openning documents is enough?

- Autosave Project or Manual Save Project ?
"""