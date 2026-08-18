#!/usr/bin/env bash
set -u
set -o pipefail

# ============================================================
# ANGEL BACKUP ENGINE - LINUX
# Native Bash/Linux backup engine
# User-friendly, safety-first, shared Angel Backup Contract
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ANGEL_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ENGINE_VERSION="1.1.0"

red(){ printf '\033[31m%s\033[0m\n' "$*"; }
green(){ printf '\033[32m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[33m%s\033[0m\n' "$*"; }
cyan(){ printf '\033[36m%s\033[0m\n' "$*"; }

fail(){
    echo
    red "============================================================"
    red "                    $1"
    red "============================================================"
    echo
    yellow "$2"
    echo
    exit 1
}

pause_error(){
    echo
    read -r -p "Press ENTER to return to the menu..." _
}

command_exists(){ command -v "$1" >/dev/null 2>&1; }

detect_package_manager(){
    if command_exists apt-get; then echo "apt"; return; fi
    if command_exists dnf; then echo "dnf"; return; fi
    if command_exists pacman; then echo "pacman"; return; fi
    if command_exists zypper; then echo "zypper"; return; fi
    echo "none"
}

run_privileged(){
    if [[ $EUID -eq 0 ]]; then
        "$@"
    elif command_exists sudo; then
        sudo "$@"
    else
        return 127
    fi
}

install_zenity(){
    local pm
    pm="$(detect_package_manager)"

    echo
    cyan "FOLDER PICKER SETUP"
    echo "------------------------------------------------------------"
    echo "Angel needs a small standard Linux utility called Zenity"
    echo "to provide a graphical folder-selection window."
    echo
    echo "Angel detected package manager: $pm"
    echo
    echo "Angel will NOT install anything without your approval."
    read -r -p "Install Zenity now? (Y/N): " answer
    [[ "$answer" =~ ^[Yy]$ ]] || return 1

    case "$pm" in
        apt)
            echo
            cyan "Installing Zenity using APT..."
            run_privileged apt-get update || return 1
            run_privileged apt-get install -y zenity || return 1
            ;;
        dnf)
            echo
            cyan "Installing Zenity using DNF..."
            run_privileged dnf install -y zenity || return 1
            ;;
        pacman)
            echo
            cyan "Installing Zenity using Pacman..."
            run_privileged pacman -Sy --noconfirm zenity || return 1
            ;;
        zypper)
            echo
            cyan "Installing Zenity using Zypper..."
            run_privileged zypper --non-interactive install zenity || return 1
            ;;
        *)
            return 2
            ;;
    esac

    command_exists zenity
}

select_folder(){
    if command_exists zenity; then
        zenity --file-selection --directory \
            --title="Choose an existing folder for Angel backups" \
            2>/dev/null
        return $?
    fi

    if command_exists kdialog; then
        kdialog --getexistingdirectory "$HOME" \
            --title "Choose an existing folder for Angel backups" \
            2>/dev/null
        return $?
    fi

    echo
    red "============================================================"
    red "              LINUX FOLDER PICKER NOT INSTALLED"
    red "============================================================"
    echo
    echo "Angel can install Zenity so option 3 can open a"
    echo "normal graphical folder-selection window."
    echo
    echo "This is optional. You can always use option 4"
    echo "to enter a Linux path manually."
    echo

    read -r -p "Would you like Angel to install the folder picker? (Y/N): " answer

    if [[ "$answer" =~ ^[Yy]$ ]]; then
        if install_zenity; then
            echo
            green "FOLDER PICKER READY"
            echo "Opening the folder selector..."
            sleep 1
            zenity --file-selection --directory \
                --title="Choose an existing folder for Angel backups" \
                2>/dev/null
            return $?
        fi

        echo
        red "Angel could not install the folder picker."
        echo "Use option 4 to enter a Linux path manually."
        return 1
    fi

    echo
    yellow "Folder picker installation skipped."
    echo "Use option 4 to enter a Linux path manually."
    return 1
}

