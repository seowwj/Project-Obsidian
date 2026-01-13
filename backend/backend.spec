# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata
import sys
import os
import certifi

block_cipher = None

# -----------------------------------------------------------------------------
# HIDDEN IMPORTS
# -----------------------------------------------------------------------------
# Libraries that do dynamic imports must be explicitly listed here.
hidden_imports = [
    # OpenVINO
    'openvino',
    'openvino.runtime',
    'openvino.runtime.utils',
    'openvino.runtime.ie_api',
    'openvino.extensions',
    'openvino_genai',
    'openvino_tokenizers',

    # Uvicorn & server components
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    
    # ChromaDB & Database
    'chromadb',
    'chromadb.telemetry.product.posthog', 
    'chromadb.db.impl.sqlite',
    'sqlite3',
    
    # AI & Tokenization
    'tiktoken_ext', 
    'tiktoken_ext.openai_public',
    'sentence_transformers',
    
    # Networking
    'engineio.async_drivers.aiohttp',
]

# -----------------------------------------------------------------------------
# DATA FILES
# -----------------------------------------------------------------------------
# Non-code files needed at runtime.
# Non-code files needed at runtime.
datas = []
binaries = []

# --- OpenVINO Binaries ---
import site
site_packages = site.getsitepackages()[1] # Usually the venv/Lib/site-packages
# Adjust index [1] if needed, or use a robust finder:
for p in site.getsitepackages():
    if "site-packages" in p:
        site_packages = p
        break

# 1. OpenVINO Libs (Core DLLs)
ov_libs = os.path.join(site_packages, "openvino", "libs")
if os.path.exists(ov_libs):
    # Tuple format: (Source, Dest_in_dist)
    # We put them in openvino/libs so python imports can find them relative to package
    datas.append((ov_libs, "openvino/libs"))

# 2. OpenVINO GenAI (DLLs)
ov_genai = os.path.join(site_packages, "openvino_genai")
if os.path.exists(ov_genai):
    datas.append((ov_genai, "openvino_genai"))

# 3. OpenVINO Tokenizers (DLLs)
ov_tok = os.path.join(site_packages, "openvino_tokenizers")
if os.path.exists(ov_tok):
    datas.append((ov_tok, "openvino_tokenizers"))

# 1. SSL Certificates (Critical for requests/huggingface)
datas.append((certifi.where(), 'certifi'))

# 2. Package Metadata (Version checks often fail without this)
packages_needing_metadata = [
    'chromadb',
    'tqdm',
    'regex',
    'requests',
    'packaging',
    'filelock',
    'numpy',
    'tokenizers',
    'huggingface_hub',
    'safetensors',
    'accelerate',
    'sentence_transformers'
]

for package in packages_needing_metadata:
    try:
        datas += copy_metadata(package)
    except Exception as e:
        print(f"Warning: Could not copy metadata for {package}: {e}")

# -----------------------------------------------------------------------------
# Collect all Transformers dependencies (Critical for AutoTokenizer)
# -----------------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_all

# Collect everything for transformers to handle dynamic loading of models/tokenizers
tmp_ret = collect_all('transformers')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hidden_imports += tmp_ret[2]

# Collect all ChromaDB dependencies (Including Rust bindings)
tmp_ret = collect_all('chromadb')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hidden_imports += tmp_ret[2]

# -----------------------------------------------------------------------------
# ANALYSIS
# -----------------------------------------------------------------------------
a = Analysis(
    ['entry_point.py'],
    pathex=['gen'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_transformers.py'],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# -----------------------------------------------------------------------------
# EXE (Single File)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# EXE (Single File)
# -----------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend',
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
)

# -----------------------------------------------------------------------------
# COLLECT (Directory Mode - DISABLED for Single File Sidecar)
# -----------------------------------------------------------------------------
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='backend',
# )
