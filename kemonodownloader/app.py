import os
import sys

import qtawesome as qta
import requests
from packaging import version
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QIcon, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from kemonodownloader.creator_downloader import CreatorDownloaderTab
from kemonodownloader.kd_help import HelpTab
from kemonodownloader.kd_language import language_manager, translate
from kemonodownloader.kd_settings import SettingsTab
from kemonodownloader.post_downloader import PostDownloaderTab

CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "VoxDroid/KemonoDownloader"


class VersionChecker(QThread):
    update_available = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            latest_version = data["tag_name"].lstrip("v")
            release_url = data["html_url"]
            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                self.update_available.emit(latest_version, release_url)
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit(translate("no_internet_connection"))
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"{translate('failed_to_check_updates')}: {str(e)}")


def resource_path(relative_path):
    # PyInstaller 打包运行时会临时注入 _MEIPASS 属性；为类型检查忽略
    if hasattr(sys, "_MEIPASS"):  # type: ignore[attr-defined]
        return os.path.join(sys._MEIPASS, relative_path)  # type: ignore[attr-defined]
    else:
        return os.path.join(os.path.dirname(__file__), relative_path)


class KemonoDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(translate("app_title"))
        self.setGeometry(100, 100, 1000, 700)

        self.settings_tab = SettingsTab(self)
        self.base_folder = os.path.join(
            self.settings_tab.settings["base_directory"], self.settings_tab.settings["base_folder_name"]
        )
        self.download_folder = os.path.join(self.base_folder, "Downloads")
        self.cache_folder = os.path.join(self.base_folder, "Cache")
        self.other_files_folder = os.path.join(self.base_folder, "Other Files")
        self.ensure_folders_exist()

        self.setWindowIcon(QIcon(resource_path("resources/KemonoDownloader.png")))

        self.main_widget = self.setup_main_ui()
        self.setCentralWidget(self.main_widget)
        self.apply_palette()

        self.settings_tab.language_changed.connect(self.update_all_ui)

        if self.settings_tab.is_auto_check_updates_enabled():
            self.check_for_updates()

    def apply_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1A2A44"))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor("#2A3B5A"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#3A4B6A"))
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor("#3A5B7A"))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        self.setPalette(palette)

    def ensure_folders_exist(self):
        for folder in [self.base_folder, self.download_folder, self.cache_folder, self.other_files_folder]:
            os.makedirs(folder, exist_ok=True)

    def setup_main_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_widget.setStyleSheet("background: #1A2A44;")

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: none;
                background: #1A2A44;
            }
            QTabBar::tab {
                background: #3A4B6A;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #4A5B7A;
                color: white;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            QTabBar::tab:disabled {
                color: gray;
            }
            * {
                color: white;
            }
        """
        )
        main_layout.addWidget(self.tabs)

        self.post_tab = PostDownloaderTab(self)
        self.tabs.addTab(self.post_tab, qta.icon("fa5s.download", color="white"), translate("post_downloader_tab"))

        self.creator_tab = CreatorDownloaderTab(self)
        self.tabs.addTab(
            self.creator_tab, qta.icon("fa5s.user-edit", color="white"), translate("creator_downloader_tab")
        )

        self.tabs.addTab(self.settings_tab, qta.icon("fa5s.cog", color="white"), translate("settings_tab"))

        self.help_tab = HelpTab(self)
        self.tabs.addTab(self.help_tab, qta.icon("fa5s.question-circle", color="white"), translate("help_tab"))

        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        self.status_label = QLabel(translate("idle"))
        self.status_label.setStyleSheet("color: white; font-size: 12px;")
        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()
        self.dev_label = QLabel(
            f"{translate('developed_by')} | GitHub: @VoxDroid | {translate('current_version', CURRENT_VERSION)}"
        )
        self.dev_label.setStyleSheet("color: white; font-size: 12px;")
        footer_layout.addWidget(self.dev_label)
        main_layout.addWidget(footer)

        return main_widget

    def update_all_ui(self):
        self.setWindowTitle(translate("app_title"))

        if self.main_widget:
            self.tabs.setTabText(0, translate("post_downloader_tab"))
            self.tabs.setTabText(1, translate("creator_downloader_tab"))
            self.tabs.setTabText(2, translate("settings_tab"))
            self.tabs.setTabText(3, translate("help_tab"))

            if (
                self.status_label.text() == "Idle"
                or self.status_label.text() == "アイドル"
                or self.status_label.text() == "대기 중"
            ):
                self.status_label.setText(translate("idle"))

            self.dev_label.setText(
                f"{translate('developed_by')} | GitHub: @VoxDroid | {translate('current_version', CURRENT_VERSION)}"
            )

            self.post_tab.refresh_ui()
            self.creator_tab.refresh_ui()
            self.settings_tab.update_ui_text()
            self.help_tab.update_ui_text()

    def check_for_updates(self):
        self.version_checker = VersionChecker()
        self.version_checker.update_available.connect(self.show_update_notification)
        self.version_checker.error_occurred.connect(self.show_error_notification)
        self.version_checker.start()

    def show_update_notification(self, new_version, url):
        msg = QMessageBox(self)
        msg.setWindowTitle(translate("update_available"))
        msg.setText(translate("update_available_message", new_version))
        msg.setInformativeText(
            f"{translate('current_version', CURRENT_VERSION)}\n"
            f'<a href="{url}" style="color: #A0C0FF; text-decoration: none;">{translate("click_release_page")}</a>'
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Ignore)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setStyleSheet(
            """
            QMessageBox {
                background-color: #2A3B5A;
                border: 1px solid #3A4B6A;
                border-radius: 8px;
            }
            QMessageBox QLabel {
                color: #FFFFFF;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton {
                background-color: #4A6B9A;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5A7BA9;
            }
            QPushButton:pressed {
                background-color: #3A5B7A;
            }
        """
        )
        reply = msg.exec()
        if reply == QMessageBox.StandardButton.Ok:
            import webbrowser

            webbrowser.open(url)

    def show_error_notification(self, error_message):
        msg = QMessageBox(self)
        msg.setWindowTitle(translate("update_check_failed"))
        msg.setText(translate("unable_check_updates"))
        msg.setInformativeText(error_message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet(
            """
            QMessageBox {
                background-color: #2A3B5A;
                border: 1px solid #3A4B6A;
                border-radius: 8px;
            }
            QMessageBox QLabel {
                color: #FFFFFF;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton {
                background-color: #4A6B9A;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5A7BA9;
            }
            QPushButton:pressed {
                background-color: #3A5B7A;
            }
        """
        )
        msg.exec()

    def animate_button(self, button, enter):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        rect = button.geometry()
        if enter:
            anim.setEndValue(rect.adjusted(-3, -3, 3, 3))
        else:
            anim.setEndValue(rect.adjusted(3, 3, -3, -3))
        anim.start()

    def log(self, message):
        self.status_label.setText(message)
        print(message)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = KemonoDownloader()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
