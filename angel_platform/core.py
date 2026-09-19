from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, logging, platform, shutil, subprocess, sys
from .execution import SafeExecutor, ExecutionPolicy

ROOT = Path(__file__).resolve().parent.parent
# Keep user data outside the installed/build directory so new EXEs retain history.
DATA = Path.home() / 'Angel_Platform'; DATA.mkdir(parents=True, exist_ok=True)
LOG_PATH = DATA / 'angel-platform.log'
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

@dataclass(frozen=True)
class Module:
    name: str
    description: str
    category: str
    action: str
    requires_confirmation: bool = True
    available: bool = True

class Kernel:
    def __init__(self):
        self.platform = platform.system()
        self.executor = SafeExecutor(DATA / 'workspaces', ExecutionPolicy())
        self.modules = [
            Module('System Health Check', 'Read-only operating system and runtime diagnostics.', 'Utilities', 'system_health', False),
            Module('Tool Inventory', 'Check local development and AI dependencies.', 'Utilities', 'tool_inventory', False),
            Module('Module Library Scan', 'List registered Angel modules.', 'Modules', 'module_scan', False),
            Module('Project ZIP Builder', 'Create a distributable ZIP from a selected workspace.', 'Development', 'build_zip', True),
            Module('Windows EXE Builder', 'Build a Windows executable using the included PyInstaller script.', 'Development', 'build_exe', True, self.platform == 'Windows'),
            Module('Safe Script Runner', 'Run an approved Python or PowerShell script inside an isolated workspace.', 'Development', 'safe_script', True),
            Module('Windows Hardening Toolkit', 'Security configuration workflow requiring explicit approval.', 'Security', 'hardening', True, self.platform == 'Windows'),
            Module('Internet Connectivity Control', 'Connectivity control workflow requiring explicit approval.', 'Security', 'internet_control', True),
        ]

    def find_modules(self, phrase: str):
        words = {w for w in phrase.lower().split() if len(w) > 2}
        scored = []
        for module in self.modules:
            hay = (module.name + ' ' + module.description + ' ' + module.category).lower()
            score = sum(1 for word in words if word in hay)
            if score:
                scored.append((score, module))
        return [m for _, m in sorted(scored, key=lambda item: item[0], reverse=True)]

    def execute(self, action: str):
        logging.info('Executing action=%s', action)
        if action == 'system_health':
            return '\n'.join([
                f'Platform: {platform.platform()}',
                f'Operating system: {platform.system()} {platform.release()}',
                f'Architecture: {platform.machine()}',
                f'Python: {sys.version.split()[0]}',
                f'Executable: {sys.executable}',
                f'Working directory: {ROOT}',
            ])
        if action == 'tool_inventory':
            names = ['python', 'git', 'ollama', 'docker', 'powershell', 'pwsh', 'pyinstaller']
            return '\n'.join(f'{name}: {shutil.which(name) or "MISSING"}' for name in names)
        if action == 'module_scan':
            return '\n'.join(f'• {m.name} — {m.category} — {"available" if m.available else "Windows only"}' for m in self.modules)
        if action == 'hardening':
            return 'Hardening preview complete. No system changes were made. A future execution adapter must apply approved changes.'
        if action == 'internet_control':
            return 'Connectivity preview complete. No network adapters were changed.'
        if action == 'safe_script':
            return 'Safe Script Runner is available through the isolated execution API. A script must be placed in an Angel workspace and explicitly approved.'
        if action == 'build_exe':
            return 'Use Build Center → Windows EXE Builder. The builder requires Windows and Python.'
        if action == 'build_zip':
            return 'Use Build Center → Create ZIP Package.'
        return 'Unknown action.'

    def snapshot(self):
        return [asdict(m) for m in self.modules]
