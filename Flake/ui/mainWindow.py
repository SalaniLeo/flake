import gi
import time
import os
from ..library.getContent import *
from threading import Thread
from .newImage import *
from .uiElements import *

gi.require_version(namespace='Gtk', version='4.0')
gi.require_version(namespace='Adw', version='1')

from gi.repository import Adw, Gio, Gtk

##Global Variables
Adw.init()

flatpak = False
contentWindow = Adw.PreferencesPage.new()
# contentWindow = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=12)
dir = str(pathlib.Path.home()) + "/.local/share/Flake"
widgets = []
changedPath = False
toast_overlay = Adw.ToastOverlay.new()
page = None
settings = Gio.Settings.new("io.github.salanileo.flake")


##checks if app data dir exists and if not creates it
if(not os.path.exists(dir)):
    os.mkdir(dir)

##main app window
class mainWindow(Gtk.ApplicationWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        page = self

        self.createImageBox = newImageBox(self)
        self.createImageBox.okButton.connect('clicked', newImageBox.initCreation, Flake.refresh, page)
        newImageBox.getFlatpak(flatpak)

        self.switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_default_size(750,450)
        self.set_title(title='Flake - library')

        ##stack that contains the scrolled and newImage
        self.stack = Gtk.Stack()
        #scrolled that contains the flowbox
        self.scrolled = Gtk.ScrolledWindow()

        #adds as child toast_overlay, that contains everything
        self.set_child(child=toast_overlay)

        #adds as toast_overlay child stack
        toast_overlay.set_child(child=self.stack)

        #adds as scrolled child flowbox
        # self.scrolled.set_child(contentWindow)

        #adds the 2 pages to stack
        self.stack.add_child(child=contentWindow)
        self.stack.add_child(child=self.createImageBox)

        #Main stack
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)

        t1 = Thread(target=mainWindow.images)
        t1.start()

        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(titlebar=self.headerbar)

        about = Gio.SimpleAction.new("about", None)
        about.connect("activate", Flake.show_about)

        self.show_in_folder = Gtk.Button.new()
        
        show_in_folder = Gio.SimpleAction.new("show_in_folder", None)
        show_in_folder.connect("activate", Flake.show_in_folder)

        menu_button_model = Gio.Menu()

        menu_button_model.append('Refresh', 'app.refresh')
        menu_button_model.append('Show in folder', 'app.show_in_folder')
        menu_button_model.append('Preferences', 'app.preferences')
        menu_button_model.append('About', 'app.about')

        menuButton = Gtk.MenuButton.new()
        menuButton.set_icon_name(icon_name='open-menu-symbolic')
        menuButton.set_menu_model(menu_model=menu_button_model)
        self.headerbar.pack_end(child=menuButton)

        self.newAppImage = Gtk.Button()
        self.newAppImage.connect('clicked', Flake.createImage, self)
        self.newAppImage.set_icon_name(icon_name='list-add-symbolic')
        self.headerbar.pack_start(child=self.newAppImage)

        self.backButton = Gtk.Button.new_from_icon_name("pan-start-symbolic") 
        self.backButton.connect("clicked", Flake.goBack, self)

        self.advancedOptions = Gtk.Box()
        self.advancedSwitch = Gtk.Switch()
        self.advancedLabel = Gtk.Label(label="Advanced")
        self.advancedLabel.set_margin_end(12)
        self.advancedOptions.append(self.advancedLabel)
        self.advancedOptions.append(self.advancedSwitch)
        self.advancedSwitch.connect("state-set", newImageBox.showAdvanced)

    def images():
        global imagesNum
        global page

        libraryPath = settings.get_string("librarypath")

        appslist = os.listdir(libraryPath)
        appsInfo = getFileNum(appslist, libraryPath)
        imagesNum = appsInfo.appimages
        time.sleep(0.1)

        # print(appslist)
        for n in range(imagesNum):
            element = getImages.createElements(appsInfo.names[n], Flake.refresh, page, setRowState, flatpak)
            widgets.append(element)
            contentWindow.add(widgets[n])

imagesNum = None

class Flake(Adw.Application):

    def __init__(self,AppId, isFlatpak):
        super().__init__(application_id=AppId,
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.create_action('show_in_folder', self.show_in_folder)
        self.create_action('preferences', self.show_preferences)
        self.create_action('about', self.show_about)
        self.create_action('refresh', self.refresh)

        global flatpak
        flatpak = isFlatpak

        # self.create_action('quit', self.do_shutdown, ['<primary>q'])

    def do_activate(self):
        global page
        page = self.props.active_window
        if not page:
            page = mainWindow(application=self)
            page.present()

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_shutdown(self):
        # shutil.rmtree(dir + "/squashfs-root")
        Gtk.Application.do_shutdown(self)
        self.quit()

    def show_preferences(self, action, param):

        adw_preferences_window = FlakePreferences(page)
        adw_preferences_window.show()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)

    def show_about(self, action, param):
        dialog = Adw.AboutWindow()
        dialog.set_application_name('Flake')
        dialog.set_version("0.0.4")
        # dialog.set_developer_name("Leonardo Salani")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_comments("GTK user insterface for appimagekit")
        dialog.set_website("https://github.com/SalaniLeo/Flake")
        dialog.set_developers(["Leonardo Salani"])
        dialog.set_application_icon("io.github.salaniLeo.flake")
        dialog.present()
        
    def show_in_folder(self, action, param):
        global settings
        libraryPath = settings.get_string("librarypath")
        os.system('xdg-open "%s"' % libraryPath)

    def refresh(self, action, param):
        for n in range(imagesNum):
            contentWindow.remove(widgets[0])
            widgets.remove(widgets[0])
        getImages.restart_count()
        t1 = Thread(target=mainWindow.images)
        t1.start()
        t1.join()

    def createImage(button, self):
        self.stack.set_visible_child(self.createImageBox)
        self.headerbar.remove(self.newAppImage)
        self.headerbar.pack_start(self.backButton)
        self.headerbar.pack_start(self.advancedOptions)
        self.set_title(title='Flake - new')

    def goBack(button, self):
        self.stack.set_visible_child(contentWindow)
        self.headerbar.remove(self.backButton)
        self.headerbar.remove(self.advancedOptions)
        self.headerbar.pack_start(self.newAppImage)
        self.set_title(title='Flake - library')

    def newToast(self, title, action):

        toast = Adw.Toast.new(title='')
        toast.set_title(title=title)
        toast.set_timeout(True)
        toast.set_button_label("Refresh")
        toast.set_action_name(action)

        return toast