is_unsafe_destination(){
    local p="$1"
    local source dest
    source="$(realpath -m -- "$ANGEL_ROOT")" || return 0
    dest="$(realpath -m -- "$p")" || return 0

    [[ "$dest" == "$source" ]] && return 0
    [[ "$dest" == "$source/"* ]] && return 0

    case "$dest" in
        "/"|"/home"|"/etc"|"/usr"|"/var"|"/boot"|"/dev"|"/proc"|"/sys"|"/run"|"/bin"|"/sbin"|"/lib"|"/lib64"|"/root"|"/opt")
            return 0 ;;
    esac
    return 1
}

is_absolute_path(){
    [[ "$1" == /* ]]
}

normalize_input(){
    local v="$1"
    v="${v#"${v%%[![:space:]]*}"}"
    v="${v%"${v##*[![:space:]]}"}"
    printf '%s' "$v"
}

choose_destination(){
    while true; do
        echo
        echo "============================================================"
        cyan "                    ANGEL BACKUP ENGINE"
        echo "============================================================"
        echo
        echo "Choose where to create your Angel backup:"
        echo
        echo "  1. Backup Test"
        echo "     $HOME/Angel_Backup_Test"
        echo
        echo "  2. Permanent Backups"
        echo "     $HOME/Angel_Backups"
        echo
        echo "  3. Browse for a folder"
        echo "     Opens a Linux folder picker"
        echo
        echo "  4. Enter a path manually"
        echo "     Example: /mnt/backup/Angel_Backups"
        echo
        echo "  0. Cancel"
        echo
        read -r -p "Enter a number: " choice

        case "$choice" in
            1)
                destination="$HOME/Angel_Backup_Test"
                return 0
                ;;
            2)
                destination="$HOME/Angel_Backups"
                return 0
                ;;
            3)
                destination="$(select_folder)" || destination=""
                if [[ -n "$destination" ]]; then return 0; fi
                echo
                yellow "No folder selected."
                echo "Returning to the backup menu..."
                sleep 1
                ;;
            4)
                echo
                cyan "CUSTOM BACKUP LOCATION"
                echo "------------------------------------------------------------"
                echo
                echo "Enter a FULL Linux folder path."
                echo
                echo "Examples:"
                echo "  /home/$USER/Angel_Backups"
                echo "  /mnt/backup/Angel_Backups"
                echo "  /media/$USER/USB/Angel_Backups"
                echo
                echo "Do NOT use:"
                echo "  home/backups"
                echo "  ./backups"
                echo "  ~/backups"
                echo
                echo "Type 0 to cancel."
                echo
                read -r -p "Backup folder path: " destination
                destination="$(normalize_input "$destination")"
                [[ "$destination" == "0" ]] && return 1
                return 0
                ;;
            0)
                return 1
                ;;
            *)
                red "INVALID CHOICE"
                echo "Choose 1, 2, 3, 4, or 0."
                sleep 1
                ;;
        esac
    done
}

# Main
choose_destination || exit 0

destination="$(normalize_input "$destination")"
[[ -z "$destination" ]] && fail "BACKUP CANCELLED" "No destination was selected."

if ! is_absolute_path "$destination"; then
    fail "BACKUP NOT PERFORMED - USE PROPER ADDRESS" \
"Linux requires a full absolute folder address.

Correct examples:
  /home/$USER/Angel_Backups
  /mnt/backup/Angel_Backups
  /media/$USER/USB/Angel_Backups

Do not use:
  home/backups
  ./backups
  ~/backups

No directory was created."
fi

if is_unsafe_destination "$destination"; then
    fail "BACKUP BLOCKED" \
"The selected location is a protected Linux system location
or is inside the live Angel project.

Angel stopped before creating or copying anything."
fi

if [[ -e "$destination" && ! -d "$destination" ]]; then
    fail "BACKUP BLOCKED" \
"The selected destination already exists but is not a directory."
fi

if [[ ! -d "$destination" ]]; then
    echo
    yellow "LOCATION NOT FOUND"
    echo
    echo "Angel could not find:"
    echo "  $destination"
    echo
    echo "Angel can create this EXACT folder, but only after you approve it."
    read -r -p "Create this exact folder? (Y/N): " create
    [[ "$create" =~ ^[Yy]$ ]] ||
        fail "BACKUP CANCELLED" "No directory was created."
    mkdir -p -- "$destination" ||
        fail "BACKUP NOT PERFORMED" "Could not create the selected directory."
fi

destination="$(realpath -- "$destination")"

# Prevent a destination that became unsafe after creation/normalization.
is_unsafe_destination "$destination" &&
    fail "BACKUP BLOCKED" "The normalized destination is unsafe."

echo
cyan "BACKUP DESTINATION CONFIRMATION"
echo "------------------------------------------------------------"
echo "Source:"
echo "  $ANGEL_ROOT"
echo "Destination:"
echo "  $destination"
echo "------------------------------------------------------------"
echo
read -r -p "Proceed with this backup? (Y/N): " confirm
[[ "$confirm" =~ ^[Yy]$ ]] ||
    fail "BACKUP CANCELLED" "The backup was not started."

free_kb="$(df -Pk -- "$destination" 2>/dev/null | awk 'NR==2 {print $4}')"
[[ "$free_kb" =~ ^[0-9]+$ ]] ||
    fail "BACKUP BLOCKED" "Could not determine destination free space."

if (( free_kb < 1048576 )); then
    fail "BACKUP BLOCKED" "Less than 1 GB is available on the destination filesystem."
fi

timestamp="$(date '+%Y-%m-%d_%H%M%S')"
backup_id="Angel_Backup_$timestamp"
backup_path="$destination/$backup_id"

[[ -e "$backup_path" ]] &&
    fail "BACKUP BLOCKED" "The generated backup directory already exists."

mkdir -p -- "$backup_path" ||
    fail "BACKUP NOT PERFORMED" "Could not create the backup directory."

started="$(date --iso-8601=seconds)"

cat > "$backup_path/backup-manifest.json" <<EOF
{
  "contract_version": "1.0",
  "backup_id": "$backup_id",
  "platform": "linux",
  "engine": "Backup-Angel.sh",
  "engine_version": "$ENGINE_VERSION",
  "timestamp_start": "$started",
  "source": "$ANGEL_ROOT",
  "destination": "$backup_path",
  "status": "IN_PROGRESS"
}
EOF

echo
cyan "Running backup..."

if command_exists rsync; then
    # -a preserves normal Linux metadata; --no-links prevents following symlinks.
    rsync -a --no-links \
        --exclude='.git/' \
        --exclude='models/' \
        --exclude='cache/' \
        --exclude='backups/' \
        -- "$ANGEL_ROOT/" "$backup_path/"
    result=$?
else
    # Portable fallback. Do not follow symbolic links.
    cp -a --no-dereference \
        --exclude='.git' \
        --exclude='models' \
        --exclude='cache' \
        --exclude='backups' \
        "$ANGEL_ROOT/." "$backup_path/" 2>/dev/null
    result=$?
fi

finished="$(date --iso-8601=seconds)"

if (( result != 0 )); then
    cat > "$backup_path/backup-report.json" <<EOF
{
  "contract_version": "1.0",
  "backup_id": "$backup_id",
  "platform": "linux",
  "engine": "Backup-Angel.sh",
  "engine_version": "$ENGINE_VERSION",
  "timestamp_start": "$started",
  "timestamp_end": "$finished",
  "source": "$ANGEL_ROOT",
  "destination": "$backup_path",
  "status": "FAILED",
  "backup_exit_code": $result
}
EOF
    fail "BACKUP FAILED" "The Linux backup engine returned exit code $result."
fi

cat > "$backup_path/backup-report.json" <<EOF
{
  "contract_version": "1.0",
  "backup_id": "$backup_id",
  "platform": "linux",
  "engine": "Backup-Angel.sh",
  "engine_version": "$ENGINE_VERSION",
  "timestamp_start": "$started",
  "timestamp_end": "$finished",
  "source": "$ANGEL_ROOT",
  "destination": "$backup_path",
  "status": "SUCCESS",
  "backup_exit_code": 0,
  "exclusions": [".git", "models", "cache", "backups"]
}
EOF

[[ -f "$backup_path/backup-manifest.json" && -f "$backup_path/backup-report.json" ]] ||
    fail "BACKUP FAILED" "The required Angel backup control files were not created."

echo
green "============================================================"
green "                    BACKUP COMPLETE"
green "============================================================"
echo
echo "Backup:"
echo "  $backup_path"
echo
echo "Manifest:"
echo "  $backup_path/backup-manifest.json"
echo
echo "Report:"
echo "  $backup_path/backup-report.json"
echo
