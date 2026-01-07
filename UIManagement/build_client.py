# -*- coding: utf-8 -*-
"""
客户端打包脚本
使用 PyInstaller 将客户端程序打包为单个可执行文件
"""
import os
import sys
import shutil
import subprocess

def main():
    print("=" * 60)
    print("斯能服务器管理系统 - 客户端打包工具")
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
    current_dir_escaped = current_dir.replace('\\', '\\\\')
    parent_dir_escaped = parent_dir.replace('\\', '\\\\')
    config_json_path = os.path.join(parent_dir, "config.json").replace('\\', '\\\\')
    config_manager_path = os.path.join(parent_dir, "config_manager.py").replace('\\', '\\\\')
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_window.py'],
    pathex=[r'{current_dir}', r'{parent_dir}'],
    binaries=[],
    datas=[
        (r'{os.path.join(parent_dir, "config.json")}', '.'),
        (r'{os.path.join(parent_dir, "config_manager.py")}', '.'),
        (r'{os.path.join(current_dir, "resources", "app_icon.ico")}', 'resources'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'requests',
        'json',
        'datetime',
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PermissionClient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'{os.path.join(current_dir, "resources", "app_icon.ico")}',
)
'''
    
    # 写入 spec 文件
    spec_file = os.path.join(current_dir, "client.spec")
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
        
        exe_path = os.path.join(dist_dir, "PermissionClient.exe")
        if os.path.exists(exe_path):
            print(f"\n可执行文件位置: {exe_path}")
            print(f"文件大小: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
        
        # 复制必要文件到 dist 目录
        print("\n正在复制必要文件...")
        
        # 创建客户端专用的配置文件（服务器地址为 192.168.110.77）
        config_dst = os.path.join(dist_dir, "config.json")
        client_config = {
            "system_name": "斯能服务器管理系统",
            "server": {
                "host": "192.168.110.77",  # 客户端默认连接到服务器
                "port": 5000
            },
            "default_directory": "D:\\\\存放资料",
            "user_mapping": {
                "lijing": "李静",
                "zhanggongan": "张公安",
                "yanghaitao": "杨海涛",
                "lirunhui": "李润辉",
                "huanghui": "黄卉",
                "maosongjie": "毛宋杰",
                "yuanxiaofang": "袁晓芳",
                "yuguolong": "余国龙",
                "yehao": "叶浩",
                "tumeng": "图勐",
                "pengzhilong": "彭治龙",
                "liwenting": "李文婷",
                "chenglei": "程雷"
            }
        }
        
        import json
        with open(config_dst, 'w', encoding='utf-8') as f:
            json.dump(client_config, f, ensure_ascii=False, indent=2)
        print(f"✓ 已创建客户端配置: config.json (服务器地址: 192.168.110.77:5000)")
        
        # 复制resources文件夹（包含图标）
        resources_src = os.path.join(current_dir, "resources")
        resources_dst = os.path.join(dist_dir, "resources")
        if os.path.exists(resources_src):
            if os.path.exists(resources_dst):
                shutil.rmtree(resources_dst)
            shutil.copytree(resources_src, resources_dst)
            print(f"✓ 已复制资源文件夹: resources/ (包含应用图标)")
        
        # 创建启动脚本
        start_bat = os.path.join(dist_dir, "启动客户端.bat")
        with open(start_bat, 'w', encoding='gbk') as f:
            f.write('@echo off\n')
            f.write('echo 正在启动客户端...\n')
            f.write('start PermissionClient.exe\n')
            f.write('exit\n')
        print(f"✓ 已创建: 启动客户端.bat")
        
        # 创建配置服务器地址的脚本
        config_server_bat = os.path.join(dist_dir, "配置服务器地址.bat")
        with open(config_server_bat, 'w', encoding='gbk') as f:
            f.write('@echo off\n')
            f.write('chcp 65001 >nul\n')
            f.write('echo ====================================\n')
            f.write('echo 配置服务器地址\n')
            f.write('echo ====================================\n')
            f.write('echo.\n')
            f.write('echo 当前默认服务器地址: 192.168.110.77:5000\n')
            f.write('echo.\n')
            f.write('echo 如需修改，请手动编辑 config.json 文件\n')
            f.write('echo 修改 server.host 和 server.port 配置项\n')
            f.write('echo.\n')
            f.write('notepad config.json\n')
            f.write('pause\n')
        print(f"✓ 已创建: 配置服务器地址.bat")
        
        # 创建快捷方式创建脚本（修复版 - 无中文注释）
        create_shortcut_vbs = os.path.join(dist_dir, "创建桌面快捷方式.vbs")
        with open(create_shortcut_vbs, 'w', encoding='gbk') as f:  # 改用gbk编码
            f.write('Set WshShell = WScript.CreateObject("WScript.Shell")\n')
            f.write('strDesktop = WshShell.SpecialFolders("Desktop")\n')
            f.write('\n')
            f.write('strScriptPath = WScript.ScriptFullName\n')
            f.write('strScriptDir = Left(strScriptPath, InStrRev(strScriptPath, "\\"))\n')
            f.write('\n')
            f.write('Set oShellLink = WshShell.CreateShortcut(strDesktop & "\\斯能服务器管理系统.lnk")\n')
            f.write('oShellLink.TargetPath = strScriptDir & "PermissionClient.exe"\n')
            f.write('oShellLink.WorkingDirectory = strScriptDir\n')
            f.write('oShellLink.Description = "斯能服务器管理系统客户端"\n')
            f.write('oShellLink.IconLocation = strScriptDir & "resources\\app_icon.ico"\n')
            f.write('oShellLink.Save\n')
            f.write('\n')
            f.write('MsgBox "桌面快捷方式创建成功！" & vbCrLf & "位置: " & strDesktop & "\\斯能服务器管理系统.lnk", vbInformation, "完成"\n')
        print(f"✓ 已创建: 创建桌面快捷方式.vbs（已修复）")
        
        # 创建部署说明
        readme = os.path.join(dist_dir, "部署说明.txt")
        with open(readme, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("斯能服务器管理系统 - 客户端部署说明\n")
            f.write("=" * 60 + "\n\n")
            f.write("部署步骤：\n")
            f.write("1. 将整个 dist 文件夹复制到客户端电脑\n")
            f.write("   建议路径: C:\\PermissionClient\\\n\n")
            f.write("2. 确认服务器地址配置正确\n")
            f.write("   服务器地址: 192.168.110.77:5000\n")
            f.write("   如需修改，双击 '配置服务器地址.bat'\n\n")
            f.write("3. 双击 'PermissionClient.exe' 或 '启动客户端.bat' 启动程序\n\n")
            f.write("4. （可选）双击 '创建桌面快捷方式.vbs' 创建桌面快捷方式\n\n")
            f.write("配置文件：\n")
            f.write("- config.json: 系统配置文件\n")
            f.write("  重要配置项:\n")
            f.write("  - server.host: 服务器IP地址（默认 192.168.110.77）⭐\n")
            f.write("  - server.port: 服务器端口（默认 5000）\n")
            f.write("  - system_name: 系统名称\n")
            f.write("  注意：首次启动后，程序会从配置文件读取服务器地址\n")
            f.write("       如需修改服务器地址，请编辑 config.json 后重启程序\n\n")
            f.write("连接要求：\n")
            f.write("1. 客户端电脑能够访问服务器 192.168.110.77\n")
            f.write("2. 服务器的 5000 端口已开放\n")
            f.write("3. 网络连通正常\n\n")
            f.write("使用说明：\n")
            f.write("1. 启动程序后会自动连接服务器\n")
            f.write("2. 顶部状态栏显示连接状态\n")
            f.write("3. 连接成功后可以进行权限管理、目录管理等操作\n")
            f.write("4. 如果连接失败，请检查：\n")
            f.write("   - 服务器是否正常运行\n")
            f.write("   - 网络是否连通\n")
            f.write("   - config.json 中的服务器地址是否正确\n\n")
            f.write("注意事项：\n")
            f.write("1. 无需管理员权限即可运行\n")
            f.write("2. 首次运行可能需要几秒钟初始化\n")
            f.write("3. 可以同时在多台客户端电脑上安装使用\n")
            f.write("4. 所有操作通过服务器统一管理\n\n")
            f.write("故障排除：\n")
            f.write("问题1: 无法连接服务器\n")
            f.write("  - 检查服务器是否运行: http://192.168.110.77:5000/health\n")
            f.write("  - 检查网络: ping 192.168.110.77\n")
            f.write("  - 检查端口: telnet 192.168.110.77 5000\n\n")
            f.write("问题2: 程序无法启动\n")
            f.write("  - 确认 PermissionClient.exe 完整\n")
            f.write("  - 确认 config.json 存在\n")
            f.write("  - 重新解压部署包\n\n")
            f.write("问题3: 配置文件错误\n")
            f.write("  - 从服务器获取最新的 config.json\n")
            f.write("  - 确保 JSON 格式正确\n\n")
            f.write("=" * 60 + "\n")
        print(f"✓ 已创建: 部署说明.txt")
        
        # 复制部署指南
        guide_files = [
            ("客户端部署指南.md", "客户端部署指南.md"),
            ("客户端部署清单.md", "客户端部署清单.md"),
            ("快速开始.md", "快速开始.md")
        ]
        
        for src_name, dst_name in guide_files:
            src_path = os.path.join(current_dir, src_name)
            dst_path = os.path.join(dist_dir, dst_name)
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)
                print(f"✓ 已复制: {dst_name}")
        
        print("\n" + "=" * 60)
        print("打包完成！部署文件位于:")
        print(dist_dir)
        print("\n可以将 dist 文件夹复制到任意客户端电脑使用")
        print("默认连接服务器: 192.168.110.77:5000")
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print("\n✗ 打包失败！")
        print(f"错误: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
