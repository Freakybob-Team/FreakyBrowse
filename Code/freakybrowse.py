from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
import sys

class MainWindow(QMainWindow):
    HOME_URL = "https://search.freakybob.site/"
    DARK_MODE_STYLE = """
    QMainWindow {
        background-color: #2b2b2b;
        color: white;
    }
    QToolBar, QLineEdit, QStatusBar {
        background-color: #3c3c3c;
        color: white;
    }
    QLineEdit {
        border: 1px solid #5c5c5c;
    }
    QToolButton {
        background-color: #3c3c3c;
        color: white;
    }
    QTabWidget::pane {
        border-top: 1px solid #444;
    }
    QTabBar::tab {
        background-color: #3c3c3c;
        color: white;
        padding: 5px;
    }
    QTabBar::tab:selected {
        background-color: #5c5c5c;
        color: white;
    }
    QTabBar::tab:hover {
        background-color: #4c4c4c;
        color: white;
    }
    """

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        try:
            self.setWindowIcon(QIcon("logo.ico"))
        except Exception as e:
            print(f"Error loading icon: {e}")

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.update_title)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)

        self.setCentralWidget(self.tabs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.navtb = QToolBar("Navigation")
        self.addToolBar(self.navtb)

        back_btn = QAction("Back", self)
        back_btn.setStatusTip("Go back")
        back_btn.triggered.connect(lambda: self.current_browser().back())
        self.navtb.addAction(back_btn)

        next_btn = QAction("Forward", self)
        next_btn.setStatusTip("Go forward")
        next_btn.triggered.connect(lambda: self.current_browser().forward())
        self.navtb.addAction(next_btn)

        reload_btn = QAction("Reload", self)
        reload_btn.setStatusTip("Reload the page")
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        self.navtb.addAction(reload_btn)

        home_btn = QAction("Home", self)
        home_btn.setStatusTip("Go home")
        home_btn.triggered.connect(self.navigate_home)
        self.navtb.addAction(home_btn)

        self.navtb.addSeparator()

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.navtb.addWidget(self.urlbar)

        stop_btn = QAction("Stop", self)
        stop_btn.setStatusTip("Stop loading the page")
        stop_btn.triggered.connect(lambda: self.current_browser().stop())
        self.navtb.addAction(stop_btn)

        settings_btn = QAction("Settings", self)
        settings_btn.setStatusTip("Open Settings")
        settings_btn.triggered.connect(self.open_settings)
        self.navtb.addAction(settings_btn)

        bookmark_btn = QAction("Bookmark", self)
        bookmark_btn.setStatusTip("Bookmark this page")
        bookmark_btn.triggered.connect(self.bookmark_page)
        self.navtb.addAction(bookmark_btn)

        view_bookmarks_btn = QAction("View Bookmarks", self)
        view_bookmarks_btn.setStatusTip("View all bookmarks")
        view_bookmarks_btn.triggered.connect(self.show_bookmarks)
        self.navtb.addAction(view_bookmarks_btn)

        view_source_btn = QAction("View Page Source", self)
        view_source_btn.setStatusTip("View the source of the current page")
        view_source_btn.triggered.connect(self.view_page_source)
        self.navtb.addAction(view_source_btn)

        save_page_btn = QAction("Save Page", self)
        save_page_btn.setStatusTip("Save the current page as HTML")
        save_page_btn.triggered.connect(self.save_page)
        self.navtb.addAction(save_page_btn)

        self.settings = QSettings("FreakyBrowse", "UserPreferences")
        self.dark_mode_enabled = self.settings.value("dark_mode", False, type=bool)
        self.nav_toolbar_visible = self.settings.value("nav_toolbar_visible", True, type=bool)

        self.bookmarks = self.settings.value("bookmarks", [], type=list)

        self.navtb.setVisible(True)
        self.toggle_dark_mode(self.dark_mode_enabled)

        self.add_new_tab(QUrl(self.HOME_URL), "New Tab")
        self.show()

    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None:
            qurl = QUrl(self.HOME_URL)

        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i=i, browser=browser: self.tabs.setTabText(i, browser.page().title()))

    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()

    def update_title(self):
        title = self.current_browser().page().title()
        self.setWindowTitle(f"{title} - FreakyBrowse, by the Freakybob Team.")
        self.update_urlbar(self.current_browser().url())

    def navigate_home(self):
        self.current_browser().setUrl(QUrl(self.HOME_URL))

    def navigate_to_url(self):
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme("https")
        if q.isValid():
            self.current_browser().setUrl(q)
        else:
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL.")

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

    def toggle_dark_mode(self, enabled):
        if enabled:
            self.setStyleSheet(self.DARK_MODE_STYLE)
        else:
            self.setStyleSheet("")
        self.dark_mode_enabled = enabled
        self.settings.setValue("dark_mode", self.dark_mode_enabled)

    def toggle_nav_toolbar(self, enabled):
        self.navtb.setVisible(enabled)
        self.nav_toolbar_visible = enabled
        self.settings.setValue("nav_toolbar_visible", self.nav_toolbar_visible)

    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Settings")

        layout = QVBoxLayout()

        dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        dark_mode_checkbox.setChecked(self.dark_mode_enabled)
        dark_mode_checkbox.stateChanged.connect(lambda: self.toggle_dark_mode(dark_mode_checkbox.isChecked()))
        layout.addWidget(dark_mode_checkbox)

        nav_toolbar_checkbox = QCheckBox("Show Navigation Toolbar")
        nav_toolbar_checkbox.setChecked(self.nav_toolbar_visible)
        nav_toolbar_checkbox.stateChanged.connect(lambda: self.toggle_nav_toolbar(nav_toolbar_checkbox.isChecked()))
        layout.addWidget(nav_toolbar_checkbox)

        close_button = QPushButton("Close")
        close_button.clicked.connect(settings_dialog.accept)
        layout.addWidget(close_button)

        settings_dialog.setLayout(layout)
        settings_dialog.exec_()

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
        bookmarks_dialog.exec_()

    def delete_bookmark(self, url, dialog):
        if url in self.bookmarks:
            self.bookmarks.remove(url)
            self.settings.setValue("bookmarks", self.bookmarks)
            dialog.accept()
            self.show_bookmarks()

    def view_page_source(self):
        page_source_dialog = QDialog(self)
        page_source_dialog.setWindowTitle("Page Source")

        layout = QVBoxLayout()

        source_browser = QTextEdit()
        source_browser.setReadOnly(True)
        page = self.current_browser().page()
        page.toHtml(lambda html: source_browser.setText(html))

        layout.addWidget(source_browser)

        close_button = QPushButton("Close")
        close_button.clicked.connect(page_source_dialog.accept)
        layout.addWidget(close_button)

        page_source_dialog.setLayout(layout)
        page_source_dialog.exec_()

    def save_page(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Page", "", "HTML Files (*.html)")
        if filename:
            page = self.current_browser().page()
            page.toHtml(lambda html: self.write_to_file(filename, html))

    def write_to_file(self, filename, content):
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
        QMessageBox.information(self, "Page Saved", f"Page has been saved to {filename}.")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("FreakyBrowse")
    app.setWindowIcon(QIcon("logo.ico")) 
    
    window = MainWindow()
    app.exec_()
#I am steve :33333 GREG GREG GREG I HATE YOU !!!!VFYUGEIHLJ:K:D<MNFKGILEHQODJLK:A?<
