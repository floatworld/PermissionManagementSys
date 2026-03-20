# -*- coding: utf-8 -*-
"""
Flask API 路由层
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from datetime import datetime

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_manager import config
from services import DirectoryService, PermissionService, AuditService, SystemService
from dao import UserDAO, DirectoryDAO, PermissionDAO


app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ==================== 目录管理 API ====================

@app.route('/api/directory/structure', methods=['GET'])
def get_directory_structure():
    """获取目录树结构"""
    try:
        structure = DirectoryService.get_directory_structure()
        return jsonify({
            "success": True,
            "data": structure
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/directory/scan', methods=['POST'])
def scan_directory():
    """扫描并同步目录"""
    data = request.json
    root_path = data.get('path')
    is_shared = data.get('is_shared', False)
    
    if not root_path:
        return jsonify({"success": False, "error": "缺少参数: path"}), 400
    
    if not os.path.exists(root_path):
        return jsonify({"success": False, "error": f"路径不存在: {root_path}"}), 400
    
    try:
        count = DirectoryService.sync_directory_to_database(root_path, is_shared)
        return jsonify({
            "success": True,
            "message": f"同步完成，共 {count} 个目录"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/directory/tree', methods=['POST'])
def scan_directory_tree():
    """扫描目录树（不写入数据库）"""
    data = request.json
    root_path = data.get('path')
    max_depth = data.get('max_depth', 3)
    
    if not root_path:
        return jsonify({"success": False, "error": "缺少参数: path"}), 400
    
    try:
        tree = DirectoryService.scan_directory_tree(root_path, max_depth)
        return jsonify({
            "success": True,
            "data": tree
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 权限管理 API ====================

@app.route('/api/permissions', methods=['GET'])
def get_all_permissions():
    """获取所有权限记录"""
    try:
        permissions = PermissionDAO.list_all()
        return jsonify({
            "success": True,
            "data": permissions,
            "count": len(permissions)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/permissions/user/<username>', methods=['GET'])
def get_user_permissions(username):
    """获取用户的权限列表"""
    try:
        permissions = PermissionService.get_user_permissions(username)
        return jsonify({
            "success": True,
            "data": permissions,
            "count": len(permissions)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/permissions/directory', methods=['POST'])
def get_directory_permissions():
    """获取目录的权限列表（从数据库）"""
    data = request.json
    directory_path = data.get('path')
    
    if not directory_path:
        return jsonify({"success": False, "error": "缺少参数: path"}), 400
    
    try:
        permissions = PermissionService.get_folder_permissions(directory_path)
        return jsonify({
            "success": True,
            "data": permissions,
            "count": len(permissions)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/directory/system-permissions', methods=['GET'])
def get_directory_system_permissions():
    """获取目录的系统权限（实时从Windows ACL读取），过滤配置文件中的用户"""
    directory_path = request.args.get('path')
    
    if not directory_path:
        return jsonify({"success": False, "error": "缺少参数: path"}), 400
    
    try:
        # 获取系统权限
        result = SystemService.get_file_permissions(directory_path)
        
        if result.get('success'):
            permissions = result.get('permissions', [])
            
            # 获取配置文件中的用户映射
            user_mapping = config.user_mapping
            
            # 过滤出配置文件中存在的用户
            filtered_permissions = []
            for perm in permissions:
                username = perm.get('username', '').lower()
                # 检查用户名是否在配置文件中（不区分大小写）
                if username in user_mapping:
                    # 添加中文名
                    perm['chinese_name'] = user_mapping[username]
                    filtered_permissions.append(perm)
            
            # 返回过滤后的权限列表
            return jsonify({
                "success": True,
                "permissions": filtered_permissions,
                "total_permissions": len(permissions),
                "filtered_count": len(filtered_permissions)
            })
        else:
            return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/permissions/grant', methods=['POST'])
def grant_permission():
    """授予权限"""
    data = request.json
    
    # 必需参数
    username = data.get('username')
    directory_path = data.get('directory_path')
    
    if not username or not directory_path:
        return jsonify({
            "success": False, 
            "error": "缺少必需参数: username, directory_path"
        }), 400
    
    # 可选参数
    can_read = data.get('can_read', False)
    can_write = data.get('can_write', False)
    can_delete = data.get('can_delete', False)
    can_execute = data.get('can_execute', False)
    is_recursive = data.get('is_recursive', False)
    granted_by = data.get('granted_by', 'admin')
    note = data.get('note', '')
    
    try:
        result = PermissionService.grant_permission(
            username, directory_path,
            can_read, can_write, can_delete, can_execute,
            is_recursive, granted_by, note
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/permissions/revoke', methods=['POST'])
def revoke_permission():
    """撤销权限"""
    data = request.json
    username = data.get('username')
    directory_path = data.get('directory_path')
    
    if not username or not directory_path:
        return jsonify({
            "success": False,
            "error": "缺少必需参数: username, directory_path"
        }), 400
    
    try:
        result = PermissionService.revoke_permission(username, directory_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/permissions/check', methods=['POST'])
def check_permission():
    """检查权限"""
    data = request.json
    username = data.get('username')
    directory_path = data.get('directory_path')
    action = data.get('action', 'read')  # read/write/delete/execute
    
    if not username or not directory_path:
        return jsonify({
            "success": False,
            "error": "缺少必需参数: username, directory_path"
        }), 400
    
    try:
        has_permission = PermissionService.check_permission(
            username, directory_path, action
        )
        return jsonify({
            "success": True,
            "has_permission": has_permission,
            "action": action
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 用户管理 API ====================

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """获取所有用户"""
    try:
        users = UserDAO.list_all()
        return jsonify({
            "success": True,
            "data": users,
            "count": len(users)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/users/<username>', methods=['GET'])
def get_user(username):
    """获取单个用户信息"""
    try:
        user = UserDAO.get_by_username(username)
        if user:
            return jsonify({"success": True, "data": user})
        else:
            return jsonify({"success": False, "error": "用户不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/users', methods=['POST'])
def create_user():
    """创建用户"""
    data = request.json
    username = data.get('username')
    role = data.get('role', '普通用户')
    
    if not username:
        return jsonify({"success": False, "error": "缺少参数: username"}), 400
    
    try:
        # 检查用户是否已存在
        existing = UserDAO.get_by_username(username)
        if existing:
            return jsonify({
                "success": False,
                "error": f"用户 {username} 已存在"
            }), 400
        
        user_id = UserDAO.create(username, role)
        return jsonify({
            "success": True,
            "user_id": user_id,
            "message": f"用户 {username} 创建成功"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 审计日志 API ====================

@app.route('/api/audit/logs', methods=['GET'])
def get_audit_logs():
    """查询审计日志"""
    username = request.args.get('username')
    action_type = request.args.get('action_type')
    file_path = request.args.get('file_path')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    limit = int(request.args.get('limit', 1000))
    
    try:
        logs = AuditService.query_audit_logs(
            username, action_type, file_path,
            start_time, end_time, limit
        )
        return jsonify({
            "success": True,
            "data": logs,
            "count": len(logs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/audit/user/<username>', methods=['GET'])
def get_user_audit_logs(username):
    """获取用户的审计日志"""
    limit = int(request.args.get('limit', 1000))
    
    try:
        logs = AuditService.get_user_activity(username, limit)
        return jsonify({
            "success": True,
            "data": logs,
            "count": len(logs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/audit/statistics', methods=['GET'])
def get_audit_statistics():
    """获取审计统计信息"""
    try:
        stats = AuditService.get_statistics()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 系统管理 API ====================

@app.route('/api/system/local-users', methods=['GET'])
def get_local_users():
    """获取本地所有Windows用户"""
    try:
        users = SystemService.get_local_users()
        return jsonify({
            "success": True,
            "data": users,
            "count": len(users)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/system/create-user', methods=['POST'])
def create_local_user():
    """
    创建本地Windows用户
    
    参数: username, password, fullname(可选), comment(可选)
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    fullname = data.get('fullname', '')
    comment = data.get('comment', '')
    
    # 参数验证
    if not username:
        return jsonify({"success": False, "message": "缺少参数: username"}), 400
    if not password:
        return jsonify({"success": False, "message": "缺少参数: password"}), 400
    
    try:
        result = SystemService.create_local_user(username, password, fullname, comment)
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"创建用户异常: {str(e)}"
        }), 500


