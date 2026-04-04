# 导入必要的模块
import sys
import socket
import json

# 从Revit API导入必要的类
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import CurveElement
from Autodesk.Revit.DB import Line

# 尝试导入redis库（可选）
try:
    import redis
    redis_available = True
except ImportError:
    redis_available = False

# 收集墙体元素
walls = Fec(doc).OfCategory(Bic.OST_Walls).WhereElementIsNotElementType().ToElements()

# 不需要收集线元素，只处理墙元素
line_elements = []
print("已禁用线元素收集，只处理墙元素")

# 准备墙体数据
wall_data_list = []

# 处理墙元素
all_bricks = []

print("\n处理墙元素:")
if walls:
    print(f"找到 {len(walls)} 个墙元素")
    for i, wall in enumerate(walls):
        try:
            # 获取墙的边界框
            bbox = wall.get_BoundingBox(None)
            if bbox is None:
                continue
            
            # 计算墙的8个点坐标
            x1 = bbox.Max.X
            y1 = bbox.Max.Y
            z1 = bbox.Max.Z
            
            x2 = bbox.Min.X
            y2 = bbox.Min.Y
            z2 = bbox.Min.Z
            
            center_x = (bbox.Min.X + bbox.Max.X) / 2
            center_y = (bbox.Min.Y + bbox.Max.Y) / 2
            center_z = (bbox.Min.Z + bbox.Max.Z) / 2
            
            x3 = x2
            y3 = y1
            z3 = z1
            
            x4 = x1
            y4 = y2
            z4 = z1
            
            x5 = x2
            y5 = y2
            z5 = z1
            
            x6 = x2
            y6 = y1
            z6 = z2
            
            x7 = x1
            y7 = y1
            z7 = z2
            
            x8 = x1
            y8 = y2
            z8 = z2
            
            brick = {
                "id": f"wall_{wall.Id}",
                "center_point": [center_x, center_y, center_z],
                "max_point": [x1, y1, z1],
                "min_point": [x2, y2, z2],
                "point3": [x3, y3, z3],
                "point4": [x4, y4, z4],
                "point5": [x5, y5, z5],
                "point6": [x6, y6, z6],
                "point7": [x7, y7, z7],
                "point8": [x8, y8, z8]
            }
            all_bricks.append(brick)
            print(f"  创建墙砖块: ID=wall_{wall.Id}")
        except Exception as e:
            print(f"  处理墙 {wall.Id} 时出错: {e}")
else:
    print("没有找到墙元素")

# 创建虚拟墙体来包含所有砖块
print("\n创建虚拟墙体:")
if all_bricks:
    print(f"创建虚拟墙体，包含 {len(all_bricks)} 个砖块")
    virtual_wall = {
        "id": "virtual_wall",
        "center_point": [0, 0, 0],  # 虚拟中心点
        "bricks": all_bricks,
        "brick_count": len(all_bricks)
    }
    wall_data_list.append(virtual_wall)
else:
    print("没有找到任何砖块，创建空的虚拟墙体")
    # 创建一个空的虚拟墙体，确保即使没有砖块也能发送数据
    virtual_wall = {
        "id": "virtual_wall",
        "center_point": [0, 0, 0],  # 虚拟中心点
        "bricks": [],
        "brick_count": 0
    }
    wall_data_list.append(virtual_wall)

print(f"最终墙体数据列表长度: {len(wall_data_list)}")

# 保存数据到Redis
if redis_available:
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.set('revit_wall_data', json.dumps(wall_data_list))
    except:
        pass

# 启动TCP服务器
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(("127.0.0.1", 8080))
        server.listen(1)
        
        # 等待连接
        client, addr = server.accept()
        
        # 处理连接
        client.recv(1024)  # 接收握手
        client.send("Hello\r\n".encode('utf-8'))  # 发送响应
        
        # 发送数据
        for wall in wall_data_list:
            # 确保JSON格式正确
            json_data = json.dumps(wall, ensure_ascii=False, separators=(',', ':'))
            client.send((json_data + "\n").encode('utf-8'))
        
        client.send("DATA_END\n".encode('utf-8'))  # 发送结束标记
        client.close()
        
    except Exception as e:
        pass
    finally:
        server.close()

# 执行服务器
start_server()
