# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for creating standalone Aether executables.

Usage:
  pyinstaller aether.spec

This will create:
  - dist/aether_planner.exe - Standalone planner executable
  - dist/aether_wake.exe - Standalone wake listener executable
  - dist/aether_tray.exe - Standalone system tray executable
"""

block_cipher = None

a = Analysis(
    ['src/assistant/core/listener.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assistant', 'assistant'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'assistant.core',
        'assistant.skills',
        'assistant.memory',
        'assistant.audit',
        'assistant.learning',
        'vosk',
        'sounddevice',
        'faster_whisper',
        'pyttsx3',
        'pyautogui',
        'pygetwindow',
        'pyperclip',
        'keyboard',
        'structlog',
        'pydantic',
        'fastapi',
        'uvicorn',
        'websockets',
        'psutil',
        'pystray',
        'PIL',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_planner = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='aether_planner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# Wake listener executable
b = Analysis(
    ['src/assistant/core/wake.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assistant', 'assistant'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'assistant.core',
        'assistant.skills',
        'vosk',
        'sounddevice',
        'numpy',
        'structlog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'scipy',
        'fastapi',
        'uvicorn',
        'websockets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_b = PYZ(b.pure, b.zipped_data, cipher=block_cipher)

exe_wake = EXE(
    pyz_b,
    b.scripts,
    b.binaries,
    b.zipfiles,
    b.datas,
    [],
    name='aether_wake',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# System tray executable
c = Analysis(
    ['src/assistant/core/tray_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assistant', 'assistant'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'assistant.core',
        'pystray',
        'PIL',
        'numpy',
        'structlog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'scipy',
        'faster_whisper',
        'vosk',
        'sounddevice',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_c = PYZ(c.pure, c.zipped_data, cipher=block_cipher)

exe_tray = EXE(
    pyz_c,
    c.scripts,
    c.binaries,
    c.zipfiles,
    c.datas,
    [],
    name='aether_tray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console for tray app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