class FlakePreferences(Adw.PreferencesWindow):

    def __init__(self, parent,  **kwargs):
        super().__init__(**kwargs)   

        global settings

        autoDeleteOption = settings.get_boolean("removeappdir")
        autoFolderMode = settings.get_boolean("foldermode")
        autoCustomAppRun = settings.get_boolean("customapprun")
        libraryPath = settings.get_string("librarypath")
        uselibraryPath = settings.get_boolean("uselibrarypath")

        self.set_title(title='Preferences')

        self.set_transient_for(parent)
        self.set_modal(True)


        self.connect('close-request', self.do_shutdown)

        prefercePage = Adw.PreferencesPage.new()
        self.add(page=prefercePage)

        imageCreatorOptions = Adw.PreferencesGroup.new()
        imageCreatorOptions.set_title(title='General options')

        self.autoDelete = Gtk.Switch.new()
        self.autoDelete.set_valign(align=Gtk.Align.CENTER)
        self.autoDelete.connect('notify::active', self.saveOpt, "removeappdir")
        self.autoDelete.set_state(autoDeleteOption)

        deleteADRow = Adw.ActionRow.new()
        deleteADRow.set_title(title='Auto delete AppDir')
        deleteADRow.add_suffix(widget=self.autoDelete)
        imageCreatorOptions.add(child=deleteADRow)

        self.autoFolderMSw = Gtk.Switch.new()
        self.autoFolderMSw.set_valign(align=Gtk.Align.CENTER)
        self.autoFolderMSw.connect('notify::active', self.saveOpt, "foldermode")
        self.autoFolderMSw.set_state(autoFolderMode)

        autoFolderMRow = Adw.ActionRow.new()
        autoFolderMRow.set_title(title='Enable FolderMode by default')
        autoFolderMRow.add_suffix(widget=self.autoFolderMSw)
        imageCreatorOptions.add(child=autoFolderMRow)

        self.autoCustomARSw = Gtk.Switch.new()
        self.autoCustomARSw.set_valign(align=Gtk.Align.CENTER)
        self.autoCustomARSw.connect('notify::active', self.saveOpt, "customapprun")
        self.autoCustomARSw.set_state(autoCustomAppRun)

        autoCustomARRow = Adw.ActionRow.new()
        autoCustomARRow.set_title(title='Enable custom AppRun by default')
        autoCustomARRow.add_suffix(widget=self.autoCustomARSw)
        imageCreatorOptions.add(child=autoCustomARRow)

        libraryOptions = Adw.PreferencesGroup.new()
        libraryOptions.set_title(title='Library options')

        newImageOptions = Adw.PreferencesGroup.new()
        newImageOptions.set_title(title='New image options')

        prefercePage.add(group=libraryOptions)
        prefercePage.add(group=imageCreatorOptions)
        prefercePage.add(group=newImageOptions)

        self.libraryPathEntry = pathEntry(libraryPath)
        self.libraryPathEntry.connect('changed', self.saveString, "librarypath")

        self.browseLibLoc = browseButton(fileChooser, 'select library location', True, self.libraryPathEntry, page)

        libraryPathRow = Adw.ActionRow.new()
        libraryPathRow.set_title(title='Library location')
        libraryPathRow.set_subtitle("To apply changes restart the app")
        libraryPathRow.add_suffix(widget=self.libraryPathEntry)
        libraryPathRow.add_suffix(widget=self.browseLibLoc)


        libraryOptions.add(child=libraryPathRow)

        global changedPath

        changedPath = False

        useLPath = Gtk.Switch.new()
        useLPath.set_valign(align=Gtk.Align.CENTER)
        useLPath.connect('notify::active', self.useLPath, "uselibrarypath")
        useLPath.set_state(uselibraryPath)

        useLPathRow = Adw.ActionRow.new()
        useLPathRow.set_title(title='Use library folder as default')
        useLPathRow.set_subtitle('Uses library folder as default location when creating new apps')
        useLPathRow.add_suffix(widget=useLPath)

        newImageOptions.add(child=useLPathRow)


    def saveOpt(self, switch, GParamBoolean, key):
        global settings
        settings.set_boolean(key, switch.get_state())

    def useLPath(self, switch, GParamBoolean, key):
        global settings
        settings.set_boolean(key, switch.get_state())
        newImageBox.sameOutput(switch.get_state())

    def saveString(self, entry, key):
        global changedPath
        global settings
        if os.path.exists(entry.get_text()):
                changedPath = True
                settings.set_string(key, entry.get_text())
        else:
                settings.set_string(key, str(pathlib.Path.home()) + "/Applications")

    def do_shutdown(self, quit):
        global changedPath

        if(changedPath):
            toast_overlay.add_toast(Flake.newToast(self, "Library path changed", "app.refresh"))

if __name__ == '__main__':
    import sys

    app = Flake()
    app.run(sys.argv)