@app.route('/api/system/delete-user', methods=['POST'])
def delete_local_user():
    """
    删除本地Windows用户
    
    参数: username
    """
    data = request.get_json()
    username = data.get('username')
    
    # 参数验证
    if not username:
        return jsonify({"success": False, "message": "缺少参数: username"}), 400
    
    try:
        result = SystemService.delete_local_user(username)
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"删除用户异常: {str(e)}"
        }), 500


@app.route('/api/system/set-permission', methods=['POST'])
def set_file_permission():
    """
    给指定文件/文件夹添加Windows用户权限
    
    请求体:
    {
        "file_path": "C:\\path\\to\\file",
        "username": "UserName",
        "read": true,
        "write": true,
        "modify": false,
        "full_control": false,
        "recursive": false
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            print(f"[ACL设置] 错误：未接收到JSON数据")
            return jsonify({
                "success": False,
                "message": "未接收到JSON数据"
            }), 400
        
        # 打印调试信息
        print(f"[ACL设置] 收到请求: {data}")
        
        file_path = data.get('file_path')
        username = data.get('username')
        read = data.get('read', False)
        write = data.get('write', False)
        modify = data.get('modify', False)
        full_control = data.get('full_control', False)
        recursive = data.get('recursive', False)
        
        print(f"[ACL设置] 解析参数: file_path={file_path}, username={username}")
        
        if not file_path or not username:
            error_msg = f"缺少必需参数: file_path={'✓' if file_path else '✗'}, username={'✓' if username else '✗'}"
            print(f"[ACL设置] 参数验证失败: {error_msg}")
            return jsonify({
                "success": False,
                "message": error_msg
            }), 400
        
        if not (read or write or modify or full_control):
            print(f"[ACL设置] 未选择任何权限")
            return jsonify({
                "success": False,
                "message": "至少需要选择一个权限"
            }), 400
        
        print(f"[ACL设置] 调用SystemService.set_file_permission...")
        result = SystemService.set_file_permission(
            file_path, username, read, write, modify, full_control, recursive
        )
        
        print(f"[ACL设置] 结果: {result}")
        
        # 即使业务逻辑失败，也返回200状态码，让客户端根据success字段判断
        return jsonify(result)
            
    except Exception as e:
        print(f"[ACL设置] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/system/set-permissions-batch', methods=['POST'])
def set_file_permissions_batch():
    """
    批量给多个文件夹设置多个用户的Windows权限
    
    请求体:
    {
        "file_paths": ["C:\\path1", "C:\\path2"],
        "usernames": ["User1", "User2"],
        "read": true,
        "write": false,
        "modify": false,
        "full_control": false,
        "recursive": false
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "未接收到JSON数据"}), 400
        
        print(f"[ACL批量设置] 收到请求: {data}")
        
        file_paths = data.get('file_paths', [])
        usernames = data.get('usernames', [])
        read = data.get('read', False)
        write = data.get('write', False)
        modify = data.get('modify', False)
        full_control = data.get('full_control', False)
        recursive = data.get('recursive', False)
        
        if not file_paths:
            return jsonify({"success": False, "message": "缺少必需参数: file_paths"}), 400
        if not usernames:
            return jsonify({"success": False, "message": "缺少必需参数: usernames"}), 400
        if not (read or write or modify or full_control):
            return jsonify({"success": False, "message": "至少需要选择一个权限"}), 400
        
        results = []
        success_count = 0
        fail_count = 0
        
        for file_path in file_paths:
            for username in usernames:
                try:
                    result = SystemService.set_file_permission(
                        file_path, username, read, write, modify, full_control, recursive
                    )
                    entry = {
                        "file_path": file_path,
                        "username": username,
                        "success": result.get('success', False),
                        "message": result.get('message', '')
                    }
                    results.append(entry)
                    if result.get('success'):
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    results.append({
                        "file_path": file_path,
                        "username": username,
                        "success": False,
                        "message": str(e)
                    })
                    fail_count += 1
        
        print(f"[ACL批量设置] 完成: 成功={success_count}, 失败={fail_count}")
        
        total = len(file_paths) * len(usernames)
        if fail_count == 0:
            status = 'all_success'
        elif success_count > 0:
            status = 'partial_success'
        else:
            status = 'all_failed'
        
        return jsonify({
            "success": fail_count == 0,
            "status": status,
            "success_count": success_count,
            "fail_count": fail_count,
            "total": total,
            "results": results
        })
        
    except Exception as e:
        print(f"[ACL批量设置] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/system/remove-permission', methods=['POST'])
def remove_file_permission():
    """
    删除用户对文件/文件夹的所有Windows ACL权限
    
    请求体:
    {
        "file_path": "C:\\path\\to\\file",
        "username": "UserName"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            print(f"[ACL删除] 错误：未接收到JSON数据")
            return jsonify({
                "success": False,
                "message": "未接收到JSON数据"
            }), 400
        
        print(f"[ACL删除] 收到请求: {data}")
        
        file_path = data.get('file_path')
        username = data.get('username')
        
        print(f"[ACL删除] 解析参数: file_path={file_path}, username={username}")
        
        if not file_path or not username:
            error_msg = f"缺少必需参数: file_path={'✓' if file_path else '✗'}, username={'✓' if username else '✗'}"
            print(f"[ACL删除] 参数验证失败: {error_msg}")
            return jsonify({
                "success": False,
                "message": error_msg
            }), 400
        
        print(f"[ACL删除] 调用SystemService.remove_file_permission...")
        result = SystemService.remove_file_permission(file_path, username)
        
        print(f"[ACL删除] 结果: {result}")
        
        # 即使业务逻辑失败（如未找到权限），也返回200状态码，让客户端根据success字段判断
        return jsonify(result)
            
    except Exception as e:
        print(f"[ACL删除] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/system/get-permission', methods=['GET'])
def get_file_permission():
    """
    获取文件/文件夹的当前权限列表
    
    参数: file_path
    """
    file_path = request.args.get('file_path')
    
    if not file_path:
        return jsonify({
            "success": False,
            "error": "缺少参数: file_path"
        }), 400
    
    try:
        result = SystemService.get_file_permissions(file_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 健康检查 API ====================

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": config.system_name
    })


@app.route('/api/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        user_count = len(UserDAO.list_all())
        dir_count = len(DirectoryDAO.list_all())
        perm_count = len(PermissionDAO.list_all())
        
        return jsonify({
            "success": True,
            "data": {
                "system_name": config.system_name,
                "version": "2.0.0",
                "user_count": user_count,
                "directory_count": dir_count,
                "permission_count": perm_count,
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "接口不存在"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500


if __name__ == '__main__':
    # 初始化数据库
    from database import DatabaseManager
    db = DatabaseManager()
    db.init_database()
    print("数据库初始化完成")
    
    # 启动Flask服务
    print("=" * 60)
    print("斯能服务器管理系统 - API服务启动")
    print("=" * 60)
    print(f"服务地址: http://0.0.0.0:5000")
    print(f"健康检查: http://0.0.0.0:5000/health")
    print(f"系统信息: http://0.0.0.0:5000/api/info")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
