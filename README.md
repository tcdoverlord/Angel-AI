# Angel Platform

> **"Peace Be The Journey" — Callan Palmer**

**Angel Platform** is a local-first AI assistant and system-management foundation built by **TCDOVERLORD**. It combines conversational AI, local intelligence, project and module tooling, controlled system workflows, persistent local data, and a browser-based interface.

The project is intended to be useful to individuals, students, researchers, hobbyists, developers, and organizations that want to explore or build on a locally controlled AI platform.

> **Current release:** Angel Platform 3.3.3  
> **Repository:** https://github.com/tcdoverlord/Angel-AI

---

## Project Goals

Angel Platform is designed around these principles:

- **Local-first operation** with local files and optional local AI inference.
- **Human approval before sensitive actions.**
- **Clear separation between conversation, planning, and execution.**
- **Auditable workflows** where practical.
- **Modular architecture** that can grow over time.
- **Accessible development** for learners, contributors, and independent builders.
- **Responsible collaboration** with individuals, organizations, and businesses.

Angel Platform is an evolving project. Some capabilities are implemented, some are limited, and others remain planned. Always verify the actual behavior of the version you are running.

---

## Main Components

### Angel AI

The conversational and intelligence layer supports:

- General conversation and explanations.
- Technical assistance and troubleshooting.
- Planning and creative work.
- Local knowledge and intelligence resources.
- Local memory and conversation-related storage.
- Optional integration with local AI providers such as Ollama.

### Angel Nexus

The management and integration layer is intended to provide:

- System and environment information.
- Tool and module discovery.
- Project-related workflows.
- Controlled script and module execution.
- Approval checks for potentially sensitive actions.
- Future integrations with additional system tools and services.

### Angel Platform OS

Angel Platform OS is the longer-term platform vision for connecting Angel AI and Angel Nexus with a personalized, modular computing environment.

This is a continuing development direction and should not be interpreted as a fully completed operating system or unrestricted system-control layer.

---

## Current Capabilities

The 3.3.x development line includes foundations for:

- Browser-based local interface.
- Optional desktop window through `pywebview`.
- Local HTTP server.
- Local project and module management.
- Controlled action definitions with confirmation requirements.
- Knowledge and case-study resources.
- Local SQLite intelligence storage.
- Compatibility JSON history and recovery data.
- Local logging and audit-oriented structures.
- Provider-backed weather functionality in the relevant development checkpoint.
- Windows executable packaging through PyInstaller.

Capabilities can vary by platform and configuration. Features that interact with the operating system should be reviewed and tested before use.

---

## System Requirements

### Windows

Recommended:

- Windows 10 or Windows 11, 64-bit.
- Python 3.10 or newer.
- PowerShell.
- Internet access for installing Python packages and optional services.
- Ollama, if local AI inference is enabled.

### Linux

Basic source execution may be possible on Linux, but platform-specific behavior and system integrations must be tested on the target distribution.

Windows executable packaging is not intended to be used as the Linux launch method.

---

## Installation from Source

### Windows

Open PowerShell in the repository directory:

```powershell
Set-Location "C:\Path\To\Angel-AI"
```

Create a virtual environment:

```powershell
py -3 -m venv .venv
```

If the Python launcher is unavailable:

```powershell
python -m venv .venv
```

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run a source validation check:

```powershell
.\.venv\Scripts\python.exe -m compileall -q angel_platform run_angel_platform.py
```

Start Angel Platform:

```powershell
.\.venv\Scripts\python.exe -u .\run_angel_platform.py
```

The local interface normally uses:

```text
http://127.0.0.1:8765/
```

Keep the PowerShell window open while running from source so that startup errors and logs can be reviewed.

### Linux

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Validate the source:

```bash
python -m compileall -q angel_platform run_angel_platform.py
```

Start the application:

```bash
python -u ./run_angel_platform.py
```

---

## Optional Ollama Setup

Angel Platform can use local AI through Ollama when the relevant integration is enabled and configured.

Install Ollama from its official website:

```text
https://ollama.com/
```

Verify the installation:

```powershell
ollama --version
ollama list
```

If your configuration uses the example model from the development checkpoint:

```powershell
ollama pull llama3.2:3b
```

Test Ollama independently before troubleshooting Angel Platform:

```powershell
ollama run llama3.2:3b
```

Model names and integration behavior may change. Confirm the model configured by the application matches the model installed on your system.

---

## Windows Executable Build

The repository may include a Windows build script and PyInstaller specification.

Before building:

1. Verify that source mode starts successfully.
2. Back up any working `build` or `dist` directories.
3. Review the build script before running it.
4. Confirm that you trust every script being executed.

Build command:

```powershell
.\build_windows_exe.bat
```

The packaged application is expected to be an **onedir** build when generated through the documented packaging process. Keep the complete output directory together rather than copying only the executable.

Typical output:

```text
dist\AngelPlatform\AngelPlatform.exe
```

Build scripts may remove and recreate `build` and `dist`. Do not run them without backing up any package you need to preserve.

---

## Safety and Permission Model

Angel Platform is designed to keep users in control.

System-related actions should follow these principles:

- Explain the proposed action before execution.
- Request clear permission for sensitive or system-changing operations.
- Avoid unrestricted administrator access.
- Separate read-only inspection from modification.
- Make command output and errors visible.
- Distinguish between a proposed action and a completed action.
- Encourage backups before changes to important files or configurations.
- Never assume that AI-generated commands are safe or correct.

