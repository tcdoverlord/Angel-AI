# Angel Linux Backup — Safe Dependency Policy

Angel never installs Linux system packages automatically.

Option 3 uses Zenity or KDialog only if already installed. If neither is
available, Angel explains how the user can install Zenity and leaves option 4
available for manual path entry.

No sudo commands are executed by Angel.

Common commands:

Ubuntu / Debian:
  sudo apt update
  sudo apt install zenity

Fedora:
  sudo dnf install zenity

Arch:
  sudo pacman -S zenity

openSUSE:
  sudo zypper install zenity
