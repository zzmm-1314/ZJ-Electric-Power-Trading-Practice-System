# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [
    ("frontend_dist", "frontend_dist"),        # 前端静态文件
    ("icon.ico", "."),                          # 图标（运行时也能读）
]

# jieba 词典、zhipuai 元数据、flask 相关
datas += collect_data_files("jieba")
datas += collect_data_files("zhipuai")
datas += collect_data_files("apscheduler")

hiddenimports = []
hiddenimports += collect_submodules("jieba")
hiddenimports += collect_submodules("pymysql")
hiddenimports += collect_submodules("apscheduler")
hiddenimports += collect_submodules("flask")
hiddenimports += collect_submodules("zhipuai")
hiddenimports += collect_submodules("openai")
hiddenimports += collect_submodules("anthropic")
hiddenimports += ["pymysql.cursors", "sqlite3"]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ExamSystem",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                    # ← 不弹控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico",
)