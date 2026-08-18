#!/usr/bin/env bash
set -u

# ============================================================
# ANGEL BACKUP ENGINE - LINUX
# Native Bash/Linux backup engine.
# Produces the shared Angel Backup Contract.
# ============================================================

set -o pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ANGEL_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ENGINE_VERSION="1.0.0"

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
cyan() { printf '\033[36m%s\033[0m\n' "$*"; }

fail() {
    echo
    red "============================================================"
    red "                    $1"
    red "============================================================"
    echo
    yellow "$2"
    exit 1
}

is_unsafe_destination() {
    local p="$1"
    local real_source
    real_source="$(realpath -m -- "$ANGEL_ROOT")" || return 0
    local real_dest
    real_dest="$(realpath -m -- "$p")" || return 0

    [[ "$real_dest" == "$real_source" ]] && return 0
    [[ "$real_dest" == "$real_source/"* ]] && return 0

    case "$real_dest" in
        "/"|"/home"|"/etc"|"/usr"|"/var"|"/boot"|"/dev"|"/proc"|"/sys"|"/run"|"/bin"|"/sbin"|"/lib"|"/lib64"|"/root")
            return 0 ;;
    esac
    return 1
}

select_folder() {
    if command -v zenity >/dev/null 2>&1; then
        zenity --file-selection --directory --title="Choose an existing folder for Angel backups" 2>/dev/null
        return $?
    fi
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --getexistingdirectory "$HOME" --title "Choose an existing folder for Angel backups" 2>/dev/null
        return $?
    fi
    return 2
}

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
echo "     Uses the Linux folder picker when available"
echo
echo "  4. Enter a path manually"
echo "     Example: /mnt/backup/Angel_Backups"
echo
echo "  0. Cancel"
echo

read -r -p "Enter a number: " choice

case "$choice" in
    1) destination="$HOME/Angel_Backup_Test" ;;
    2) destination="$HOME/Angel_Backups" ;;
    3)
        if ! destination="$(select_folder)"; then
            rc=$?
            if [[ "$rc" -eq 2 ]]; then
                fail "BACKUP NOT PERFORMED" "No Linux folder picker is installed.\n\nUse option 4 to enter an existing Linux path manually."
            fi
            fail "BACKUP CANCELLED" "No folder was selected."
        fi
        ;;
    4)
        echo
        echo "Use a full Linux path such as:"
        echo "  /home/$USER/Angel_Backups"
        echo "  /mnt/backup/Angel_Backups"
        echo "  /media/$USER/USB/Angel_Backups"
        echo
        read -r -p "Backup folder path: " destination
        ;;
    0) exit 0 ;;
    *) fail "BACKUP NOT PERFORMED" "Invalid menu choice. Choose 1, 2, 3, 4, or 0." ;;
esac

destination="${destination#"${destination%%[![:space:]]*}"}"
destination="${destination%"${destination##*[![:space:]]}"}"

[[ -z "$destination" ]] && fail "BACKUP CANCELLED" "No destination was selected."

if [[ "$destination" != /* ]]; then
    fail "BACKUP NOT PERFORMED - USE PROPER ADDRESS" \
"Linux requires an explicit absolute path.

Example:
  /home/$USER/Angel_Backups

No directory was created."
fi

if is_unsafe_destination "$destination"; then
    fail "BACKUP BLOCKED" \
"The selected location is a protected Linux system location or is inside the live Angel project.

No backup was started."
fi

if [[ -e "$destination" && ! -d "$destination" ]]; then
    fail "BACKUP BLOCKED" "The selected destination exists but is not a directory."
fi

if [[ ! -d "$destination" ]]; then
    echo
    yellow "The selected folder does not exist."
    read -r -p "Create this exact folder? (Y/N): " create
    [[ "$create" =~ ^[Yy]$ ]] || fail "BACKUP CANCELLED" "No directory was created."
    mkdir -p -- "$destination" || fail "BACKUP NOT PERFORMED" "Could not create the selected directory."
fi

destination="$(realpath -- "$destination")"

echo
cyan "BACKUP DESTINATION CONFIRMATION"
echo "------------------------------------------------------------"
echo "Source:"
echo "  $ANGEL_ROOT"
echo "Destination:"
echo "  $destination"
echo "------------------------------------------------------------"
read -r -p "Proceed with this backup? (Y/N): " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || fail "BACKUP CANCELLED" "The backup was not started."

free_kb="$(df -Pk -- "$destination" | awk 'NR==2 {print $4}')"
[[ "$free_kb" =~ ^[0-9]+$ ]] || fail "BACKUP BLOCKED" "Could not determine free destination space."
if (( free_kb < 1048576 )); then
    fail "BACKUP BLOCKED" "Less than 1 GB is available on the destination filesystem."
fi

timestamp="$(date '+%Y-%m-%d_%H%M%S')"
backup_id="Angel_Backup_$timestamp"
backup_path="$destination/$backup_id"

[[ -e "$backup_path" ]] && fail "BACKUP BLOCKED" "The generated backup directory already exists."

mkdir -p -- "$backup_path" || fail "BACKUP NOT PERFORMED" "Could not create the backup directory."

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

# rsync is preferred because it handles Linux permissions and symlinks explicitly.
if command -v rsync >/dev/null 2>&1; then
    rsync -a --no-links \
        --exclude='.git/' \
        --exclude='models/' \
        --exclude='cache/' \
        --exclude='backups/' \
        -- "$ANGEL_ROOT/" "$backup_path/"
    result=$?
else
    # Safe fallback: cp without following symbolic links.
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
