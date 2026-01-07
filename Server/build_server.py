# -*- coding: utf-8 -*-
"""
服务器打包脚本
使用 PyInstaller 将服务器程序打包为单个可执行文件
"""
import os
import sys
import shutil
import subprocess

def main():
    print("=" * 60)
    print("斯能服务器管理系统 - 服务器端打包工具")
    print("=" * 60)
    
    # 当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # 输出目录
    dist_dir = os.path.join(current_dir, "dist")
    build_dir = os.path.join(current_dir, "build")
    
    print(f"\n当前目录: {current_dir}")
    print(f"父目录: {parent_dir}")
    print(f"输出目录: {dist_dir}")
    
    # 检查 PyInstaller
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", "pyinstaller"], 
                      check=True, capture_output=True)
    except:
        print("\n正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # 准备打包命令（使用原始字符串避免转义问题）
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['start_server.py'],
    pathex=[r'{current_dir}', r'{parent_dir}'],
    binaries=[],
    datas=[
        (r'{os.path.join(parent_dir, "config.json")}', '.'),
        (r'{os.path.join(parent_dir, "config_manager.py")}', '.'),
    ],
    hiddenimports=[
        'win32security',
        'win32api',
        'win32con',
        'ntsecuritycon',
        'pywintypes',
        'flask',
        'flask_cors',
        'watchdog',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd_a = Analysis(
    ['start_server.py'],
    pathex=['{current_dir}', '{parent_dir}'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PermissionServer',
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
    uac_admin=True,
)
'''
    
    # 写入 spec 文件
    spec_file = os.path.join(current_dir, "server.spec")
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"\n✓ 已生成 spec 文件: {spec_file}")
    
    # 执行打包
    print("\n开始打包...")
    print("=" * 60)
    
    try:
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            spec_file
        ], check=True, cwd=current_dir)
        
        print("\n" + "=" * 60)
        print("✓ 打包成功！")
        print("=" * 60)
        
        exe_path = os.path.join(dist_dir, "PermissionServer.exe")
        if os.path.exists(exe_path):
            print(f"\n可执行文件位置: {exe_path}")
            print(f"文件大小: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
        
        # 复制必要文件到 dist 目录
        print("\n正在复制必要文件...")
        
        # 复制配置文件
        config_src = os.path.join(parent_dir, "config.json")
        config_dst = os.path.join(dist_dir, "config.json")
        if os.path.exists(config_src):
            shutil.copy2(config_src, config_dst)
            print(f"✓ 已复制: config.json")
        
        # 创建启动脚本
        start_bat = os.path.join(dist_dir, "启动服务器.bat")
        with open(start_bat, 'w', encoding='gbk') as f:
            f.write('@echo off\n')
            f.write('echo 正在启动服务器...\n')
            f.write('PermissionServer.exe\n')
            f.write('pause\n')
        print(f"✓ 已创建: 启动服务器.bat")
        
        # 创建部署说明
        readme = os.path.join(dist_dir, "部署说明.txt")
        with open(readme, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("斯能服务器管理系统 - 服务器端部署说明\n")
            f.write("=" * 60 + "\n\n")
            f.write("部署步骤：\n")
            f.write("1. 将整个 dist 文件夹复制到目标服务器 192.168.110.77\n")
            f.write("   建议路径: C:\\PermissionServer\\\n\n")
            f.write("2. 双击 '启动服务器.bat' 启动服务（需要管理员权限）\n")
            f.write("   或者直接运行 PermissionServer.exe（需要管理员权限）\n\n")
            f.write("3. 设置开机自启动：\n")
            f.write("   a) 确保程序复制到 C:\\PermissionServer\\ 目录\n")
            f.write("   b) 如果路径不同，请编辑 PermissionServer_Startup.xml 修改路径\n")
            f.write("   c) 右键以管理员身份运行 '设置开机自启动.bat'\n\n")
            f.write("4. 打开防火墙 5000 端口：\n")
            f.write("   netsh advfirewall firewall add rule name=\"PermissionServer\" dir=in action=allow protocol=TCP localport=5000\n\n")
            f.write("配置文件：\n")
            f.write("- config.json: 系统配置文件，可修改系统名称、用户映射等\n\n")
            f.write("服务地址：\n")
            f.write("- 本地访问: http://localhost:5000/health\n")
            f.write("- 网络访问: http://192.168.110.77:5000/health\n")
            f.write("- 系统信息: http://192.168.110.77:5000/api/info\n\n")
            f.write("管理命令：\n")
            f.write("- 查看任务: schtasks /query /tn \"PermissionServer\"\n")
            f.write("- 运行任务: schtasks /run /tn \"PermissionServer\"\n")
            f.write("- 停止服务: taskkill /f /im PermissionServer.exe\n")
            f.write("- 删除任务: schtasks /delete /tn \"PermissionServer\" /f\n\n")
            f.write("详细说明请查看 '服务器部署指南.md'\n\n")
            f.write("=" * 60 + "\n")
        print(f"✓ 已创建: 部署说明.txt")
        
        # 复制任务计划文件
        task_xml_src = os.path.join(current_dir, "PermissionServer_Startup.xml")
        task_xml_dst = os.path.join(dist_dir, "PermissionServer_Startup.xml")
        if os.path.exists(task_xml_src):
            shutil.copy2(task_xml_src, task_xml_dst)
            print(f"✓ 已复制: PermissionServer_Startup.xml")
        
        # 复制自启动设置脚本
        startup_bat_src = os.path.join(current_dir, "设置开机自启动.bat")
        startup_bat_dst = os.path.join(dist_dir, "设置开机自启动.bat")
        if os.path.exists(startup_bat_src):
            shutil.copy2(startup_bat_src, startup_bat_dst)
            print(f"✓ 已复制: 设置开机自启动.bat")
        
        # 复制部署指南
        guide_src = os.path.join(current_dir, "服务器部署指南.md")
        guide_dst = os.path.join(dist_dir, "服务器部署指南.md")
        if os.path.exists(guide_src):
            shutil.copy2(guide_src, guide_dst)
            print(f"✓ 已复制: 服务器部署指南.md")
        
        print("\n" + "=" * 60)
        print("打包完成！部署文件位于:")
        print(dist_dir)
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print("\n✗ 打包失败！")
        print(f"错误: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
