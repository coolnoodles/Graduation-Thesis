import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket  
from tkinter import font as tkfont  
import time  
import threading  

class IntelligentMasonrySystem:
    def __init__(self, master):
        self.master = master
        master.title("机器人虚拟砌筑指令发送软件")
        
        self.original_width = 900
        self.original_height = 800
        master.geometry("650x400")  
        master.update_idletasks()
        
        # 计算屏幕居中位置
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        x = (screen_width - self.original_width) // 2
        y = (screen_height - self.original_height) // 2
        master.geometry(f"+{x}+{y}")  # 设置窗口位置
        
        # 设置主题色
        self.primary_color = "#1E88E5"  # 主色调：蓝色
        self.secondary_color = "#4CAF50"  # 次要色调：绿色
        self.background_color = "#F5F5F5"  # 背景色：浅灰色
        self.error_color = "#F44336"  # 错误色：红色
        
        # 应用自定义样式
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 使用clam主题作为基础
        
        # 配置字体
        self.default_font = tkfont.Font(family="Microsoft YaHei UI", size=10)
        self.header_font = tkfont.Font(family="Microsoft YaHei UI", size=11, weight="bold")
        self.title_font = tkfont.Font(family="Microsoft YaHei UI", size=12, weight="bold")
        
        # 自定义按钮样式
        self.style.configure('TButton', font=self.default_font, background=self.primary_color)
        self.style.map('TButton', 
                      background=[('active', self.primary_color), ('pressed', '#1565C0')],
                      foreground=[('pressed', 'white'), ('active', 'white')])
        
        # 自定义标签框样式
        self.style.configure('TLabelframe', font=self.header_font, background=self.background_color)
        self.style.configure('TLabelframe.Label', font=self.header_font, background=self.background_color)
        
        # 自定义标签样式
        self.style.configure('TLabel', font=self.default_font, background=self.background_color)
        
        # 自定义Combobox样式
        self.style.configure('TCombobox', font=self.default_font)
        
        # 自定义Entry样式
        self.style.configure('TEntry', font=self.default_font)
        
        # 配置主窗口背景色
        master.configure(bg=self.background_color)
        
        # TCP连接相关变量
        self.client_socket = None
        self.connected = False
        self.robot_ip = "127.0.0.1"  # 默认IP
        self.robot_port = 8080  # 默认端口
        self.running = True
        self.initial_handshake_done = False
        
        # 砖块数据相关变量
        self.all_bricks = []  # 存储砖块数据
        self.revit_data = []  # 存储从Revit接收的墙体数据
        self.data_received = False  # 标记是否已接收到数据

        # 创建主框架
        self.main_frame = ttk.Frame(master, padding=15, style='Main.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.style.configure('Main.TFrame', background=self.background_color)
        
        # 左侧和右侧的容器框架
        content_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板 - 控制区域
        left_frame = ttk.Frame(content_frame, padding=10, style='Left.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.style.configure('Left.TFrame', background=self.background_color)
        
        # 右侧面板 - 点位信息和日志区域
        right_frame = ttk.Frame(content_frame, padding=10, style='Right.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.style.configure('Right.TFrame', background=self.background_color)
        
        # 点位信息区域 - 上半部分
        point_info_frame = ttk.LabelFrame(right_frame, text="砖块点位信息", padding=10, style='PointInfo.TLabelframe')
        point_info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.style.configure('PointInfo.TLabelframe.Label', font=self.header_font)
        
        self.point_info_text = scrolledtext.ScrolledText(point_info_frame, state='disabled', 
                                                         font=tkfont.Font(family="Microsoft YaHei UI", size=9))
        self.point_info_text.pack(fill=tk.BOTH, expand=True)
        self.point_info_text.configure(background="white", foreground="#333333")
        
        # 日志区域 - 下半部分
        log_frame = ttk.LabelFrame(right_frame, text="系统日志", padding=10, style='Log.TLabelframe')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.style.configure('Log.TLabelframe.Label', font=self.header_font)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='normal', font=self.default_font)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(background="white", foreground="#333333")

        # 连接状态指示器
        status_frame = ttk.LabelFrame(left_frame, text="系统状态", padding=10, style='Status.TLabelframe')
        status_frame.pack(fill=tk.X, pady=(0, 15))
        self.style.configure('Status.TLabelframe.Label', font=self.header_font)
        
        self.conn_status_frame = ttk.Frame(status_frame, style='Main.TFrame')
        self.conn_status_frame.pack(fill=tk.X)
        
        self.status_indicator = tk.Canvas(self.conn_status_frame, width=20, height=20, bg=self.error_color, bd=0, highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(self.conn_status_frame, text="未连接", style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, fill=tk.X)
        self.style.configure('Status.TLabel', font=self.default_font, background=self.background_color)

        # 添加IP和端口配置
        self.create_tcp_settings(left_frame)
        
        # 连接按钮
        self.connect_btn = ttk.Button(left_frame, text="启动服务器", command=self.connect_tcp, style='Connect.TButton')
        self.connect_btn.pack(fill=tk.X, pady=(0, 15))
        self.style.configure('Connect.TButton', font=self.default_font)

        # 参数设置区域 - 使用LabelFrame包装
        params_frame = ttk.LabelFrame(left_frame, text="砌筑参数设置", padding=10, style='Params.TLabelframe')
        params_frame.pack(fill=tk.X, pady=(0, 15))
        self.style.configure('Params.TLabelframe.Label', font=self.header_font)
        
        # 添加参数设置组件
        self.create_comboboxes(params_frame)
        
        # 点位参数设置
        self.create_position_inputs(left_frame)
        
        # 开始砌筑按钮 - 底部
        self.start_btn = ttk.Button(left_frame, text="发送", command=self.start_masonry, style='Start.TButton')
        self.start_btn.pack(fill=tk.X, pady=(10, 0))
        self.style.configure('Start.TButton', font=self.header_font)
        
        # 初始状态下禁用开始砌筑按钮
        self.start_btn.configure(state="disabled")
        
        # 设置所有控件的初始透明度（通过将它们隐藏）
        self.main_frame.pack_forget()
        
        # 启动动画
        self.master.after(100, self.animate_window_open)
        
    def animate_window_open(self):
        # 首先显示主框架
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 执行窗口大小的动画
        steps = 15  # 动画步数
        current_width = self.master.winfo_width()
        current_height = self.master.winfo_height()
        width_step = (self.original_width - current_width) / steps
        height_step = (self.original_height - current_height) / steps
        
        def resize_step(step):
            if step > 0:
                new_width = int(current_width + width_step * (steps - step + 1))
                new_height = int(current_height + height_step * (steps - step + 1))
                self.master.geometry(f"{new_width}x{new_height}")
                self.master.update_idletasks()
                self.master.after(20, lambda: resize_step(step - 1))
            else:
                # 动画完成后记录系统日志
                self.log("系统启动：请先连接到服务器再开始砌筑任务")
        
        resize_step(steps)

    def create_comboboxes(self, parent):
        # 创建包含所有控件的框架
        controls_frame = ttk.Frame(parent, style='Main.TFrame')
        controls_frame.pack(fill=tk.X)
        
        # 墙类型
        type_frame = ttk.Frame(controls_frame, style='Main.TFrame')
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="墙的类型:", style='Param.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        self.style.configure('Param.TLabel', font=self.default_font, background=self.background_color)
        
        self.wall_type = ttk.Combobox(type_frame, values=["一丁一顺", "全丁", "全顺"], state="readonly", style='TCombobox')
        self.wall_type.current(0)
        self.wall_type.pack(side=tk.RIGHT, fill=tk.X, expand=True)
       
        # 层数
        layers_frame = ttk.Frame(controls_frame, style='Main.TFrame')
        layers_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(layers_frame, text="层数:", style='Param.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        
        self.layers = ttk.Combobox(layers_frame, values=["1", "2", "3"], state="readonly", style='TCombobox')
        self.layers.current(0)
        self.layers.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # 间隔
        interval_frame = ttk.Frame(controls_frame, style='Main.TFrame')
        interval_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(interval_frame, text="间隔:", style='Param.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        
        self.interval = ttk.Combobox(interval_frame, values=["5mm", "10mm"], state="readonly", style='TCombobox')
        self.interval.current(0)
        self.interval.pack(side=tk.RIGHT, fill=tk.X, expand=True)



    def create_position_inputs(self, parent):
        pos_frame = ttk.LabelFrame(parent, text="坐标设置", padding=10, style='Position.TLabelframe')
        pos_frame.pack(fill=tk.X, pady=(0, 15))
        self.style.configure('Position.TLabelframe.Label', font=self.header_font)

        # 创建包含所有坐标输入的框架
        coords_frame = ttk.Frame(pos_frame, style='Main.TFrame')
        coords_frame.pack(fill=tk.X)
        
        # X坐标
        x_frame = ttk.Frame(coords_frame, style='Main.TFrame')
        x_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(x_frame, text="X 坐标:", style='Coord.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        self.style.configure('Coord.TLabel', font=self.default_font, background=self.background_color)
        
        self.x_entry = ttk.Entry(x_frame, style='TEntry')
        self.x_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Y坐标
        y_frame = ttk.Frame(coords_frame, style='Main.TFrame')
        y_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(y_frame, text="Y 坐标:", style='Coord.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        
        self.y_entry = ttk.Entry(y_frame, style='TEntry')
        self.y_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Z坐标
        z_frame = ttk.Frame(coords_frame, style='Main.TFrame')
        z_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(z_frame, text="Z 坐标:", style='Coord.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        
        self.z_entry = ttk.Entry(z_frame, style='TEntry')
        self.z_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def create_tcp_settings(self, parent):
        tcp_frame = ttk.LabelFrame(parent, text="TCP连接设置", padding=10, style='TCP.TLabelframe')
        tcp_frame.pack(fill=tk.X, pady=(0, 15))
        self.style.configure('TCP.TLabelframe.Label', font=self.header_font)
        
        settings_frame = ttk.Frame(tcp_frame, style='Main.TFrame')
        settings_frame.pack(fill=tk.X)
        
        # IP地址
        ip_frame = ttk.Frame(settings_frame, style='Main.TFrame')
        ip_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ip_frame, text="IP地址:", style='Network.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        self.style.configure('Network.TLabel', font=self.default_font, background=self.background_color)
        
        self.ip_entry = ttk.Entry(ip_frame, style='TEntry')
        self.ip_entry.insert(0, self.robot_ip)
        self.ip_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 端口
        port_frame = ttk.Frame(settings_frame, style='Main.TFrame')
        port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(port_frame, text="端口:", style='Network.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        
        self.port_entry = ttk.Entry(port_frame, style='TEntry')
        self.port_entry.insert(0, str(self.robot_port))
        self.port_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def connect_tcp(self):
        try:
            # 获取用户输入的IP和端口
            self.robot_ip = self.ip_entry.get()
            self.robot_port = int(self.port_entry.get())
            
            # 连接按钮状态变化动画
            self.connect_btn.configure(state="disabled", text="连接中...")
            self.log("正在连接到Revit数据服务器...")
            
            # 清空之前的数据
            self.revit_data = []
            
            # 启动连接线程
            self.connect_thread = threading.Thread(target=self.connect_to_revit)
            self.connect_thread.daemon = True
            self.connect_thread.start()
            
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("连接错误", error_msg)
            self.log(f"连接错误: {error_msg}")
            self.connect_btn.configure(state="normal", text="启动服务器")

    def connect_to_revit(self):
        """连接到Revit数据服务器"""
        try:
            # 更新UI状态
            self.master.after(0, lambda: self.status_label.configure(text="正在连接..."))
            
            # 清空之前的数据，避免旧数据干扰
            self.revit_data = []
            
            # 创建TCP客户端
            self.log("2. 准备TCP连接...")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            
            # 尝试连接Revit服务器
            self.log(f"3. 尝试连接到 {self.robot_ip}:{self.robot_port}")
            client_socket.connect((self.robot_ip, self.robot_port))
            self.connected = True
            
            # 更新UI
            self.master.after(0, lambda: self.animate_status_change(True))
            self.master.after(0, lambda: self.status_label.configure(text="已连接到Revit"))
            self.master.after(0, lambda: self.start_btn.configure(state="normal"))
            self.log("✅ 成功连接到Revit数据服务器")
            
            # 发送握手消息（静默处理，不显示日志）
            client_socket.send("Hello server\n".encode('utf-8'))
            
            # 接收握手响应（静默处理，不显示日志）
            response = client_socket.recv(1024)
            
            # 接收墙体数据
            self.log("6. 开始接收墙体数据...")
            # 清空数据，确保只显示从Revit服务器接收到的新数据
            self.revit_data = []
            self.receive_revit_data(client_socket)
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ 连接失败: {error_msg}")
            self.log("⚠️ 将尝试从Redis获取数据作为备用")
            self.log("请确保：")
            self.log("1. Revit脚本已运行")
            self.log("2. Redis服务器已启动")
            self.log("3. 防火墙已允许连接")
            
            self.master.after(0, lambda: self.animate_status_change(False))
            self.master.after(0, lambda: self.status_label.configure(text="未连接"))
        finally:
            # 恢复按钮状态
            self.master.after(0, lambda: self.connect_btn.configure(state="normal", text="启动服务器"))
            
            # 确保如果有数据，显示在墙体点位信息区域
            if self.revit_data:
                self.master.after(0, self.display_revit_data)
                self.master.after(0, lambda: self.log("✅ 数据已显示在墙体点位信息区域"))
            
            self.log("=== 连接过程完成 ===")
    
    def receive_revit_data(self, client_socket):
        """接收Revit发送的墙体数据"""
        try:
            # 清空现有数据
            self.revit_data = []
            
            # 持续接收数据直到收到结束标记
            buffer = ""
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # 处理接收到的数据
                message = data.decode('utf-8')
                buffer += message
                
                # 处理结束标记
                if "DATA_END" in buffer:
                    # 提取DATA_END之前的数据
                    data_part = buffer.split("DATA_END")[0]
                    buffer = ""
                    
                    self.log("收到数据结束标记")
                    
                    # 处理数据部分
                    if data_part:
                        # 分割消息，处理可能的多个JSON对象
                        lines = data_part.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and "{" in line and "}" in line:
                                try:
                                    import json
                                    wall_data = json.loads(line)
                                    
                                    # 检查是否是有效的墙体数据
                                    if "id" in wall_data:
                                        self.revit_data.append(wall_data)
                                        wall_id = wall_data.get('id')
                                        brick_count = wall_data.get('brick_count', 0)
                                        bricks = wall_data.get('bricks', [])
                                        self.log(f"收到墙体数据: ID={wall_id}, 砖块数量={brick_count}")
                                        
                                        # 标记已接收到数据
                                        self.data_received = True
                                        
                                        # 显示砖块详细信息
                                        self.log(f"  墙体 {wall_id} 包含 {len(bricks)} 个砖块")
                                        for brick in bricks:
                                            brick_id = brick.get('id', '未知')
                                            brick_center = brick.get('center_point', [0, 0, 0])
                                            self.log(f"    砖块 {brick_id}: 中心=({brick_center[0]}, {brick_center[1]}, {brick_center[2]})")
                                except json.JSONDecodeError as e:
                                    self.log(f"解析JSON时出错: {e}")
                                    self.log(f"问题行: {line}")
                    
                    self.log(f"共收到 {len(self.revit_data)} 个墙体数据")
                    
                    # 检查是否有数据
                    if self.revit_data:
                        # 立即在主线程中显示数据到墙体点位信息区域
                        self.log("✅ 已成功接收一次Revit数据，正在显示到墙体点位信息区域...")
                        
                        # 强制在主线程中更新UI
                        def update_ui():
                            try:
                                self.display_revit_data()
                                self.log("✅ 数据已显示在墙体点位信息区域")
                                
                                # 记录第一个墙体的中心点坐标
                                if self.revit_data:
                                    first_wall = self.revit_data[0]
                                    center_point = first_wall.get('center_point', [0, 0, 0])
                                    self.log(f"第一个墙体中心点: ({int(center_point[0])}, {int(center_point[1])}, {int(center_point[2])})")
                            except Exception as e:
                                self.log(f"更新UI时出错: {e}")
                        
                        # 使用after(0)确保在主线程中执行
                        self.master.after(0, update_ui)
                    else:
                        self.log("⚠️ 未收到任何墙体数据")
                    
                    break
                        
        except Exception as e:
            self.log(f"接收数据时出错: {e}")
        finally:
            # 关闭连接
            client_socket.close()
            self.connected = False
            self.master.after(0, lambda: self.animate_status_change(False))
            self.master.after(0, lambda: self.status_label.configure(text="未连接"))
            self.master.after(0, lambda: self.log("与Revit的连接已关闭"))
    
    def display_revit_data(self):
        """显示从Revit接收的数据"""
        self.point_info_text.configure(state='normal')
        self.point_info_text.delete('1.0', tk.END)
        
        # 显示Revit数据标题
        self.point_info_text.insert(tk.END, "点位数据信息\n", "header")
        self.point_info_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # 收集所有砖块数据
        all_bricks = []
        for wall_data in self.revit_data:
            bricks = wall_data.get('bricks', [])
            all_bricks.extend(bricks)
        
        # 添加调试信息
        self.log(f"调试: self.revit_data长度={len(self.revit_data)}")
        self.log(f"调试: all_bricks长度={len(all_bricks)}")
        
        if not all_bricks:
            # 没有砖块数据的情况
            self.point_info_text.insert(tk.END, "⚠️ 未收到任何点位数据\n", "warning")
            self.point_info_text.insert(tk.END, "请确保：\n")
            self.point_info_text.insert(tk.END, "  1. Revit脚本已运行\n")
            self.point_info_text.insert(tk.END, "  2. 场景中有墙元素\n")
            self.point_info_text.insert(tk.END, "  3. Redis服务器已启动（作为备用）\n")
            
            # 配置警告样式
            self.point_info_text.tag_configure("warning", font=tkfont.Font(family="Microsoft YaHei UI", size=10, weight="bold"), foreground="#F44336")
        else:
            # 显示统计信息
            self.point_info_text.insert(tk.END, f"统计信息:\n", "subtitle")
            self.point_info_text.insert(tk.END, f"  总砖块数量: {len(all_bricks)}\n")
            self.point_info_text.insert(tk.END, "\n" + "-" * 60 + "\n\n")
            
            # 显示砖块的8个点坐标
            self.point_info_text.insert(tk.END, "砖块8个点坐标:\n", "brick_subtitle")
            
            # 每块砖块显示一行，包含8个点坐标
            for i, brick in enumerate(all_bricks):
                brick_id = brick.get('id', '未知')
                
                # 获取8个点坐标
                max_point = brick.get('max_point', [0, 0, 0])
                min_point = brick.get('min_point', [0, 0, 0])
                point3 = brick.get('point3', [0, 0, 0])
                point4 = brick.get('point4', [0, 0, 0])
                point5 = brick.get('point5', [0, 0, 0])
                point6 = brick.get('point6', [0, 0, 0])
                point7 = brick.get('point7', [0, 0, 0])
                point8 = brick.get('point8', [0, 0, 0])
                
                # 格式化8个点坐标
                coords_str = f"点1({int(max_point[0])},{int(max_point[1])},{int(max_point[2])}) 点2({int(min_point[0])},{int(min_point[1])},{int(min_point[2])}) 点3({int(point3[0])},{int(point3[1])},{int(point3[2])}) 点4({int(point4[0])},{int(point4[1])},{int(point4[2])}) 点5({int(point5[0])},{int(point5[1])},{int(point5[2])}) 点6({int(point6[0])},{int(point6[1])},{int(point6[2])}) 点7({int(point7[0])},{int(point7[1])},{int(point7[2])}) 点8({int(point8[0])},{int(point8[1])},{int(point8[2])})"
                
                # 检查是否是墙元素砖块
                if 'wall_' in brick_id:
                    brick_info = f"  [{i+1}] 墙元素砖块: {coords_str}\n"
                else:
                    brick_info = f"  [{i+1}] 砖块: {coords_str}\n"
                
                self.point_info_text.insert(tk.END, brick_info)
        
        # 配置文本样式
        self.point_info_text.tag_configure("header", font=tkfont.Font(family="Microsoft YaHei UI", size=12, weight="bold"), foreground="#1E88E5")
        self.point_info_text.tag_configure("subtitle", font=tkfont.Font(family="Microsoft YaHei UI", size=10, weight="bold"), foreground="#4CAF50")
        self.point_info_text.tag_configure("brick_subtitle", font=tkfont.Font(family="Microsoft YaHei UI", size=9, weight="bold"), foreground="#607D8B")
        
        # 设置文本对齐和间距
        self.point_info_text.tag_configure("left", justify=tk.LEFT)
        
        self.point_info_text.configure(state='disabled')
    
    def accept_connections(self):
        """接受客户端连接的线程函数"""
        self.running = True
        while self.running:
            try:
                self.server_socket.settimeout(1)  # 设置超时，以便能够响应停止信号
                client_socket, client_address = self.server_socket.accept()
                self.client_socket = client_socket
                self.connected = True
                
                # 在主线程中更新UI
                self.master.after(0, lambda: self.animate_status_change(True))
                self.master.after(0, lambda: self.status_label.configure(text="已连接"))
                self.master.after(0, lambda: self.start_btn.configure(state="normal"))
                self.master.after(0, lambda: self.log(f"RobotStudio已连接: {client_address}"))
                
                # 启动数据接收线程
                self.receive_thread = threading.Thread(target=self.receive_data)
                self.receive_thread.daemon = True
                self.receive_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.master.after(0, lambda e=e: self.log(f"接受连接错误: {str(e)}"))
                break
        
        # 确保资源被清理
        if hasattr(self, 'server_socket'):
            try:
                self.server_socket.close()
            except:
                pass

    def disconnect_tcp(self):
        """停止TCP服务器"""
        self.running = False  # 停止所有线程
        self.initial_handshake_done = False  # 重置
        
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            
        if hasattr(self, 'server_socket'):
            try:
                self.server_socket.close()
            except:
                pass
            
        self.connected = False
        
        # 更新UI
        self.animate_status_change(False)
        self.status_label.configure(text="未连接")
        self.connect_btn.configure(state="normal", text="启动服务器", command=self.connect_tcp)
        self.start_btn.configure(state="disabled")
        self.log("服务器已停止")
        messagebox.showinfo("服务器状态", "TCP服务器已停止")

    def receive_data(self):
        """接收数据的线程函数"""
        request_count = 0
        while self.running and self.client_socket:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    # 连接已断开
                    self.handle_disconnect()
                    break
                    
                # 处理接收到的数据
                try:
                    message = data.decode('utf-8')
                    
                    # 只在第一次收到"Hello server"时回复"Hello"，但不显示在日志中
                    if "Hello server" in message and not self.initial_handshake_done:
                        try:
                            self.client_socket.send("Hello\r\n".encode('utf-8'))
                            self.initial_handshake_done = True  # 标记握手已完成
                        except Exception as e:
                            self.log(f"回复消息错误: {str(e)}")
                    
                    # 处理机器人的READY请求
                    elif "READY" in message:
                        request_count += 1
                        self.log(f"收到机器人第{request_count}个READY请求")
                        
                        # 如果有砖块数据，发送坐标
                        if self.all_bricks:
                            brick = self.all_bricks[0]
                            # 模拟8个点坐标（这里使用固定值，实际应该从砖块数据中获取）
                            max_point = brick.get('max_point', [-40.2, 17.4, 0.7])
                            min_point = brick.get('min_point', [-41.5, 16.8, 0.0])
                            point3 = brick.get('point3', [-41.5, 17.4, 0.7])
                            point4 = brick.get('point4', [-40.2, 16.8, 0.7])
                            point5 = brick.get('point5', [-41.5, 16.8, 0.7])
                            point6 = brick.get('point6', [-41.5, 17.4, 0.0])
                            point7 = brick.get('point7', [-40.2, 17.4, 0.0])
                            point8 = brick.get('point8', [-40.2, 16.8, 0.0])
                            
                            # 创建一个包含所有8个点的列表
                            all_points = [max_point, min_point, point3, point4, point5, point6, point7, point8]
                            
                            # 根据请求次数发送对应的点（每次发送1个点）
                            point_index = request_count - 1  # 转换为0-based索引
                            if point_index < len(all_points):
                                point = all_points[point_index]
                                coord_data = f"{point[0]:.1f};{point[1]:.1f};{point[2]:.1f}"
                                self.log(f"发送第{request_count}个点坐标: {coord_data}")
                                
                                coord_bytes = coord_data.encode('utf-8')
                                self.client_socket.sendall(coord_bytes)
                                self.log(f"已发送第{request_count}个点坐标")
                            else:
                                # 如果请求超过8次，发送结束标记
                                self.log(f"所有8个点已发送完毕，发送结束标记")
                                self.client_socket.sendall(b"END")
                        else:
                            # 没有砖块数据，发送ACK确认
                            self.client_socket.sendall(b"ACK")
                            self.log("发送ACK确认（无砖块数据）")
                            
                except Exception as e:
                    self.log(f"处理数据错误: {str(e)}")
            except socket.timeout:
                continue
            except ConnectionResetError:
                self.handle_disconnect()
                break
            except Exception as e:
                if self.running:
                    self.master.after(0, lambda e=e: self.log(f"接收数据错误: {str(e)}"))
                break
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            finally:
                self.client_socket = None
                
        if self.connected:
            self.handle_disconnect()

    def handle_disconnect(self):
        if self.connected:
            self.connected = False
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
            
            # 在主线程中更新UI
            self.master.after(0, lambda: self.status_label.configure(text="未连接"))
            self.master.after(0, lambda: self.animate_status_change(False))
            self.master.after(0, lambda: self.start_btn.configure(state="disabled"))
            self.master.after(0, lambda: self.log("连接已断开"))
            self.master.after(0, lambda: self.connect_btn.configure(state="normal", text="启动服务器", command=self.connect_tcp))

    def animate_status_change(self, is_connected):
        """连接状态切换的渐变动画"""
        steps = 10
        start_color = self.error_color if is_connected else self.secondary_color
        end_color = self.secondary_color if is_connected else self.error_color
        
        # 解析颜色
        sr = int(start_color[1:3], 16)
        sg = int(start_color[3:5], 16)
        sb = int(start_color[5:7], 16)
        
        er = int(end_color[1:3], 16)
        eg = int(end_color[3:5], 16)
        eb = int(end_color[5:7], 16)
        
        # 计算每步变化量
        dr = (er - sr) / steps
        dg = (eg - sg) / steps
        db = (eb - sb) / steps
        
        def color_step(step):
            if step >= 0:
                r = int(sr + dr * (steps - step))
                g = int(sg + dg * (steps - step))
                b = int(sb + db * (steps - step))
                
                # 转换为16进制颜色
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.status_indicator.configure(bg=color)
                self.master.update_idletasks()
                
                self.master.after(30, lambda: color_step(step - 1))
            else:
                # 动画完成，更新文本
                self.status_label.configure(text="已连接" if is_connected else "未连接")
        
        color_step(steps - 1)
            
    def start_masonry(self):
        try:
            # 清除日志区域
            self.log_area.configure(state='normal')
            self.log_area.delete('1.0', tk.END)
            self.log_area.configure(state='disabled')
            
            # 获取其他参数
            wall_type = self.wall_type.get()
            layers = self.layers.get()
            interval = self.interval.get().replace("mm", "")  # 移除mm单位
            
            # 记录参数到日志
            self.log("开始砌筑任务...")
            self.log("参数设置：")
            self.log(f"墙类型: {wall_type}")
            self.log(f"层数: {layers}")
            self.log(f"间隔: {interval}mm")
            
            # 收集所有砖块数据
            self.all_bricks = []
            for wall_data in self.revit_data:
                bricks = wall_data.get('bricks', [])
                self.all_bricks.extend(bricks)
            
            # 输出砌筑方式和砖块数量
            self.log(f"砌筑方式为: {wall_type}")
            self.log(f"砖有 {len(self.all_bricks)} 块")
            
            # 启动Socket服务器发送数据
            import socket
            import threading
            
            def start_socket_server():
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('127.0.0.1', 8080))
                server_socket.listen(1)
                self.log("Socket服务器已启动，等待机器人连接...")
                
                try:
                    while True:
                        client_socket, addr = server_socket.accept()
                        self.log(f"机器人已连接: {addr}")
                        
                        # 保持连接打开，持续通信
                        try:
                            self.log("等待接收握手消息...")
                            # 接收握手消息
                            handshake_data = client_socket.recv(1024)
                            self.log(f"收到原始数据: {handshake_data}")
                            handshake = handshake_data.decode('utf-8')
                            self.log(f"收到握手消息: '{handshake}'")
                            
                            # 立即发送握手响应
                            response = b"Hello client"
                            client_socket.sendall(response)
                            self.log(f"已发送握手响应: '{response.decode()}'")
                            
                            # 持续循环处理机器人的请求
                            request_count = 0
                            while True:
                                request_count += 1
                                self.log(f"等待机器人第{request_count}个请求...")
                                # 等待机器人发送READY请求
                                try:
                                    client_socket.settimeout(10.0)
                                    request_data = client_socket.recv(1024)
                                    if not request_data:
                                        self.log("收到空数据，连接可能已关闭")
                                        break
                                    request = request_data.decode('utf-8')
                                    self.log(f"收到机器人请求: '{request}'")
                                except socket.timeout:
                                    self.log("等待机器人请求超时")
                                    break
                                except Exception as e:
                                    self.log(f"接收请求错误: {e}")
                                    break
                                
                                # 如果收到READY请求，发送坐标数据
                                if "READY" in request and self.all_bricks:
                                    brick = self.all_bricks[0]
                                    # 获取8个点坐标
                                    max_point = brick.get('max_point', [0, 0, 0])
                                    min_point = brick.get('min_point', [0, 0, 0])
                                    point3 = brick.get('point3', [0, 0, 0])
                                    point4 = brick.get('point4', [0, 0, 0])
                                    point5 = brick.get('point5', [0, 0, 0])
                                    point6 = brick.get('point6', [0, 0, 0])
                                    point7 = brick.get('point7', [0, 0, 0])
                                    point8 = brick.get('point8', [0, 0, 0])
                                    
                                    # 创建一个包含前4个点的列表
                                    all_points = [max_point, min_point, point3, point4]
                                    
                                    # 根据请求次数发送对应的点（每次发送1个点）
                                    point_index = request_count - 1  # 转换为0-based索引
                                    if point_index < len(all_points):
                                        point = all_points[point_index]
                                        coord_data = f"{point[0]:.1f};{point[1]:.1f};{point[2]:.1f}"
                                        self.log(f"发送第{request_count}个点坐标: {coord_data}")
                                        
                                        coord_bytes = coord_data.encode('utf-8')
                                        client_socket.sendall(coord_bytes)
                                        self.log(f"已发送第{request_count}个点坐标")
                                    else:
                                        # 如果请求超过4次，发送结束标记
                                        self.log(f"所有4个点已发送完毕，发送结束标记")
                                        client_socket.sendall(b"END")
                                        break
                                else:
                                    # 其他请求，发送确认
                                    client_socket.sendall(b"ACK")
                                    self.log("发送ACK确认")
                        except Exception as e:
                            self.log(f"通信错误: {e}")
                            import traceback
                            self.log(traceback.format_exc())
                        finally:
                            client_socket.close()
                            self.log("连接已关闭")
                            break
                except Exception as e:
                    self.log(f"Socket服务器错误: {e}")
                finally:
                    server_socket.close()
            
            # 启动Socket服务器线程
            server_thread = threading.Thread(target=start_socket_server)
            server_thread.daemon = True
            server_thread.start()
            
            self.log(f"✅ 已启动Socket服务器")
            self.log(f"总砖块数: {len(self.all_bricks)}")
            self.log("等待机器人连接...")
            
        except Exception as e:
            messagebox.showerror("发送错误", f"发送参数失败: {str(e)}")
            self.log(f"发送错误: {str(e)}")
            self.start_btn.configure(state="normal")

    def log(self, message):
        """添加日志信息"""
        self.log_area.configure(state='normal')
        
        # 添加时间戳前缀
        import datetime
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        
        # 根据消息类型添加不同颜色
        if "错误" in message or "失败" in message:
            self.log_area.tag_configure("error", foreground=self.error_color)
            self.log_area.insert(tk.END, timestamp, "timestamp")
            self.log_area.insert(tk.END, message + "\n", "error")
        elif "成功" in message:
            self.log_area.tag_configure("success", foreground=self.secondary_color)
            self.log_area.insert(tk.END, timestamp, "timestamp")
            self.log_area.insert(tk.END, message + "\n", "success")
        elif "正在" in message:
            self.log_area.tag_configure("progress", foreground="#FF9800")
            self.log_area.insert(tk.END, timestamp, "timestamp")
            self.log_area.insert(tk.END, message + "\n", "progress")
        else:
            self.log_area.tag_configure("info", foreground="#333333")
            self.log_area.tag_configure("timestamp", foreground="#666666")
            self.log_area.insert(tk.END, timestamp, "timestamp")
            self.log_area.insert(tk.END, message + "\n", "info")
            
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = IntelligentMasonrySystem(root)
    root.mainloop()
    