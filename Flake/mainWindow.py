import gi
import os
# import library.getFiles as count
from .library.getContent import *
# from .library.getContent import *
from threading import Thread
from .newImage import *


gi.require_version(namespace='Gtk', version='4.0')
gi.require_version(namespace='Adw', version='1')

from gi.repository import Adw, Gio, Gtk

Adw.init()
flowbox = Gtk.FlowBox.new()
libraryPath = ""
dir = str(pathlib.Path.home()) + "/.local/share/Flake"
widgets = []

if(not os.path.exists(dir)):
    os.mkdir(dir)

class mainWindow(Gtk.ApplicationWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.createImageBox = newImageBox()

        self.switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_default_size(750,450)
        self.set_title(title='Flake - library')
        # self.set_size_request(750,450)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.set_child(self.stack)

        global flowbox

        flowbox.set_margin_top(margin=12)
        flowbox.set_margin_end(margin=12)
        flowbox.set_margin_bottom(margin=12)
        flowbox.set_margin_start(margin=12)
        flowbox.set_valign(align=Gtk.Align.START)
        flowbox.set_max_children_per_line(n_children=10)
        flowbox.set_selection_mode(mode=Gtk.SelectionMode.NONE)

        self.addBox(False)

        self.stack.add_child(child=self.createImageBox)

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

    def addBox(self, refresh):

        global flowbox

        if not refresh:
            self.stack.add_child(child=flowbox)
        elif refresh:
            self.stack.remove_child(flowbox)


    def images():
        global widgets
        global dir
        global flowbox
        global imagesNum
        test = FlakePreferences()
        imagesDir = test.settings.get_string("librarypath")
        appslist = os.listdir(imagesDir)
        appsInfo = getFileNum(appslist, imagesDir, dir)
        imagesNum = appsInfo.appimages
        time.sleep(0.5)
        for n in range(appsInfo.appimages):
            element = createElements(None, appsInfo.names[n], dir)
            widgets.append(element)
            flowbox.insert(element, position=n)

imagesNum = None

class Flake(Adw.Application):

    def __init__(self,AppId):
        super().__init__(application_id=AppId,
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.create_action('show_in_folder', self.show_in_folder)
        self.create_action('preferences', self.show_preferences)
        self.create_action('about', self.show_about)
        self.create_action('refresh', self.refresh)

        # self.create_action('quit', self.do_shutdown, ['<primary>q'])

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = mainWindow(application=self)
        win.present()

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_shutdown(self):
        global dir
        shutil.rmtree(dir + "/squashfs-root")
        Gtk.Application.do_shutdown(self)
        self.quit()

    def show_preferences(self, action, param):
        adw_preferences_window = FlakePreferences()
        adw_preferences_window.show()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)

    def show_about(self, action, param):
        dialog = Adw.AboutWindow()
        dialog.set_application_name=("Flake")
        dialog.set_version("0.0.4")
        dialog.set_developer_name("Leonardo Salani")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_comments("GTK user insterface for appimagekit")
        dialog.set_website("https://github.com/SalaniLeo/Flake")
        dialog.set_developers(["salaniLeo"])
        dialog.set_application_icon("io.github.salaniLeo.flake")
        dialog.present()
        
    def show_in_folder(self, action, param):
        os.system('xdg-open "%s"' % libraryPath)

    def refresh(self, action, param):
        global flowbox
        global imagesNum
        for n in range(imagesNum):
            flowbox.remove(widgets[n].get_parent())
        getContent.refresh()
        t1 = Thread(target=mainWindow.images)
        t1.start()

    def createImage(button, self):
        self.get_style_context().add_class(class_name='devel')
        self.stack.set_visible_child(self.createImageBox)
        self.headerbar.remove(self.newAppImage)
        self.headerbar.pack_start(self.backButton)
        self.headerbar.pack_start(self.advancedOptions)
        self.set_title(title='Flake - new')

    def goBack(button, self):
        self.get_style_context().remove_class(class_name='devel')
        self.stack.set_visible_child(self.flowbox)
        self.headerbar.remove(self.backButton)
        self.headerbar.remove(self.advancedOptions)
        self.headerbar.pack_start(self.newAppImage)
        self.set_title(title='Flake - library')

class FlakePreferences(Adw.PreferencesWindow):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(title='Preferences')
        self.settings = Gio.Settings.new("io.github.salanileo.flake")
        autoDeleteOption = self.settings.get_boolean("removeappdir")
        autoFolderMode = self.settings.get_boolean("foldermode")
        autoCustomAppRun = self.settings.get_boolean("customapprun")
        self.libraryPath = self.settings.get_string("librarypath")

        # self.connect('close-request', self.do_shutdown)

        prefercePage = Adw.PreferencesPage.new()
        self.add(page=prefercePage)

        imageCreatorOptions = Adw.PreferencesGroup.new()
        imageCreatorOptions.set_title(title='General')

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
        libraryOptions.set_title(title='Library')

        prefercePage.add(group=libraryOptions)
        prefercePage.add(group=imageCreatorOptions)

        self.libraryPathEntry = Gtk.Entry.new()
        self.libraryPathEntry.set_valign(align=Gtk.Align.CENTER)

        self.libraryPathEntry.set_text(self.libraryPath)
        # self.libraryPathButton = Gtk.Button.new_from_icon_name("document-open-symbolic") 
        # self.libraryPathButton.set_size_request(40,10)


        self.libraryPathEntry.connect('changed', self.saveString, "librarypath")
        global libraryPath
        libraryPath = self.libraryPathEntry.get_text()

        libraryPathRow = Adw.ActionRow.new()
        libraryPathRow.set_title(title='Library location')
        libraryPathRow.set_subtitle("To apply changes restart the app")
        libraryPathRow.add_suffix(widget=self.libraryPathEntry)
        # libraryPathRow.add_suffix(widget=self.libraryPathButton)

        libraryOptions.add(child=libraryPathRow)

        self.changedPath = False

    def saveOpt(self, switch, GParamBoolean, key):
        self.settings.set_boolean(key, switch.get_state())

    def saveString(self, entry, key):
        if os.path.exists(entry.get_text()):
                self.changedPath = True
                self.settings.set_string(key, entry.get_text())
                self.libraryPathEntry.get_style_context().remove_class(class_name='error')
        else:
                self.settings.set_string(key, str(pathlib.Path.home()) + "/Applications")
                self.libraryPathEntry.get_style_context().add_class(class_name='error')

    # def do_shutdown(self, quit):
        # Flake.refresh(self, None, None)





if __name__ == '__main__':
    import sys

    app = Flake()
    app.run(sys.argv)

