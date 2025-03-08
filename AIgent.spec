# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['streamlit', 'requests', 'fitz', 'docx2txt', 'json', 'time', 'random', 'os'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 基础大型库 - 保留排除这些，因为你之前明确提到不需要
        'matplotlib', 'numpy', 'pandas', 'PIL', 'scipy', 'sklearn',
        'tensorflow', 'torch', 'cv2', 'pygame', 'PyQt5', 'tkinter',
        'wx',
        # Streamlit相关不需要的模块 - 保留排除这些，streamlit内部模块
        'streamlit.web', 'streamlit.proto', 'streamlit.testing',
        'streamlit.runtime.legacy', 'streamlit.runtime.metrics',
        #  以下模块可能是误排除，移除，让 PyInstaller 自动判断是否需要
        'babel',
        'docutils',
        'sphinx', # 文档生成，如果你的app不需要生成文档可以排除，先保留
        'nose',
        'mock',
        'pytest',
        'unittest', # 测试框架，运行时不需要
        'IPython',  # 交互式环境，运行时不需要
        'pydoc',    # 文档生成，运行时不需要
        'distutils', # 打包工具，运行时可能不需要，但有些库可能依赖，先保留
        'setuptools',# 打包工具，运行时可能不需要，但有些库可能依赖，先保留
        'pip',      # 包管理器，运行时不需要
        'pkg_resources', # setuptools 的一部分，运行时有时需要，先保留
        'wheel',    # 打包工具，运行时不需要
        # 其他不需要的模块 - 保留排除这些，比较确定不需要
        'asyncio', # 异步库，如果你代码没用async/await可以排除，先保留
        'concurrent', # 并发库，如果没用线程/进程池可以排除，先保留
        'curses',    # 终端UI库，大概率不需要
        'lib2to3',  # Python2to3转换工具，不需要
        'pydoc_data',# 文档数据，不需要
        'test',     # 测试模块，不需要
        'xmlrpc',   # XML RPC库，大概率不需要
        'ensurepip',# pip引导工具，不需要
        'idlelib',  # IDLE编辑器，不需要
        'venv'      # 虚拟环境，不需要
    ],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='chaifenup',
    debug=False,
    bootloader_ignore_signals=False,
    upx=True, # 保持 UPX 启用，如果你想排除UPX测试，改为 False
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=False, # 保持 onefile=False，单文件夹模式
    icon=None,
    version=None,
    manifest=None,
    uac_admin=False,
    uac_uiaccess=False,
    win_private_assemblies=True,
    win_no_prefer_redirects=True
)