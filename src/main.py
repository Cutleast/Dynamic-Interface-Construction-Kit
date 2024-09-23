"""
Name: Dynamic Interface Construction Kit (DICK)
Author: Cutleast
License: Attribution-NonCommercial-NoDerivatives 4.0 International
Python Version: 3.11.2
Qt Version: 6.5.1
"""

import logging
import os
import shutil
import pyperclip as clipboard
import sys
import time
from pathlib import Path

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import errors
import utils


class MainApp(qtw.QApplication):
    """
    Main application class.
    """

    name = "Dynamic Interface Construction Kit"
    version = "1.0.2"

    creator_thread: utils.Thread = None
    done_signal = qtc.Signal()
    start_time: int = None

    def __init__(self):
        super().__init__()

        self.log = logging.getLogger(self.__repr__())
        log_format = "[%(asctime)s.%(msecs)03d]"
        log_format += "[%(levelname)s]"
        log_format += "[%(name)s.%(funcName)s]: "
        log_format += "%(message)s"
        self.log_format = logging.Formatter(
            log_format,
            datefmt="%d.%m.%Y %H:%M:%S"
        )
        self.std_handler = utils.StdoutHandler(self)
        self.log_str = logging.StreamHandler(self.std_handler)
        self.log_str.setFormatter(self.log_format)
        self.log.addHandler(self.log_str)
        self.log_level = 10 # Debug level
        self.log.setLevel(self.log_level)
        self._excepthook = sys.excepthook
        sys.excepthook = self.handle_exception

        self.root = qtw.QWidget()
        self.root.setWindowTitle(f"{self.name} v{self.version}")
        self.root.setStyleSheet((Path(".") / "assets" / "style.qss").read_text())
        self.root.setWindowIcon(qtg.QIcon("./assets/icon.ico"))
        self.root.setMinimumWidth(1000)
        self.root.setMinimumHeight(500)

        self.layout = qtw.QVBoxLayout()
        self.root.setLayout(self.layout)

        self.conf_layout = qtw.QGridLayout()
        self.layout.addLayout(self.conf_layout)

        patched_path_label = qtw.QLabel("Enter Path to patched Mod:")
        self.conf_layout.addWidget(patched_path_label, 0, 0)
        self.patched_path_entry = qtw.QLineEdit()
        self.conf_layout.addWidget(self.patched_path_entry, 0, 1)
        patched_path_button = qtw.QPushButton("Browse...")

        def browse_patched_path():
            file_dialog = qtw.QFileDialog(self.root)
            file_dialog.setWindowTitle("Browse patched Mod...")
            path = Path(self.patched_path_entry.text()) if self.patched_path_entry.text() else Path(".")
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.patched_path_entry.setText(folder)
        patched_path_button.clicked.connect(browse_patched_path)
        self.conf_layout.addWidget(patched_path_button, 0, 2)

        original_path_label = qtw.QLabel("Enter Path to Original Mod:")
        self.conf_layout.addWidget(original_path_label, 1, 0)
        self.original_path_entry = qtw.QLineEdit()
        self.conf_layout.addWidget(self.original_path_entry, 1, 1)
        original_path_button = qtw.QPushButton("Browse")

        def browse_original_path():
            file_dialog = qtw.QFileDialog(self.root)
            file_dialog.setWindowTitle("Browse Original Mod...")
            path = Path(self.original_path_entry.text()) if self.original_path_entry.text() else Path(".")
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.original_path_entry.setText(folder)
        original_path_button.clicked.connect(browse_original_path)
        self.conf_layout.addWidget(original_path_button, 1, 2)

        self.protocol_widget = qtw.QTextEdit()
        self.protocol_widget.setReadOnly(True)
        self.protocol_widget.setObjectName("protocol")
        self.layout.addWidget(self.protocol_widget, 1)

        cmd_layout = qtw.QHBoxLayout()
        self.layout.addLayout(cmd_layout)

        self.create_button = qtw.QPushButton("Create Patch!")
        self.create_button.clicked.connect(self.run_creator)
        cmd_layout.addWidget(self.create_button)

        copy_log_button = qtw.QPushButton("Copy Log")
        copy_log_button.setFixedWidth(120)
        copy_log_button.clicked.connect(lambda: (
            clipboard.copy(self.protocol_widget.toPlainText().strip())
        ))
        cmd_layout.addWidget(copy_log_button)

        docs_label = qtw.QLabel(
            "\
Need help? \
Read the documentation \
<a href='https://github.com/Cutleast/Dynamic-Interface-Patcher/blob/main/DOCUMENTATION.md'>\
here</a>.\
"
        )
        docs_label.setTextFormat(qtc.Qt.TextFormat.RichText)
        docs_label.setAlignment(qtc.Qt.AlignmentFlag.AlignRight)
        docs_label.setOpenExternalLinks(True)
        self.layout.addWidget(docs_label)

        # Fix link color
        palette = self.palette()
        palette.setColor(
            palette.ColorRole.Link,
            qtg.QColor("#ff6767")
        )
        self.setPalette(palette)

        self.std_handler.output_signal.connect(self.handle_stdout)
        self.std_handler.output_signal.emit(self.std_handler._content)
        self.done_signal.connect(self.done)

        self.log.debug("Program started!")

        self.root.show()
        utils.apply_dark_title_bar(self.root)

    def __repr__(self):
        return "MainApp"

    def check_java(self):
        self.log.info("Checking for java installation...")

        java_installed = utils.check_java()

        if not java_installed:
            self.log.critical("Java could not be found! Patching not possible!")
            message_box = qtw.QMessageBox(self.root)
            message_box.setWindowIcon(self.root.windowIcon())
            message_box.setStyleSheet(self.root.styleSheet())
            utils.apply_dark_title_bar(message_box)
            message_box.setWindowTitle("No Java installed!")
            message_box.setText(
                "Java could not be found on PATH.\nMake sure that Java 64-bit is installed and try again!"
            )
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No
                | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(
                qtw.QMessageBox.StandardButton.Yes
            )
            message_box.button(
                qtw.QMessageBox.StandardButton.Yes
            ).setText("Open Java Website")
            message_box.button(
                qtw.QMessageBox.StandardButton.No
            ).setText("Exit")
            choice = message_box.exec()

            # Handle the user's choice
            if choice == qtw.QMessageBox.StandardButton.Yes:
                # Open nexus mods file page
                os.startfile(
                    "https://www.java.com/en/download/"
                )

            self.root.close()
            sys.exit()

        self.log.info("Java found.")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        self.log.critical(
            "An uncaught exception occured:",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def handle_stdout(self, text):
        self.protocol_widget.insertPlainText(text)
        self.protocol_widget.moveCursor(qtg.QTextCursor.MoveOperation.End)

    def run_creator(self):
        try:
            self.patch_creator = patch_creator.PatchCreator(
                self,
                Path(self.patched_path_entry.text()).resolve(),
                Path(self.original_path_entry.text()).resolve()
            )
            self.creator_thread = utils.Thread(
                self.patch_creator.create_patch,
                "CreatorThread",
                self
            )
        except errors.InvalidPatchError as ex:
            self.log.error(f"Selected patch is invalid: {ex}")
            return

        self.create_button.setText("Cancel")
        self.create_button.clicked.disconnect(self.run_creator)
        self.create_button.clicked.connect(self.cancel_creator)

        self.start_time = time.time()

        self.creator_thread.start()

    def done(self):
        self.create_button.setText("Create Patch!")
        self.create_button.clicked.disconnect(self.cancel_creator)
        self.create_button.clicked.connect(self.run_creator)

        self.log.info(f"Created patch in {(time.time() - self.start_time):.3f} second(s).")

        message_box = qtw.QMessageBox(self.root)
        message_box.setWindowIcon(self.root.windowIcon())
        message_box.setStyleSheet(self.root.styleSheet())
        utils.apply_dark_title_bar(message_box)
        message_box.setWindowTitle(f"Created pach in {(time.time() - self.start_time):.3f} second(s)")
        message_box.setText(
            "Patch successfully created"
        )
        message_box.setStandardButtons(
            qtw.QMessageBox.StandardButton.No
            | qtw.QMessageBox.StandardButton.Yes
        )
        message_box.setDefaultButton(
            qtw.QMessageBox.StandardButton.Yes
        )
        message_box.button(
            qtw.QMessageBox.StandardButton.Yes
        ).setText("Close DICK")
        message_box.button(
            qtw.QMessageBox.StandardButton.No
        ).setText("Ok")
        choice = message_box.exec()

        # Handle the user's choice
        if choice == qtw.QMessageBox.StandardButton.Yes:
            # Close DICK
            self.exit()

    def cancel_creator(self):
        self.creator_thread.terminate()

        if self.patch_creator.ffdec_interface is not None:
            if self.patch_creator.ffdec_interface.pid is not None:
                utils.kill_child_process(self.patch_creator.ffdec_interface.pid)
                self.log.info(f"Killed FFDec with pid {self.patch_creator.ffdec_interface.pid}.")
                self.patch_creator.ffdec_interface.pid = None

        if self.patch_creator.tmpdir is not None:
            if self.patch_creator.tmpdir.is_dir():
                shutil.rmtree(self.patch_creator.tmpdir)
                self.log.info("Cleaned up temporary folder.")

        self.done()
        self.log.warning("Patch creation incomplete!")


if __name__ == "__main__":
    import patch_creator

    app = MainApp()
    app.exec()
