#!/usr/bin/env bash
set -u

# ============================================================
# ANGEL BACKUP VERIFIER - LINUX
# Read-only verification of the shared Angel Backup Contract.
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ANGEL_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="$ANGEL_ROOT/bootstrap/reports"
mkdir -p -- "$REPORT_DIR"

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
cyan() { printf '\033[36m%s\033[0m\n' "$*"; }

echo "============================================================"
cyan "                 ANGEL BACKUP VERIFIER"
echo "============================================================"
echo
echo "Choose where your Angel backups are stored:"
echo
echo "  1. Backup Test"
echo "     $HOME/Angel_Backup_Test"
echo
echo "  2. Permanent Backups"
echo "     $HOME/Angel_Backups"
echo
echo "  3. Another existing folder"
echo "     Example: /mnt/backup/Angel_Backups"
echo
echo "  0. Cancel"
echo

read -r -p "Enter a number: " choice

case "$choice" in
    1) root="$HOME/Angel_Backup_Test" ;;
    2) root="$HOME/Angel_Backups" ;;
    3)
        echo
        echo "Enter an EXISTING Linux folder."
        echo "Example: /mnt/backup/Angel_Backups"
        echo
        read -r -p "Existing folder path: " root
        [[ "$root" == /* ]] || {
            red "BACKUP NOT PERFORMED - USE PROPER ADDRESS"
            echo "Use an absolute Linux path such as /home/$USER/Angel_Backups."
            exit 1
        }
        ;;
    0) exit 0 ;;
    *) red "Invalid menu choice."; exit 1 ;;
esac

[[ -d "$root" ]] || {
    red "BACKUP NOT PERFORMED - FOLDER NOT FOUND"
    echo "The verifier will not create the folder."
    exit 1
}

mapfile -t backups < <(find "$root" -mindepth 1 -maxdepth 1 -type d -name 'Angel_Backup_*' -printf '%T@ %p\n' 2>/dev/null | sort -nr | cut -d' ' -f2-)

if (( ${#backups[@]} == 0 )); then
    red "No Angel_Backup_* folders were found in $root"
    exit 1
fi

echo
cyan "AVAILABLE ANGEL BACKUPS"
echo "------------------------------------------------------------"
for i in "${!backups[@]}"; do
    printf "  %d. %s\n" "$((i+1))" "$(basename -- "${backups[$i]}")"
done
echo
echo "  0. Cancel"
echo
read -r -p "Choose backup number: " n
[[ "$n" == "0" ]] && exit 0

[[ "$n" =~ ^[0-9]+$ ]] || { red "Invalid backup selection."; exit 1; }
(( n >= 1 && n <= ${#backups[@]} )) || { red "Invalid backup selection."; exit 1; }

backup="${backups[$((n-1))]}"

echo
echo "Selected backup:"
echo "  $backup"
read -r -p "Verify this backup? (Y/N): " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || exit 0

failed=0
checks=()

check() {
    local name="$1" pass="$2" detail="$3"
    if [[ "$pass" == "1" ]]; then
        green "[PASS] $name"
        echo "       $detail"
        checks+=("{\"check\":\"$name\",\"status\":\"PASS\",\"detail\":\"$detail\"}")
    else
        red "[FAIL] $name"
        echo "       $detail"
        checks+=("{\"check\":\"$name\",\"status\":\"FAIL\",\"detail\":\"$detail\"}")
        failed=1
    fi
}

manifest="$backup/backup-manifest.json"
report="$backup/backup-report.json"

if [[ -f "$manifest" ]] && python3 - "$manifest" <<'PY' >/dev/null 2>&1
import json,sys
json.load(open(sys.argv[1], encoding="utf-8"))
PY
then
    check "Backup manifest" 1 "Manifest exists and is valid JSON."
else
    check "Backup manifest" 0 "Manifest is missing or invalid JSON."
fi

if [[ -f "$report" ]] && python3 - "$report" <<'PY' >/dev/null 2>&1
import json,sys
d=json.load(open(sys.argv[1], encoding="utf-8"))
raise SystemExit(0 if d.get("status")=="SUCCESS" else 1)
PY
then
    check "Backup report" 1 "Report status is SUCCESS."
else
    check "Backup report" 0 "Report is missing, invalid, or not SUCCESS."
fi

for f in ANGEL-BIBLE.md README.md; do
    [[ -f "$backup/$f" ]] && check "File: $f" 1 "Required file exists." || check "File: $f" 0 "Required file is missing."
done

for d in angel bootstrap skills tests; do
    [[ -d "$backup/$d" ]] && check "Directory: $d" 1 "Required directory exists." || check "Directory: $d" 0 "Required directory is missing."
done

nested="$(find "$backup" -mindepth 1 -maxdepth 1 -type d -name 'Angel_Backup_*' -print -quit 2>/dev/null)"
[[ -z "$nested" ]] && check "Nested backup check" 1 "No nested Angel backup found at backup root." || check "Nested backup check" 0 "Nested Angel backup found: $nested"

[[ ! -d "$backup/.git" ]] && check "Git exclusion" 1 ".git was not copied into the backup root." || check "Git exclusion" 0 ".git exists in the backup root."

# Read-only symlink/reparse safety check.
symlink="$(find "$backup" -type l -print -quit 2>/dev/null)"
[[ -z "$symlink" ]] && check "Symlink check" 1 "No symbolic links found in the backup." || check "Symlink check" 0 "Symbolic link found: $symlink"

timestamp="$(date '+%Y-%m-%d_%H%M%S')"
status="PASS"
(( failed != 0 )) && status="FAIL"
report_out="$REPORT_DIR/Angel_Backup_Verification_$timestamp.json"

{
    echo "{"
    printf '  "timestamp": "%s",\n' "$(date --iso-8601=seconds)"
    printf '  "backup": "%s",\n' "$backup"
    printf '  "status": "%s",\n' "$status"
    printf '  "verifier": "Verify-Angel-Backup.sh",\n'
    printf '  "verifier_version": "1.0.0",\n'
    echo '  "checks": ['
    (IFS=,; printf '    %s\n' "${checks[*]}")
    echo '  ]'
    echo "}"
} > "$report_out"

echo
echo "Verification report saved to:"
echo "  $report_out"
echo

if (( failed == 0 )); then
    green "BACKUP VERIFIED"
    exit 0
else
    red "BACKUP VERIFICATION FAILED"
    exit 1
fi
