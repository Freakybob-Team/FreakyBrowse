# Hai there! Welcome to the main file of FreakyBrowse!
# If ya see any issues, plz make an issue on our github!
# Feel free to add anything or fix anything!
# - Freakybob-Team <3
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWidgets import QToolBar, QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QUrl, QSettings
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QTextEdit, QInputDialog, QMessageBox
from PyQt6.QtWidgets import QApplication, QTextEdit, QInputDialog
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkReply
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import requests
import mimetypes

import sys
import os
from pypresence import Presence
from pypresence.exceptions import InvalidPipe

RPC = None
haveDiscord = None
try:
    RPC = Presence("1312584606637101156")
    RPC.connect()
    RPC.update(
        details="Browsing the interwebs!",
        buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
        large_image="icon.png",
        large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
    )
    haveDiscord = "True"
except InvalidPipe:
    print("")
    haveDiscord = "False"
except Exception as e:
    print("")
    haveDiscord = "False"

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and bundled apps """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class DownloadManagerWindow(QDialog):
    def __init__(self, parent=None):
        super(DownloadManagerWindow, self).__init__(parent)
        self.setWindowTitle("Download Manager")
        self.download_manager = DownloadManager(self)
        self.download_manager.download_progress.connect(self.update_progress)
        self.download_manager.download_complete.connect(self.download_complete)
        self.download_manager.download_error.connect(self.download_error)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.url_label = QLabel("URL:")
        layout.addWidget(self.url_label)
        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)

        self.file_name_label = QLabel("File Name (optional):")
        layout.addWidget(self.file_name_label)
        self.file_name_input = QLineEdit()
        layout.addWidget(self.file_name_input)

        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Status:")
        layout.addWidget(self.status_label)

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def download_complete(self, file_name):
        self.status_label.setText(f"Download complete: {file_name}")
        self.progress_bar.setValue(100)

    def download_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")

    def start_download(self):
        url = self.url_input.text()
        file_name = self.file_name_input.text().strip()

        if not url:
            self.status_label.setText("Error: URL is required.")
            return

        if not file_name:
            file_name = self.download_manager.get_file_name(url)

        self.progress_bar.setValue(0)
        self.status_label.setText("Downloading...")
        self.download_manager.get(url, file_name)


class DownloadManager(QObject):
    download_progress = pyqtSignal(int)
    download_complete = pyqtSignal(str)
    download_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super(DownloadManager, self).__init__(parent)
        self.parent = parent

    def get(self, url, file_name):
        self.thread = QThread(self)
        self.worker = DownloadWorker(url, file_name)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.start)
        self.worker.download_progress.connect(self.download_progress.emit)
        self.worker.download_complete.connect(self.download_complete.emit)
        self.worker.download_error.connect(self.download_error.emit)
        self.worker.download_complete.connect(self.thread.quit)
        self.worker.download_complete.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def get_file_name(self, url):
        file_name = os.path.basename(url.split("?")[0])
        if not file_name:
            return "downloaded_file"

        mime_type, _ = mimetypes.guess_type(file_name)
        if mime_type:
            file_extension = mimetypes.guess_extension(mime_type)
            if file_extension and not file_name.endswith(file_extension):
                file_name += file_extension
        return file_name


class DownloadWorker(QObject):
    download_progress = pyqtSignal(int)
    download_complete = pyqtSignal(str)
    download_error = pyqtSignal(str)

    def __init__(self, url, file_name):
        super(DownloadWorker, self).__init__()
        self.url = url if url.startswith("http") else "http://" + url
        self.file_name = file_name

    def start(self):
        try:
            with requests.get(self.url, stream=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0))
                if total_length == 0:
                    self.download_error.emit("Unable to determine file size.")
                    return


                mime_type = r.headers.get('content-type', '')
                if mime_type == 'application/zip' or self.file_name.endswith('.pyz'):
                    self.file_name = self.ensure_zip_extension(self.file_name)

                with open(self.file_name, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = int((downloaded / total_length) * 100)
                            self.download_progress.emit(progress)

            self.download_complete.emit(self.file_name)
        except Exception as e:
            self.download_error.emit(str(e))

    def ensure_zip_extension(self, file_name):
        if not file_name.endswith('.zip'):
            base_name, _ = os.path.splitext(file_name)
            return base_name + '.zip'
        return file_name
class MainWindow(QMainWindow):
    HOME_URL = "https://search.freakybob.site/"
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.resize(900, 700)
        self.setWindowTitle("FreakyBrowse 2.2 - by the Freakybob Team.")
        try:
            icon_path = resource_path("icons/logo_new.ico")
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Error loading icon: {e}")
        self.download_manager = DownloadManager(self)

        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        
        self.home_url = MainWindow.HOME_URL
        self.setCentralWidget(self.tabs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.navtb = QToolBar("Navigation")
        self.addToolBar(self.navtb)
        
        
        back_btn = QAction(QIcon(resource_path("icons/back.png")), "Back", self)
        back_btn.setStatusTip("Go back")
        back_btn.triggered.connect(lambda: self.current_browser().back())
        self.navtb.addAction(back_btn)

        next_btn = QAction(QIcon(resource_path("icons/forward.png")), "Forward", self)
        next_btn.setStatusTip("Go forward")
        next_btn.triggered.connect(lambda: self.current_browser().forward())
        self.navtb.addAction(next_btn)

        reload_btn = QAction(QIcon(resource_path("icons/refresh.png")), "Reload", self)
        reload_btn.setStatusTip("Reload the page")
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        self.navtb.addAction(reload_btn)

        home_btn = QAction(QIcon(resource_path("icons/home.png")), "Home", self)
        home_btn.setStatusTip("Go back to home")
        home_btn.triggered.connect(self.navigate_home)
        self.navtb.addAction(home_btn)

        settings_btn = QAction(QIcon(resource_path("icons/settings.png")), "Settings", self)
        settings_btn.setStatusTip("Open Settings")
        settings_btn.triggered.connect(self.open_settings)
        self.navtb.addAction(settings_btn)

        new_tab_btn = QAction(QIcon(resource_path("icons/new_tab.png")), "New Tab", self)
        new_tab_btn.setStatusTip("Open a new tab")
        new_tab_btn.triggered.connect(self.add_new_tab)
        self.navtb.addAction(new_tab_btn)

        self.navtb.addSeparator()


        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.navtb.addWidget(self.urlbar)
        self.urlbar.setPlaceholderText("Enter URL...")
        logo_action = QAction(QIcon(resource_path("icons/logo.png")), "Logo", self.urlbar)
        self.urlbar.addAction(logo_action, QLineEdit.ActionPosition.LeadingPosition)
        self.urlbar.setClearButtonEnabled(True)

        pikidiary_btn = QAction(QIcon(resource_path("icons/piki.png")), "PikiDiary", self)
        pikidiary_btn.setStatusTip("Go to PikiDiary!")
        pikidiary_btn.triggered.connect(self.pikidiary)
        self.navtb.addAction(pikidiary_btn)

        notes_button = QAction(QIcon(resource_path("icons/notes1.png")), "Manage Notes", self)
        notes_button.setStatusTip("Manage your notes")
        notes_button.triggered.connect(self.manage_notes)
        self.navtb.addAction(notes_button)

        

        bookmark_btn = QAction(QIcon(resource_path("icons/bookmark.png")), "Bookmark", self)
        bookmark_btn.setStatusTip("Bookmark this page!")
        bookmark_btn.triggered.connect(self.bookmark_page)
        self.navtb.addAction(bookmark_btn)

        view_bookmarks_btn = QAction(QIcon(resource_path("icons/bookmarks.png")), "Bookmarks", self)
        view_bookmarks_btn.setStatusTip("View all bookmarks")
        view_bookmarks_btn.triggered.connect(self.show_bookmarks)
        self.navtb.addAction(view_bookmarks_btn)

        view_source_btn = QAction(QIcon(resource_path("icons/source.png")), "View Source", self)
        view_source_btn.setStatusTip("View the source of the current page")
        view_source_btn.triggered.connect(self.view_page_source)
        self.navtb.addAction(view_source_btn)

        download_btn = QAction(QIcon(resource_path("icons/download.png")), "Download Manager", self)
        download_btn.setStatusTip("Open Download Manager")
        download_btn.triggered.connect(self.open_download_manager)
        self.navtb.addAction(download_btn)
        
        self.settings = QSettings("FreakyBrowse", "UserSettings")
        self.pink_mode_enabled = self.settings.value("pink_mode", False, type=bool)
        self.blue_mode_enabled = self.settings.value("blue_mode", False, type=bool)
        self.green_mode_enabled = self.settings.value("green_mode", False, type=bool)
        self.orange_mode_enabled = self.settings.value("orange_mode", False, type=bool)
        self.red_mode_enabled = self.settings.value("red_mode", False, type=bool)
        self.oceanic_blue_enabled = self.settings.value("oceanic_blue_mode", False, type=bool)
        self.lavender_mode_enabled = self.settings.value("lavender_mode", False, type=bool)
        self.retro_green_mode_enabled = self.settings.value("retro_green_mode", False, type=bool)
        self.purple_mode_enabled = self.settings.value("purple_mode", False, type=bool)

        
        self.settings = QSettings("FreakyBrowse", "RPC2Settings")
        self.rpc_enabled = self.settings.value("rpc_enabled", True, type=bool)
        self.warned_about_rpc = False
        self.update_rpc_state()

       

        self.toggle_mode()

        
        self.add_new_tab(QUrl(self.HOME_URL), "New Tab")
        self.show()

        
        self.bookmarks = self.settings.value("bookmarks", [], type=list)

        

    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None:
            qurl = QUrl(self.HOME_URL)

        if not isinstance(qurl, QUrl):
            qurl = QUrl(self.HOME_URL)

        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.titleChanged.connect(lambda title, browser=browser: self.update_tab_title(title, browser))

        self.tabs.setStyleSheet("""
        QTabBar::tab:selected {
            font-weight: bold
        }
    """)
        
    
    
        if haveDiscord == "True" and self.rpc_enabled:
            try:
                RPC.update(
                    state="Looking at " + str(self.HOME_URL),
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
                print("Updated RPC! (New tab)")
            except Exception as e:
                print(f"Error updating RPC: {e}")
                if "style" in RPC.state:
                    RPC.update(
                        details="Browsing the interwebs!",
                        buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                        large_image="icon.png",
                        large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                    )
    def update_tab_title(self, title, browser):
        index = self.tabs.indexOf(browser)
        self.tabs.setTabText(index, title)
    def pikidiary(self):
        url = QUrl("https://pikidiary.lol")
        self.add_new_tab(url, "FUCKING PEAK YAYAY")
        if haveDiscord == "True" and self.rpc_enabled:
            try:
                RPC.update(
                    state="Looking at " + str( self.urlbar.text()),
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icons/piki.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
                print("Updated RPC! (Navigated to URL)")
            except Exception as e:
                print(f"Error updating RPC: {e}")
                if "style" in RPC.state:
                    RPC.update(
                        details="Browsing the interwebs!",
                        buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                        large_image="icon.png",
                        large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                    )


    def navigate_home(self):
        self.current_browser().setUrl(QUrl(self.HOME_URL))

    def navigate_to_url(self):
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme("https")
        if q.isValid():
            if q.scheme() == "freak":
                freak_path = q.path().lstrip('/')
                if freak_path == "changelog":
                    self.current_browser().load(QUrl("https://freakybrowse.freakybob.site/freak/changelog"))
                else:
                    QMessageBox.warning(self, "Invalid URL", "Unknown freak:/ URL")
        
            else:
                self.current_browser().setUrl(q)
            
            if haveDiscord == "True" and self.rpc_enabled:
                try:
                    RPC.update(
                        state="Looking at " + str( self.urlbar.text()),
                        buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                        large_image="icon.png",
                        large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                    )
                    print("Updated RPC! (Navigated to URL)")
                except Exception as e:
                    print(f"Error updating RPC: {e}")
                    if "style" in RPC.state:
                        RPC.update(
                            details="Browsing the interwebs!",
                            buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                            large_image="icon.png",
                            large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                        )
                        # tried showing the URL but it also showed the style, if we can fix that this would be fire fr
                        # HOLY CRAP I FIXED IT - wish
                        # gg !! - greg
        else:
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL.")
        if haveDiscord == "True" and self.rpc_enabled and "chrome" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="Commiting a sin",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "freakybob.site" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="Browsing peak, freakybob.site",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "https://rentahitman.com/" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="Oooohh interesting IP address!",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "pikidiary.lol" and "PikiDiary.lol" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="This user is peak! Speaking of peak, check out PikiDiary!",
                    buttons=[{"label": "PikiDiary", "url": "https://pikidiary.lol"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "x.com" and "X.com" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="You know there's always a nearby therapist office",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "reddit.com" and "Reddit" and "reddit" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="wikihow is always a last resort",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "classroom.google.com" and "Classroom.Google.com" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="im sorry for you",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "archive.org" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="This user is either a huge nerd or a pirator. Prob both tbh",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "apple.com" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="We're more open than them, y'know?",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "match.com" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="On FreakyBrowse? Really",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
        if haveDiscord == "True" and self.rpc_enabled and "redditforcommunity.com" and "www.reddit.com/r/modhelp/" in str(self.urlbar.text()):
            try:
                RPC.update(
                    details="Weight.. being.. gained..",
                    buttons=[{"label": "Get FreakyBrowse", "url": "https://github.com/Freakybob-Team/Freakybrowse/releases/latest"}],
                    large_image="icon.png",
                    large_text="FreakyBrowse next to a search glass with Freakybob inside of the glass."
                )
            except Exception as e:
                print(f"Error updating RPC: {e}")
    def update_urlbar(self, q, browser=None):
        if browser != self.current_browser():
            return
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def current_browser(self):
        return self.tabs.currentWidget()

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)



    def load_style_from_file(self, style_name):
        if hasattr(sys, '_MEIPASS'):
            styles_folder = os.path.join(sys._MEIPASS, 'styles')
        else:
            styles_folder = os.path.join(os.path.dirname(__file__), 'styles')

   
        style_path = os.path.join(styles_folder, f"{style_name}.qss")
    
        if os.path.exists(style_path):
            with open(style_path, "r") as style_file:
                style = style_file.read()
                self.setStyleSheet(style)
        else:
            print(f"Style file '{style_name}.qss' not found at {style_path}!")
    def open_browser_settings(self):
        
        browser_dialog = QDialog(self)
        browser_dialog.setWindowTitle("Browser Settings")
        layout = QVBoxLayout()

        
        use_google_checkbox = QCheckBox("Use Google's main page?")
        use_google_checkbox.setChecked(self.home_url == "https://google.com")
        use_google_checkbox.stateChanged.connect(
            lambda state: self.toggle_homepage_url(state, home_url_label))
        layout.addWidget(use_google_checkbox)
        warning_label = QLabel("This does not bring you to https://google.com when you start the app. This just changes the Home button location and new tab location :P (This also doesn't save yet :PPP)")
        home_url_label = QLabel(f"Current Home URL: {self.home_url}")
        layout.addWidget(warning_label)
        layout.addWidget(home_url_label)

        use_rpc_checkbox = QCheckBox("Use FreakyBrowese's Discord RPC?")
        use_rpc_checkbox.setChecked(self.rpc_enabled)
        use_rpc_checkbox.stateChanged.connect(self.toggle_rpc)
        layout.addWidget(use_rpc_checkbox)
        
        warn_label = QLabel("If you disable FreakyBrowse's Discord RPC, it will not be enabled again until you reinstall or update.")
        layout.addWidget(warn_label)

        close_button = QPushButton("Close")
        close_button.clicked.connect(browser_dialog.accept)
        layout.addWidget(close_button)

        browser_dialog.setLayout(layout)
        browser_dialog.exec()

    def toggle_rpc(self, state):
        if self.rpc_enabled and not self.warned_about_rpc:
            reply = QMessageBox.question(self, "Warning", 
                                     "Are you sure you want to disable Discord RPC? This action cannot be undone unless you reinstall or update.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                self.sender().setChecked(self.rpc_enabled)
                return

            self.warned_about_rpc = True

        self.rpc_enabled = state == Qt.CheckState.Checked
        self.settings.setValue("rpc_enabled", self.rpc_enabled)
        print(f"RPC toggled: {'Enabled' if self.rpc_enabled else 'Disabled'}")
        self.update_rpc_state()

    def update_rpc_state(self):
        if self.rpc_enabled:
            try:
                print("RPC is now enabled.")
            except Exception as e:
                print(f"Error enabling RPC: {e}")
        else:
            try:
                RPC.clear()
                print("RPC is now disabled.")
            except Exception as e:
                print(f"Error disabling RPC: {e}")

        


    def toggle_mode(self):
        if self.pink_mode_enabled:
            self.load_style_from_file("pink_mode")
        elif self.blue_mode_enabled:
            self.load_style_from_file("blue_mode")
        elif self.green_mode_enabled:
            self.load_style_from_file("green_mode")
        elif self.red_mode_enabled:
            self.load_style_from_file("red_mode")
        elif self.orange_mode_enabled:
            self.load_style_from_file("orange_mode")
        elif self.oceanic_blue_enabled:
            self.load_style_from_file("oceanic_blue_mode")
        elif self.lavender_mode_enabled:
            self.load_style_from_file("lavender_mode")
        elif self.retro_green_mode_enabled:
            self.load_style_from_file("retro_green_mode")
        elif self.purple_mode_enabled:
            self.load_style_from_file("purple_mode")
        else:
            self.load_style_from_file("dark_mode")


    
    def toggle_retro_green_mode(self, enabled):
        if enabled:
            self.orange_mode_enabled = False
            self.red_mode_enabled = False
            self.dark_mode_enabled = False
            self.blue_mode_enabled = False
            self.green_mode_enabled = False
            self.pink_mode_enabled = False
            self.oceanic_blue_enabled = False
            self.lavender_mode_enabled = False
        self.retro_green_mode_enabled = enabled
        self.settings.setValue("pink_mode", self.pink_mode_enabled)
        self.settings.setValue("orange_mode", self.orange_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", self.oceanic_blue_enabled)
        self.settings.setValue("red_mode", self.red_mode_enabled)
        self.settings.setValue("blue_mode", self.blue_mode_enabled)
        self.settings.setValue("green_mode", self.green_mode_enabled)
        self.settings.setValue("Lavender_mode", self.lavender_mode_enabled)
        self.settings.setValue("retro_green_mode", enabled)
        self.settings.setValue("purple_mode", self.purple_mode_enabled)
        self.toggle_mode()
    def toggle_pink_mode(self, enabled):
        if enabled:
            self.orange_mode_enabled = False
            self.red_mode_enabled = False
            self.dark_mode_enabled = False
            self.blue_mode_enabled = False
            self.green_mode_enabled = False
            self.oceanic_blue_enabled = False
            self.retro_green_mode_enabled = False
            self.purple_mode_enabled = False
        self.lavender_mode_enabled = False
        self.pink_mode_enabled = enabled
        self.settings.setValue("pink_mode", enabled)
        self.settings.setValue("lavender_mode", self.lavender_mode_enabled)
        self.settings.setValue("orange_mode", self.orange_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", self.oceanic_blue_enabled)
        self.settings.setValue("red_mode", self.red_mode_enabled)
        self.settings.setValue("blue_mode", self.blue_mode_enabled)
        self.settings.setValue("green_mode", self.green_mode_enabled)
        self.settings.setValue("retro_green_mode", self.retro_green_mode_enabled)
        self.settings.setValue("purple_mode", self.purple_mode_enabled)
        self.toggle_mode()
    def toggle_orange_mode(self, enabled):
        if enabled:
            self.red_mode_enabled = False
            self.dark_mode_enabled = False
            self.pink_mode_enabled = False
            self.blue_mode_enabled = False
            self.green_mode_enabled = False
            self.oceanic_blue_enabled = False
            self.retro_green_mode_enabled = False
            self.purple_mode_enabled = False
        self.orange_mode_enabled = enabled
        self.settings.setValue("pink_mode", self.pink_mode_enabled)
        self.settings.setValue("orange_mode", enabled)
        self.settings.setValue("red_mode", self.red_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", self.oceanic_blue_enabled)
        self.settings.setValue("blue_mode", self.blue_mode_enabled)
        self.settings.setValue("green_mode", self.green_mode_enabled)
        self.settings.setValue("Lavender_mode", self.lavender_mode_enabled)
        self.settings.setValue("retro_green_mode", self.retro_green_mode_enabled)
        self.settings.setValue("purple_mode", self.purple_mode_enabled)
        self.toggle_mode()
    
    def toggle_blue_mode(self, enabled):
        if enabled:
            self.orange_mode_enabled = False
            self.red_mode_enabled = False
            self.dark_mode_enabled = False
            self.pink_mode_enabled = False
            self.green_mode_enabled = False
            self.oceanic_blue_enabled = False
            self.retro_green_mode_enabled = False
            self.purple_mode_enabled = False
        self.blue_mode_enabled = enabled
        self.settings.setValue("pink_mode", self.pink_mode_enabled)
        self.settings.setValue("orange_mode", self.orange_mode_enabled)
        self.settings.setValue("red_mode", self.red_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", self.oceanic_blue_enabled)
        self.settings.setValue("blue_mode", enabled)
        self.settings.setValue("green_mode", self.green_mode_enabled)
        self.settings.setValue("Lavender_mode", self.lavender_mode_enabled)
        self.settings.setValue("retro_green_mode", self.retro_green_mode_enabled)
        self.settings.setValue("purple_mode", self.purple_mode_enabled)
        self.toggle_mode()
        

    def toggle_green_mode(self, enabled):
        if enabled:
            self.orange_mode_enabled = False
            self.red_mode_enabled = False
            self.dark_mode_enabled = False
            self.pink_mode_enabled = False
            self.blue_mode_enabled = False
            self.oceanic_blue_enabled = False
            self.retro_green_mode_enabled = False
            self.purple_mode_enabled = False
        self.green_mode_enabled = enabled
        self.settings.setValue("pink_mode", self.pink_mode_enabled)
        self.settings.setValue("orange_mode", self.orange_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", self.oceanic_blue_enabled)
        self.settings.setValue("red_mode", self.red_mode_enabled)
        self.settings.setValue("blue_mode", self.blue_mode_enabled)
        self.settings.setValue("green_mode", enabled)
        self.settings.setValue("Lavender_mode", self.lavender_mode_enabled)
        self.settings.setValue("retro_green_mode", self.retro_green_mode_enabled)
        self.settings.setValue("purple_mode", self.purple_mode_enabled)
        self.toggle_mode()
    def toggle_red_mode(self, enabled):
        if enabled:
            self.dark_mode_enabled = False
            self.pink_mode_enabled = False
            self.blue_mode_enabled = False
            self.green_mode_enabled = False
            self.orange_mode_enabled = False
            self.oceanic_blue_enabled = False
            self.retro_green_mode_enabled = False
            self.purple_mode_enabled = False
        self.red_mode_enabled = enabled
        self.settings.setValue("pink_mode", self.pink_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", self.oceanic_blue_enabled)
        self.settings.setValue("orange_mode", self.orange_mode_enabled)
        self.settings.setValue("red_mode", enabled)
        self.settings.setValue("blue_mode", self.blue_mode_enabled)
        self.settings.setValue("green_mode", self.green_mode_enabled)
        self.settings.setValue("Lavender_mode", self.lavender_mode_enabled)
        self.settings.setValue("retro_green_mode", self.retro_green_mode_enabled)
        self.settings.setValue("purple_mode", self.purple_mode_enabled)
        self.toggle_mode()
    def toggle_oceanic_blue_mode(self, enabled):
        if enabled:
            self.pink_mode_enabled = False
            self.orange_mode_enabled = False
            self.red_mode_enabled = False
            self.dark_mode_enabled = False
            self.blue_mode_enabled = False
            self.green_mode_enabled = False
            self.retro_green_mode_enabled = False
            self.purple_mode_enabled = False
        self.oceanic_blue_enabled = enabled
        self.settings.setValue("pink_mode", self.pink_mode_enabled)
        self.settings.setValue("orange_mode", self.orange_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", enabled)
        self.settings.setValue("red_mode", self.red_mode_enabled)
        self.settings.setValue("blue_mode", self.blue_mode_enabled)
        self.settings.setValue("green_mode", self.green_mode_enabled)
        self.settings.setValue("Lavender_mode", self.lavender_mode_enabled)
        self.settings.setValue("retro_green_mode", self.retro_green_mode_enabled)
        self.settings.setValue("purple_mode", self.purple_mode_enabled)
        self.toggle_mode()
    def toggle_lavender_mode(self, enabled):
        if enabled:
            self.pink_mode_enabled = False
            self.orange_mode_enabled = False
            self.red_mode_enabled = False
            self.dark_mode_enabled = False
            self.blue_mode_enabled = False
            self.green_mode_enabled = False
            self.oceanic_blue_enabled = False
            self.retro_green_mode_enabled = False
            self.purple_mode_enabled = False

        self.lavender_mode_enabled = enabled
        self.settings.setValue("pink_mode", self.pink_mode_enabled)
        self.settings.setValue("orange_mode", self.orange_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", self.oceanic_blue_enabled)
        self.settings.setValue("Lavender_mode", enabled)
        self.settings.setValue("red_mode", self.red_mode_enabled)
        self.settings.setValue("blue_mode", self.blue_mode_enabled)
        self.settings.setValue("green_mode", self.green_mode_enabled)
        self.settings.setValue("retro_green_mode", self.retro_green_mode_enabled)
        self.settings.setValue("purple_mode", self.purple_mode_enabled)
        self.toggle_mode()
    def toggle_purple_mode(self, enabled):
        if enabled:
            self.pink_mode_enabled = False
            self.blue_mode_enabled = False
            self.green_mode_enabled = False
            self.red_mode_enabled = False
            self.orange_mode_enabled = False
            self.oceanic_blue_enabled = False
            self.retro_green_mode_enabled = False
            self.lavender_mode_enabled = False
        self.purple_mode_enabled = enabled
        self.settings.setValue("pink_mode", self.pink_mode_enabled)
        self.settings.setValue("orange_mode", self.orange_mode_enabled)
        self.settings.setValue("oceanic_blue_mode", self.oceanic_blue_enabled)
        self.settings.setValue("red_mode", self.red_mode_enabled)
        self.settings.setValue("blue_mode", self.blue_mode_enabled)
        self.settings.setValue("green_mode", self.green_mode_enabled)
        self.settings.setValue("Lavender_mode", self.lavender_mode_enabled)
        self.settings.setValue("retro_green_mode", self.retro_green_mode_enabled)
        self.settings.setValue("purple_mode", enabled)  
        self.toggle_mode()

    def open_style_settings(self):
        style_dialog = QDialog(self)
        style_dialog.setWindowTitle("Style Settings")
        style_dialog.setFixedSize(400, 400)
        style_dialog.setStyleSheet("""
            background-color: #17786d;
            border-radius: 10px;
        """)
    
        layout = QVBoxLayout()

        main_label = QLabel("Style Settings")
        main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        main_label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        layout.addWidget(main_label)

        styles = [
            ("Pink Mode", self.pink_mode_enabled, self.toggle_pink_mode),
            ("Blue Mode", self.blue_mode_enabled, self.toggle_blue_mode),
            ("Green Mode", self.green_mode_enabled, self.toggle_green_mode),
            ("Red Mode", self.red_mode_enabled, self.toggle_red_mode),
            ("Orange Mode", self.orange_mode_enabled, self.toggle_orange_mode),
            ("Oceanic Blue Mode", self.oceanic_blue_enabled, self.toggle_oceanic_blue_mode),
            ("Lavender Mode", self.lavender_mode_enabled, self.toggle_lavender_mode),
            ("Retro Green Mode", self.retro_green_mode_enabled, self.toggle_retro_green_mode),
            ("Dark Purple", self.purple_mode_enabled, self.toggle_purple_mode)
        ]
    
        for label, enabled, toggle_func in styles:
            checkbox = QCheckBox(f"Enable {label}")
            checkbox.setChecked(enabled)
            checkbox.setStyleSheet("font-size: 14px; padding: 5px;")
            checkbox.stateChanged.connect(lambda checked, func=toggle_func: func(checked))
            layout.addWidget(checkbox)

        button_layout = QVBoxLayout()
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            background-color: #0078d4;
            color: white;
            padding: 4px;
            border-radius: 5px;
            font-size: 14px;
        """)
        close_button.clicked.connect(style_dialog.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
    
        style_dialog.setLayout(layout)
        style_dialog.exec()

    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Settings")
        
       
        settings_dialog.resize(100, 100)  

        
        layout = QVBoxLayout()

        style_button = QPushButton("Style Settings")
        style_button.clicked.connect(self.open_style_settings)
        layout.addWidget(style_button)

        browser_stg_button = QPushButton("Browser Settings")
        browser_stg_button.clicked.connect(self.open_browser_settings)
        layout.addWidget(browser_stg_button)
        
        info_button = QPushButton("Info")
        info_button.clicked.connect(self.open_info_button)
        layout.addWidget(info_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(settings_dialog.accept)

        layout.addWidget(close_button)

        settings_dialog.setLayout(layout)
        settings_dialog.exec()  


    
    
    def open_info_button(self):
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("FreakyBrowse Info")
        info_dialog.setFixedSize(940, 510)
        info_dialog.setStyleSheet("""
        background-color: #477168;
        """)

        layout = QVBoxLayout()

        title_label = QLabel("𝓯𝓻𝓮𝓪𝓴𝔂Browse Info")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #333333;")
        layout.addWidget(title_label)

        below_label1 = QLabel("FreakyBrowse, by the Freakybob Team.")
        below_label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        below_label1.setFont(QFont("Arial", 11, QFont.Weight.Normal))
        below_label1.setStyleSheet("color:#333333;")
        layout.addWidget(below_label1)

        version_layout = QHBoxLayout()
        version_label = QLabel("Version: 2.2!!!!")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setFont(QFont("Arial", 11, QFont.Weight.Normal))
        version_label.setStyleSheet("color: white;")
        version_layout.addWidget(version_label)

        image_label = QLabel()
        image_label.setPixmap(QPixmap("images/Cube004.png"))
        image_label.setScaledContents(True)
        version_layout.addWidget(image_label)
        layout.addLayout(version_layout)

        title_label2 = QLabel("Sorta History")
        title_label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label2.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label2.setStyleSheet("color: #333333;")
        layout.addWidget(title_label2)

        info_label = QLabel("FreakyBrowse was made on Oct 13th 2024. It first started out as code stolen from stackoverflow but was updated to work and look better.\nThe first time we started to try to distribute FreakyBrowse, it was flagged as a trojan. It was a false positive from what wish13yt used to turn the code into an exe.\nSince Pyinstaller sucks and gave false positives, we are starting to use the direct python file!!")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setFont(QFont("Arial", 10, QFont.Weight.Normal))
        info_label.setStyleSheet("color: white;")
        layout.addWidget(info_label)

        your_info_title = QLabel("Your Info")
        your_info_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        your_info_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        your_info_title.setStyleSheet("color: #333333;")
        layout.addWidget(your_info_title)

        your_info_label = QLabel("FreakyBrowse does not use your personal info. Every website you visit is your choice to give THEM your info.\nYou do have to agree to the Privacy Policy on search.freakybob.site.\nYou can find it by pressing 'here' on search.freakybob.site.\n Some dependencies we use may also use your data. We can't do anything about this.")
        your_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        your_info_label.setFont(QFont("Arial", 10, QFont.Weight.Normal))
        your_info_label.setStyleSheet("color: white;")
        layout.addWidget(your_info_label)

        gpl_label = QLabel("License?")
        gpl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gpl_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        gpl_label.setStyleSheet("color: #333333;")
        layout.addWidget(gpl_label)

        info_label2 = QLabel("Everything is GPL-3")
        info_label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label2.setFont(QFont("Arial", 10, QFont.Weight.Normal))
        info_label2.setStyleSheet("color: white;  ")
        layout.addWidget(info_label2)

        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
        background-color: #0078d4;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        margin-top: 15px;
        """)
        close_button.clicked.connect(info_dialog.accept)
        layout.addWidget(close_button)

        info_dialog.setLayout(layout)
        info_dialog.exec()

    def toggle_homepage_url(self, state, home_url_label):
        if state == 2:
            
            MainWindow.HOME_URL = "https://google.com"
            self.home_url = MainWindow.HOME_URL
        else:
           
            MainWindow.HOME_URL = "https://search.freakybob.site/"
            self.home_url = MainWindow.HOME_URL

        home_url_label.setText(f"Current Home URL: {self.home_url}")
        print(f"Home URL set to: {self.home_url}")

    
        
    def manage_notes(self):
        notes_dialog = QDialog(self)
        notes_dialog.setWindowTitle("Notes Manager")
        notes_dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout()

    
        notes_list = QListWidget()
        layout.addWidget(notes_list)

    
        saved_notes = self.settings.value("notes", {}, type=dict)
        for note_name in saved_notes.keys():
            notes_list.addItem(note_name)
    
        button_layout = QHBoxLayout()

    
        add_note_button = QPushButton("Add Note")
    
        add_note_button.clicked.connect(lambda: self.add_note_dialog(notes_list, saved_notes))
        button_layout.addWidget(add_note_button)

    
        delete_note_button = QPushButton("Delete Note")
        delete_note_button.clicked.connect(lambda: self.delete_note(notes_list, saved_notes))
        button_layout.addWidget(delete_note_button)

        layout.addLayout(button_layout)

        download_note_button = QPushButton("Download Note")
        download_note_button.clicked.connect(lambda: self.download_note_as_txt(notes_list, saved_notes))
        button_layout.addWidget(download_note_button)

        note_viewer = QTextEdit()
        note_viewer.setReadOnly(False)
        layout.addWidget(note_viewer)

    
        upload_image_button = QPushButton("Insert Image")
        upload_image_button.clicked.connect(lambda: self.insert_image(note_viewer))
        layout.addWidget(upload_image_button)

    
        def load_note_content():
            selected_item = notes_list.currentItem()
            if selected_item:
                note_content = saved_notes.get(selected_item.text(), "")
                note_viewer.setHtml(note_content)
            else:
                note_viewer.clear()
        notes_list.itemSelectionChanged.connect(load_note_content)
          

    
        def save_note_content():
            selected_item = notes_list.currentItem()
            if selected_item:
                saved_notes[selected_item.text()] = note_viewer.toHtml()
                self.settings.setValue("notes", saved_notes)

        note_viewer.textChanged.connect(save_note_content)

        notes_dialog.setLayout(layout)
        notes_dialog.exec()
        
    def add_note_dialog(self, notes_list, saved_notes):
        text, ok = QInputDialog.getText(self, "Add Note", "Enter note name:")
    
   
        if not ok:
            return

   
        if text:
            notes_list.addItem(text)
        saved_notes[text] = ""

   
        self.settings.setValue("notes", saved_notes)

   
        item = notes_list.findItems(text, Qt.MatchFlag.MatchExactly)[0]
        notes_list.setCurrentItem(item)

   
        note_viewer = self.findChild(QTextEdit) 
        note_viewer.setHtml("")
        note_viewer.setFocus()


    def delete_note(self, notes_list, saved_notes):
        if notes_list.count() == 0:
            QMessageBox.warning(self, "No Notes to Delete", "Vro, there are no notes to delete.")
            return

        selected_item = notes_list.currentItem()
        selected_item = notes_list.currentItem()
        if selected_item:
            note_name = selected_item.text()
        confirm = QMessageBox.question(self, "Delete Note", f"Are you sure you want to delete '{note_name}'?", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                       QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            
            notes_list.takeItem(notes_list.row(selected_item))
            
            
            saved_notes.pop(note_name, None)
            
            
            self.settings.setValue("notes", saved_notes)
    def insert_image(self, note_viewer):
        image_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not image_path:
            return 
    
        width, ok = QInputDialog.getInt(self, "Image Width", "Enter image width:", 300, 1, 10000, 1)
        if not ok:
            return

        height, ok = QInputDialog.getInt(self, "Image Height", "Enter image height:", 300, 1, 10000, 1)
        if not ok:
            return

    
        file_extension = image_path.split('.')[-1].lower()

        if file_extension == "gif":
        
            note_viewer.insertHtml(f'<img src="{image_path}" width="{width}" height="{height}" alt="GIF">')
        else:
        
            note_viewer.insertHtml(f'<img src="{image_path}" width="{width}" height="{height}">')
    def download_note_as_txt(self, notes_list, saved_notes):
        selected_item = notes_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Note Selected", "Please select a note to download.")
            return

   
        note_name = selected_item.text()
        note_content = saved_notes.get(note_name, "")

    
        temp_editor = QTextEdit()
        temp_editor.setHtml(note_content)
        plain_text_content = temp_editor.toPlainText()

    
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Note As",
            f"{note_name}.txt",
            "Text Files (*.txt)"
        )
        if not file_path:
            return

    
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(plain_text_content)
            QMessageBox.information(self, "Download Successful", f"'{note_name}' has been downloaded as '{file_path}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error Saving File", f"An error occurred: {e}")



    def bookmark_page(self):
        url = self.current_browser().url().toString()
        if url not in self.bookmarks:
            self.bookmarks.append(url)
            self.settings.setValue("bookmarks", self.bookmarks)
            QMessageBox.information(self, "Bookmark Added", f"{url} has been bookmarked.")
        else:
            QMessageBox.warning(self, "Already Bookmarked", "This page is already in your bookmarks.")

    def show_bookmarks(self):
        bookmarks_dialog = QDialog(self)
        bookmarks_dialog.setWindowTitle("Bookmarks")

        layout = QVBoxLayout()

        for url in self.bookmarks:
            bookmark_layout = QHBoxLayout()

            bookmark_label = QLabel(url)
            bookmark_layout.addWidget(bookmark_label)

            open_btn = QPushButton("Open")
            open_btn.clicked.connect(lambda _, url=url: self.add_new_tab(QUrl(url), url))
            bookmark_layout.addWidget(open_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda _, url=url: self.delete_bookmark(url, bookmarks_dialog))
            bookmark_layout.addWidget(delete_btn)

            layout.addLayout(bookmark_layout)

        close_button = QPushButton("Close")
        close_button.clicked.connect(bookmarks_dialog.accept)
        layout.addWidget(close_button)

        bookmarks_dialog.setLayout(layout)
        bookmarks_dialog.exec() # bookmarks_dialog.exec_() is deprecated in PyQt6

    def delete_bookmark(self, url, dialog):
        if url in self.bookmarks:
            self.bookmarks.remove(url)
            self.settings.setValue("bookmarks", self.bookmarks)
            dialog.accept()
            self.show_bookmarks()

    def view_page_source(self):
     
        current_browser = self.current_browser()
        
       
        current_browser.page().toHtml(lambda html: self.show_html(html))
    def show_html(self, html):
        html_viewer = QDialog(self)
        html_viewer.setWindowTitle("Page Source")
        html_viewer.setMinimumSize(800, 600)
        layout = QVBoxLayout()
        html_text_edit = QTextEdit()
        html_text_edit.setPlainText(html)
        html_text_edit.setReadOnly(True)
        layout.addWidget(html_text_edit)
        close_button = QPushButton("Close")
        close_button.clicked.connect(html_viewer.accept)
        layout.addWidget(close_button)
        html_viewer.setLayout(layout)
        html_viewer.exec() # html_viewer.exec_() is deprecated in PyQt6

    def open_download_manager(self):
        self.download_manager_window = DownloadManagerWindow(self)
        self.download_manager_window.show()

    def on_download_finished(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            content = reply.readAll()
            file_name = reply.url().fileName()
            with open(file_name, "wb") as file:
                file.write(content)
            self.status.showMessage(f"Downloaded {file_name}")
        else:
            self.status.showMessage(f"Download failed: {reply.errorString()}")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("FreakyBrowse.2.2")
    app.setWindowIcon(QIcon("logo_new.ico")) 
    
    window = MainWindow()
    app.exec() # app.exec_() is deprecated in PyQt6
#I am steve :33333 GREG GREG GREG I HATE YOU !!!!VFYUGEIHLJ:K:D<MNFKGILEHQODJLK:A?<
