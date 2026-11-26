---
name: "source-command-package-python-onefile"
description: "Migrated source command `package-python-oneFile`"
---

# source-command-package-python-onefile

Use this skill when the user asks to run the migrated source command `package-python-oneFile`.

## Command Template

# Package Python App

Package the current Python project into a standalone `.exe` using PyInstaller.

## Steps

### 1. Discover the project

Read the project directory to find:
- The entry point: look for `main.py`, `app.py`, or `run.py` in the root. If none found, ask the user which file to use.
- The app name: use the current directory name as default, or ask the user.
- `requirements.txt`: read it to know which packages are bundled and spot ones that commonly need `--hidden-import` or `--collect-all`.

### 2. Check PyInstaller is installed

Run:
```
pip show pyinstaller
```
If not installed, run `pip install pyinstaller` before continuing.

### 3. Determine build flags

Build the PyInstaller command with these rules:

**Always include:**
- `--onefile` — single executable
- `--windowed` — no console window (omit this if the app is a CLI tool with terminal output)
- `--name <app-name>` — name of the output exe
- `--distpath packages` — output directory

**Hidden imports — add `--hidden-import <pkg>` for any of these found in requirements.txt:**
- `pynput` → `--hidden-import pynput.keyboard --hidden-import pynput.mouse`
- `faster_whisper` → `--hidden-import faster_whisper`
- `cv2` → `--hidden-import cv2`
- `sklearn` → `--hidden-import sklearn`
- `pyperclip` → `--hidden-import pyperclip`

**Collect-all — add `--collect-all <pkg>` for packages with data files:**
- `faster_whisper` → `--collect-all faster_whisper`
- `ctranslate2` → `--collect-all ctranslate2`
- `transformers` → `--collect-all transformers`
- `gradio` → `--collect-all gradio`

**Icon — if an `.ico` file exists anywhere in the project:**
- Find it with Glob `**/*.ico`
- Add `--icon <path>`

### 4. Create the packages directory

```
New-Item -ItemType Directory -Force packages
```

### 5. Run PyInstaller

Run the assembled command. Stream the output. If it fails:
- Search the error for `ModuleNotFoundError: No module named '<x>'` and add `--hidden-import <x>`, then retry.
- If a `WARNING: Hidden import "<x>" not found` appears, remove that flag and retry.
- If it fails a second time, show the user the last 30 lines of output and stop.

### 6. Verify output

After a successful build:
- Confirm `packages/<app-name>.exe` exists.
- Print its file size in MB.
- Remind the user that first launch will be slow (PyInstaller unpacks to a temp folder on fir
st run).

### 7. Update .gitignore

If a `.gitignore` exists in the project, check whether `packages/`, `build/`, and `*.spec` are already listed. Add any that are missing so build artefacts are not committed.

## Notes

- `--onefile` is always used. If the user asks for a folder-based build instead, use `--onedir` and omit `--onefile`.
- Do not bundle model weight files (`.bin`, `.pt`, `.gguf`, `.onnx`) — they are large and should be downloaded at runtime.
- If the project has a `assets/` or `resources/` folder with non-Python files needed at runtime, add `--add-data "assets;assets"` (Windows path separator is `;`).
