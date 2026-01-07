"""
创建应用程序图标
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """创建权限管理系统图标"""
    # 创建多个尺寸的图标
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for size in sizes:
        # 创建图像
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 背景渐变（深蓝色）
        for y in range(size[1]):
            color_value = int(26 + (74 - 26) * y / size[1])  # 从#1a4a7a到#2a5a8a
            draw.rectangle([(0, y), (size[0], y+1)], fill=(26, color_value, 122, 255))
        
        # 绘制盾牌形状（权限管理的象征）
        shield_points = [
            (size[0] * 0.5, size[1] * 0.1),   # 顶部
            (size[0] * 0.8, size[1] * 0.3),   # 右上
            (size[0] * 0.8, size[1] * 0.6),   # 右中
            (size[0] * 0.5, size[1] * 0.9),   # 底部
            (size[0] * 0.2, size[1] * 0.6),   # 左中
            (size[0] * 0.2, size[1] * 0.3),   # 左上
        ]
        draw.polygon(shield_points, fill=(255, 255, 255, 200), outline=(255, 215, 0, 255))
        
        # 绘制锁的图标
        lock_center_x = size[0] * 0.5
        lock_center_y = size[1] * 0.5
        lock_size = size[0] * 0.15
        
        # 锁的身体
        draw.rectangle([
            (lock_center_x - lock_size, lock_center_y),
            (lock_center_x + lock_size, lock_center_y + lock_size * 1.5)
        ], fill=(74, 158, 255, 255))
        
        # 锁的弧形部分
        draw.arc([
            (lock_center_x - lock_size * 0.7, lock_center_y - lock_size),
            (lock_center_x + lock_size * 0.7, lock_center_y + lock_size * 0.3)
        ], start=180, end=0, fill=(74, 158, 255, 255), width=max(2, size[0]//32))
        
        images.append(img)
    
    # 保存为ICO文件
    icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'app_icon.ico')
    images[0].save(icon_path, format='ICO', sizes=[img.size for img in images], append_images=images[1:])
    print(f"图标已创建: {icon_path}")
    
    # 同时保存PNG版本（用于任务栏）
    png_path = os.path.join(os.path.dirname(__file__), 'resources', 'app_icon.png')
    images[-1].save(png_path, format='PNG')
    print(f"PNG图标已创建: {png_path}")

if __name__ == '__main__':
    try:
        create_app_icon()
    except ImportError:
        print("需要安装 Pillow 库: pip install Pillow")
    except Exception as e:
        print(f"创建图标时出错: {e}")