**Do not run unfamiliar scripts with administrator privileges unless you have reviewed and understood them.**

---

## Local Data and Privacy

Angel Platform may create local application data under:

```text
~/Angel_Platform
```

Depending on the installed version and enabled features, local data may include:

- Logs.
- SQLite intelligence data.
- Conversation or history compatibility files.
- Approved memories.
- Feedback records.
- Tool audit records.
- Recovery information.

Review the source and configuration before using Angel Platform with sensitive information. Protect local files, backups, credentials, tokens, and encryption material.

Do not commit private runtime data to GitHub.

---

## Development Workflow

Recommended workflow:

1. Inspect the existing implementation.
2. Explain the intended change.
3. Back up important files.
4. Make one controlled change.
5. Run syntax and validation checks.
6. Test the actual interface.
7. Review logs and errors.
8. Document the result.
9. Submit a focused contribution or pull request.

Useful checks:

```powershell
python -m py_compile .\angel_platform\webui\server.py
python -m compileall -q angel_platform run_angel_platform.py
git status
git diff --stat
git diff --cached --name-status
```

---

## Contributing

Contributions are welcome when they are respectful, useful, and aligned with the project's safety goals.

You can contribute through:

- Bug reports.
- Documentation improvements.
- Installation instructions.
- Testing on additional systems.
- Accessibility and interface improvements.
- Security reviews.
- Performance improvements.
- Unit tests.
- New modules and integrations.
- Knowledge resources.
- Error reports with reproducible steps.

### Suggested Contribution Process

1. Open an issue describing the proposed change.
2. Explain the problem, expected behavior, and possible risks.
3. Fork the repository or create a working branch.
4. Make focused changes.
5. Test your work.
6. Document important behavior or limitations.
7. Submit a pull request.
8. Respond to review feedback in good faith.

Please do not include secrets, private data, malware, destructive functionality, or unreviewed system-control behavior in contributions.

Contributions do not automatically guarantee inclusion in an official release.

---

## Business and Commercial Use

Angel Platform is intended to be accessible for personal, educational, research, and non-commercial use under the included license.

**Business and commercial use requires written permission or a separate commercial license from the copyright holder unless the project license is formally changed.**

Organizations and businesses are encouraged to:

- Contact the project before commercial deployment.
- Explain the intended use and distribution model.
- Discuss security, support, branding, and integration needs.
- Contribute improvements, testing, documentation, funding, infrastructure, or other support when they are able.
- Respect the project's safety and attribution requirements.

Permission is not automatically granted by downloading, modifying, or contributing to the repository. See `LICENSE.md` for the current legal terms.

> Important: The included Angel AI Build license is **source-available and non-commercial**, not an OSI-approved open-source license. If the project is later intended to use a formal open-source license, the licensing terms must be changed deliberately and consistently across the repository.

---

## Licensing

The repository currently includes:

```text
LICENSE.md
```

The included license reserves commercial rights to the copyright holder and permits specified personal, educational, research, evaluation, and other non-commercial uses.

Third-party dependencies, models, APIs, assets, and services may have separate licenses and terms. Review and comply with those terms.

---

## Project Structure

The exact structure may change, but major areas include:

```text
Angel-AI/
├── angel_platform/
│   ├── capabilities/
│   ├── intelligence/
│   ├── knowledge/
│   ├── storage/
│   └── webui/
├── assets/
├── scripts/
├── tests/
├── AngelPlatform.spec
├── requirements.txt
├── run_angel_platform.py
├── build_windows_exe.bat
├── RUN_WINDOWS.bat
├── RUN_REPAIR_MODE.bat
├── LICENSE.md
└── README.md
```

Always inspect the current repository before assuming a file or directory exists.

---

## Known Limitations

- Platform support varies between Windows and Linux.
- Some system-management features are controlled, preview-based, or still under development.
- AI-generated output can be inaccurate or incomplete.
- Local AI model compatibility depends on the configured provider and model.
- External services such as weather providers can become unavailable.
- Packaging behavior can change as the project evolves.
- Security and administrative workflows require continued testing and review.
- The project should not be treated as production-ready for every environment without independent validation.

---

## Roadmap Direction

Possible future work includes:

- Stronger automated tests.
- Improved Linux support.
- Better module discovery and installation workflows.
- More detailed permission and audit controls.
- Safer execution limits and sandboxing.
- Improved memory management and user controls.
- Additional local AI providers.
- Better error reporting and recovery.
- More accessible documentation.
- Community contribution guidelines.
- Business collaboration and commercial licensing options.
- More complete Angel Platform OS integration.

Roadmap items are goals, not guarantees or commitments to a specific release date.

---

## Community Values

Angel Platform is built around:

- Human control.
- Transparency.
- Privacy-conscious local operation.
- Responsible experimentation.
- Open communication.
- Respect for contributors.
- Practical documentation.
- Safety before automation.
- Shared improvement when people and organizations have the ability to contribute.

---

## Disclaimer

Angel Platform is provided for experimentation, development, research, and other permitted uses. Review the code, test changes, protect your data, maintain backups, and verify commands before execution.

The project may interact with local files, operating-system tools, AI models, network services, and administrative workflows. You are responsible for determining whether it is appropriate for your environment.

---

## Contact and Repository

- **GitHub:** https://github.com/tcdoverlord/Angel-AI
- **Project:** Angel Platform / Angel AI / Angel Nexus
- **Maintainer:** TCDOVERLORD

**Peace Be The Journey.**
