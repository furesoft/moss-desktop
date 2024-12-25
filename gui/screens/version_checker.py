import os.path
import subprocess
from typing import TYPE_CHECKING

import pygameextra as pe

from gui.events import ResizeEvent
from gui.pp_helpers.popups import WarningPopup
from gui.screens.mixins import LogoMixin

from gui.gui import APP_NAME

if TYPE_CHECKING:
    from gui.gui import GUI

class GitCheckException(Exception):
    pass


class VersionChecker(pe.ChildContext, LogoMixin):
    LAYER = pe.AFTER_LOOP_LAYER

    def __init__(self, parent: "GUI"):
        self.checked = False
        if os.path.exists('requirements.txt'):
            with open('requirements.txt'):
                self.versions = {
                    package: version
                    for package, version in
                    map(lambda line: str.split(line, '=='), open('requirements.txt').read().splitlines())
                }
        else:
            self.versions = None
        super().__init__(parent)
        self.warnings = []
        self.initialize_logo_and_line()
        self.api.add_hook('version_checker_resize_check', self.resize_check_hook)

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.initialize_logo_and_line()

    def events(self):
        pass

    def check(self):
        self.checked = True
        if self.versions is not None:
            # Ensure PygameExtra is up to date
            if pe.__version__ != self.versions['pygameextra']:
                self.warnings.append(WarningPopup(
                    self.parent_context,
                    "PygameExtra is outdated",
                    f"You are running from source, the main package that {APP_NAME} uses is outdated\n"
                    f"Please update PygameExtra to {self.versions['pygameextra']}\n"
                    "This should resolve any issues you may experience if you ignore this warning!\n\n"
                    "Do not report issues unless you have updated PygameExtra!"
                ))
        if os.path.exists('.git'):
            # Check for new commit
            try:
                branch = subprocess.check_output(
                    ["git", "branch", "--show-current"],
                    stderr=subprocess.DEVNULL
                ).strip().decode("utf-8")

                if not branch:
                    raise GitCheckException("No branch found")

                # Fetch remote changes
                subprocess.run(["git", "fetch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Compare local and remote branch
                status = subprocess.check_output(["git", "status", "-sb"]).strip().decode('utf-8')
                if '[behind' in status:
                    self.warnings.append(WarningPopup(
                        self.parent_context,
                        "New commits available!",
                        "There are new commits available for this branch.\n"
                        "Please pull the changes to stay up to date.\n\n"
                        "Do not report issues unless you have pulled the changes!"
                    ))
                elif '[ahead' in status and not self.config.debug:
                    self.warnings.append(WarningPopup(
                        self.parent_context,
                        "You've created new commits!",
                        "Can't wait for you to share them!\n"
                        "Disable this message by enabling debug.\n\n"
                        "Do not report issues unless you have pushed these changes!"
                    ))
            except (FileNotFoundError, GitCheckException):
                self.warnings.append(WarningPopup(
                    self.parent_context,
                    "Failed to check for updates.",
                    "Failed to check for updates, please check manually for any new commits."
                ))


    def close(self):
        self.api.remove_hook('version_checker_resize_check')
        del self.screens.queue[-1]

    def loop(self):
        self.logo.display()
        if not self.checked:
            self.check()
        if self.warnings:
            self.warnings[0]()
            if self.warnings[0].closed:
                self.warnings.pop(0)
        else:
            self.close()
