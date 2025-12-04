import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
from PIL import Image
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import platform
import datetime

class ImageBatchConverter:
    def __init__(self, root):
        self.root = root
        self.root.title(" 多格式图片批量转换器 for dingla")
        self.root.geometry("800x800")  # 调整窗口大小以容纳更多列
        
        # 存储文件路径和输出目录
        self.input_paths = []
        self.output_dir_var = tk.StringVar()
        
        # 支持的图片格式
        self.supported_exts = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp']

        # 图片转换选项变量
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.keep_aspect_var = tk.BooleanVar(value=True)
        self.is_percent_unit = tk.BooleanVar(value=False)
        self.quality_var = tk.IntVar(value=90)
        self.rename_mode_var = tk.StringVar(value="自动重命名")
        
        # 存储文件的元数据
        self.file_metadata = {}
        # 文件列表树需要的格式：字段名、header显示名、宽度
        self.tree_column =[['filename', "文件名", 260], ['size',"大小",80], 
                            ['resolution',"分辨率", 100], ['modified_time',"修改时间",80]]
        
        # 创建 GUI
        self.create_widgets()

        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🔄 多格式图片批量转换器", bootstyle=PRIMARY,
                                font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Notebook 用于多标签页
        self.notebook = ttk.Notebook(main_frame,bootstyle=SECONDARY)
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # 创建标签页
        self.input_tab = ttk.Frame(self.notebook, padding=10)
        self.options_tab = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.input_tab, text="📁 输入设置")
        self.notebook.add(self.options_tab, text="⚒️ 输出选项")
        
        # 创建各个标签页的内容
        self.create_input_tab(self.input_tab)
        self.create_options_tab(self.options_tab)
        
        
        # 命令框架
        command_frame = ttk.Frame(main_frame)
        command_frame.pack(fill=tk.X, pady=(0, 10))
        for i in range(2):   
            command_frame.columnconfigure(i, weight=2)
        command_frame.columnconfigure(2, weight=1)  

        open_dir_button = ttk.Button(command_frame, text="📂 打开输出目录", width=18,
                                    command=self.open_output_dir, bootstyle=WARNING)
        open_dir_button.grid(row=0, column=0, sticky="ew", padx=(5,10))
            
        self.convert_button = ttk.Button(command_frame, text="🍭 开始转换", width=18,
                                        command=self.start_conversion, bootstyle=SUCCESS)
        self.convert_button.grid(row=0, column=1, sticky="ew", padx=10)
        
        clear_log_button = ttk.Button(command_frame, text="🗑️ 清空日志", width=9,
                                    command=self.clear_log, bootstyle=SECONDARY)
        clear_log_button.grid(row=0, column=2, sticky="ew", padx=(10,15))
        
        # 进度和日志框架 (保留在主框架中)
        progress_frame = ttk.Labelframe(main_frame, text="进度与日志", bootstyle=INFO, padding=10)
        progress_frame.pack(fill=BOTH, expand=True, pady=(0, 0))
        
        # 日志文本框
        log_container = ttk.Frame(progress_frame)
        log_container.pack(fill=BOTH, expand=True)
        
        self.log_text = ScrolledText(log_container, height=4, font=("Consolas", 9))
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        
        # 状态栏 (保留在主框架中)
        status_frame = ttk.Frame(self.root, padding=(10, 5))
        status_frame.pack(fill=X, side=BOTTOM)

        self.status_label = ttk.Label(status_frame, text=f"就绪", anchor="w", bootstyle=INFO)
        self.status_label.pack(side=LEFT, pady=(0, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100, bootstyle=SUCCESS)
        self.progress_bar.pack(side=RIGHT, fill=tk.X, expand=True, padx=(5,0), pady=(0, 0))

    def create_input_tab(self, parent):
        
        # 选择按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 10))
        for i in range(2):   
            button_frame.columnconfigure(i, weight=2)  
        button_frame.columnconfigure(2, weight=1)  

        
        file_button = ttk.Button(button_frame, text="🎬 选择图片", bootstyle=INFO,width=18,
                                command=self.select_files)
        file_button.grid(row=0, column=0, sticky="ew",padx=(0,10))
        
        folder_button = ttk.Button(button_frame, text="📂 选择目录", bootstyle=PRIMARY,width=18,
                                command=self.select_folder)
        folder_button.grid(row=0, column=1, sticky="ew", padx=(10,10))
        
        clear_button = ttk.Button(button_frame, text="🧹 清除选择",bootstyle=SECONDARY,width=9,
                                command=self.clear_selection)
        clear_button.grid(row=0, column=2, sticky="ew",padx=(10,0))

        
        # 过滤和文件列表部分
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=BOTH, expand=True, pady=(10, 10))
        
        # 文件列表标签和计数
        list_header_frame = ttk.Frame(list_frame)
        list_header_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Label(list_header_frame, text="选择的文件:").pack(side=LEFT)
        self.file_count_label = ttk.Label(list_header_frame, bootstyle=INFO, text="(0 个文件)")
        self.file_count_label.pack(side=LEFT, padx=(10, 0))

        # 格式过滤
        self.filter_var = tk.StringVar(value="所有图片")
        self.filter_combo = ttk.Combobox(list_header_frame, textvariable=self.filter_var, bootstyle=PRIMARY,
                                        values=["所有图片", "仅TIFF文件", "仅PNG文件", "仅JPEG文件", "仅BMP文件", "仅GIF文件", "仅WEBP文件"],
                                        state="readonly", width=10)
        self.filter_combo.pack(side=RIGHT)      
        ttk.Label(list_header_frame, text="格式过滤:").pack(side=RIGHT, padx=(20, 5))

        # 递归选项
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_check = ttk.Checkbutton(list_header_frame, text="递归搜索", 
                                        variable=self.recursive_var, bootstyle=INFO)
        recursive_check.pack(side=RIGHT, padx=10)
        
        # Treeview
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=BOTH, expand=True)

        cols = [filename for filename,_,_ in self.tree_column]
        self.file_list_tree = ttk.Treeview(
            list_container, 
            columns=cols, 
            show='headings',
            selectmode='extended',
            height=3
        )

        for filename,text,width in self.tree_column:
            self.file_list_tree.heading(filename, text=text, anchor=W)
            self.file_list_tree.column(filename, width=width, anchor=W)
        
        self.file_list_tree.pack(side=LEFT, fill=BOTH, expand=True)
        
        # 绑定双击事件 (删除文件)
        self.file_list_tree.bind('<Double-1>', self.remove_selected_item)
        
        # 滚动条
        list_scroll = ttk.Scrollbar(list_container, orient="vertical", command=self.file_list_tree.yview)
        list_scroll.pack(side=RIGHT, fill=Y)
        self.file_list_tree.configure(yscrollcommand=list_scroll.set)
        
        # 绑定过滤事件
        self.filter_combo.bind("<<ComboboxSelected>>", lambda event: self.refresh_filtered_list())


    def create_options_tab(self, parent):
        output_frame = ttk.Labelframe(parent, text="输出设置", bootstyle=INFO, padding=10)
        output_frame.pack(fill=X, pady=10)
        
        # 输出目录选择
        output_dir_frame = ttk.Frame(output_frame)
        output_dir_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(output_dir_frame, text="输出目录:").pack(side=LEFT)
        
        output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.output_dir_var)
        output_dir_entry.pack(side=LEFT, padx=(10, 0), fill=X, expand=True)
        
        select_dir_button = ttk.Button(output_dir_frame, text="🔍 浏览", bootstyle=SUCCESS,width=10, 
                                        command=self.select_output_dir)
        select_dir_button.pack(side=LEFT, padx=(10, 0))
        
        # 重名处理选项
        rename_frame = ttk.Frame(output_frame)
        rename_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Label(rename_frame, text="重名文件处理:").grid(row=0,column=0,sticky="w", padx=(0, 10))
        rename_combo = ttk.Combobox(rename_frame, textvariable=self.rename_mode_var,
                                    values=["自动重命名", "覆盖现有文件", "跳过重名文件"],
                                    state="readonly", width=18)
        rename_combo.grid(row=0,column=1,sticky="w", padx=(0, 10))
        rename_frame.columnconfigure(1, weight=1)


        options_frame = ttk.Labelframe(parent, text="转换选项", bootstyle=PRIMARY, padding=10)
        options_frame.pack(fill=X, pady=10)
        
        # 尺寸设置
        size_frame = ttk.Frame(options_frame)
        size_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(size_frame, text="输出尺寸:").pack(side=LEFT)
        
        size_subframe = ttk.Frame(size_frame)
        size_subframe.pack(side=LEFT, padx=(10, 0))
        
        ttk.Label(size_subframe, text="宽度:").pack(side=LEFT, padx=(10, 0))
        width_entry = ttk.Entry(size_subframe, textvariable=self.width_var, width=8)
        width_entry.pack(side=LEFT, padx=(10, 0))
        self.width_value_label = ttk.Label(size_subframe, text="px")
        self.width_value_label.pack(side=LEFT, padx=(0, 5))
        
        ttk.Label(size_subframe, text="高度:").pack(side=LEFT, padx=(10, 0))
        height_entry = ttk.Entry(size_subframe, textvariable=self.height_var, width=8)
        height_entry.pack(side=LEFT, padx=(10, 0))
        self.height_value_label = ttk.Label(size_subframe, text="px",width=3)
        self.height_value_label.pack(side=LEFT, padx=(0, 5))

        unit_check = ttk.Checkbutton(size_frame, text="百分比单位", 
                                            variable=self.is_percent_unit,command=self.set_image_unit, bootstyle=INFO)
        unit_check.pack(side=LEFT, padx=(20, 0))
        
        keep_aspect_check = ttk.Checkbutton(size_frame, text="保持宽高比", 
                                            variable=self.keep_aspect_var, bootstyle=INFO)
        keep_aspect_check.pack(side=LEFT, padx=(20, 0))
        
        # 质量设置
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(quality_frame, text="JPEG 质量:").pack(side=LEFT)        
        quality_scale = ttk.Scale(quality_frame, from_=1, to=100, 
                                variable=self.quality_var, orient=HORIZONTAL, bootstyle=WARNING)
        quality_scale.pack(side=LEFT, padx=(10, 10), fill=X, expand=True)
        
        self.quality_value_label = ttk.Label(quality_frame, text="90")
        self.quality_value_label.pack(side=RIGHT)
        
        quality_scale.configure(command=self.update_quality_label)

    # 改变图片单位
    def set_image_unit(self):
        if self.is_percent_unit.get():
            self.width_value_label.configure(text="% ")
            self.height_value_label.configure(text="% ")
        else:
            self.width_value_label.configure(text="px")
            self.height_value_label.configure(text="px")
        

    def get_file_metadata(self, path):
        """获取文件大小、分辨率和修改时间"""
        
        filename = os.path.basename(path)
        
        # 1. 文件大小
        try:
            size_bytes = os.path.getsize(path)
            size = self.format_bytes(size_bytes)
        except OSError:
            size = "N/A"

        # 2. 修改时间
        try:
            timestamp = os.path.getmtime(path)
            # metadata['modified_time'] = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            modified_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except OSError:
            modified_time = "N/A"

        # 3. 分辨率
        resolution = "N/A"
        if path.lower().endswith(tuple(self.supported_exts)):
            try:
                with Image.open(path) as img:
                    width, height = img.size
                    resolution = f"{width}x{height}"
            except Exception:
                pass 

        return filename, size, resolution, modified_time

    def format_bytes(self, size):
        """格式化文件大小为 KB, MB, GB"""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while size > 1024 and i < len(units) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.2f} {units[i]}"
        
    def get_extensions(self):
        """根据过滤模式获取支持的扩展名列表"""
        mode = self.filter_var.get()
        if mode == "所有图片":
            return self.supported_exts
        elif mode == "仅TIFF文件":
            return ['.tif', '.tiff']
        elif mode == "仅PNG文件":
            return ['.png']
        elif mode == "仅JPEG文件":
            return ['.jpg', '.jpeg']
        elif mode == "仅BMP文件":
            return ['.bmp']
        elif mode == "仅GIF文件":
            return ['.gif']
        elif mode == "仅WEBP文件":
            return ['.webp']
        else:
            return self.supported_exts
    
    def add_paths(self, paths):
        """添加路径，去重并排序，并收集元数据"""
        added_count = 0
        seen = set(self.input_paths)
        
        new_paths = []
        for path in paths:
            if path not in seen:
                new_paths.append(path)
                seen.add(path)
        
        if new_paths:
            # 收集元数据
            for path in new_paths:
                metadata = self.get_file_metadata(path)
                self.file_metadata[path] = metadata
            
            # 添加到主列表并排序
            self.input_paths.extend(new_paths)
            self.input_paths.sort(key=lambda x: os.path.basename(x).lower())
            added_count = len(new_paths)
            self.update_file_list()
        return added_count
    
    def get_image_files(self, folder):
        """获取文件夹中的图片文件，支持递归选项和格式过滤"""
        image_files = []
        exts = tuple(self.get_extensions())
        if self.recursive_var.get():
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(exts):
                        image_files.append(os.path.join(root, file))
        else:
            try:
                for file in os.listdir(folder):
                    if file.lower().endswith(exts):
                        image_files.append(os.path.join(folder, file))
            except PermissionError:
                pass
        return image_files
    
    def select_files(self):
        """选择多个图片文件"""
        exts = self.get_extensions()
        patterns = " ".join(f"*{ext}" for ext in exts)
        filetypes = [("图片文件", patterns), ("所有文件", "*.*")]
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=filetypes
        )
        if files:
            filtered_files = [f for f in files if f.lower().endswith(tuple(exts))]
            added = self.add_paths(filtered_files)
            if added > 0:
                self.log_message(f"[信息] 添加了 {added} 个图片文件")
    
    def select_folder(self):
        """选择包含图片文件的文件夹"""
        folder = filedialog.askdirectory(title="选择包含图片文件的文件夹")
        if folder:
            image_files = self.get_image_files(folder)
            filter_desc = self.filter_var.get().replace("仅", "")
            if image_files:
                added = self.add_paths(image_files)
                mode = "递归目录" if self.recursive_var.get() else "当前文件夹"
                self.log_message(f"[信息] 从 {mode} '{os.path.basename(folder)}' 中添加了 {added} 个 {filter_desc}")
            else:
                self.log_message(f"[警告] 所选文件夹中没有找到 {filter_desc} ！")

    def refresh_filtered_list(self):
        """根据新的过滤设置刷新列表显示（仅重新渲染，不改变 input_paths）"""
        self.update_file_list()
        self.log_message(f"[信息] 列表已按 '{self.filter_var.get()}' 过滤刷新。")

    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)
    
    def open_output_dir(self):
        """打开输出目录 (保留在主框架中)"""
        output_dir = self.output_dir_var.get()
        if not output_dir:
            # 如果没有设置输出目录，尝试打开第一个输入文件的目录
            if self.input_paths:
                default_dir = os.path.dirname(self.input_paths[0])
                if os.path.isdir(default_dir):
                    output_dir = default_dir
                    self.output_dir_var.set(default_dir)
                    self.log_message(f"[信息] 使用默认目录: {default_dir}")
                else:
                    messagebox.showwarning("警告", "请先选择输出目录或确保输入文件存在")
                    return
            else:
                messagebox.showwarning("警告", "请先选择输出目录")
                return
                
        if not os.path.exists(output_dir):
            messagebox.showwarning("警告", "输出目录不存在")
            return
            
        try:
            if platform.system() == 'Windows':
                os.startfile(output_dir)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{output_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{output_dir}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {str(e)}")
    
    def clear_selection(self):
        """清除所有选择的文件"""
        self.input_paths.clear()
        self.file_metadata.clear()
        self.update_file_list()
        self.log_message("[信息] 已清除所有文件选择")
    
    def remove_selected_item(self, event):
        """双击移除选中的文件"""
        selected_item = self.file_list_tree.selection()
        if selected_item:
            item_id = selected_item[0]
            item_values = self.file_list_tree.item(item_id, 'values')
            
            if item_values:
                filename_to_remove = item_values[0]
                
                # 查找对应的文件路径 (基于文件名匹配，注意重名问题)
                path_to_remove = None
                for path in self.input_paths:
                    if os.path.basename(path) == filename_to_remove:
                        # 更好的匹配方式是依赖 IID 如果它存储了路径，但这里我们简化处理
                        path_to_remove = path
                        break

                if path_to_remove and path_to_remove in self.input_paths:
                    self.input_paths.remove(path_to_remove)
                    if path_to_remove in self.file_metadata:
                        del self.file_metadata[path_to_remove]
                    
                    self.file_list_tree.delete(item_id)
                    self.log_message(f"[信息] 已从列表中移除: {filename_to_remove}")
        
        self.update_file_count()

    def update_file_count(self):
        count = len(self.input_paths)
        self.file_count_label.config(text=f"({count} 个文件)")


    def update_file_list(self):
        """更新文件列表 Treeview"""
        # 清空现有内容
        for i in self.file_list_tree.get_children():
            self.file_list_tree.delete(i)
        
        # 根据扩展名筛选并更新数据
        exts_to_show = self.get_extensions()
        temp_paths = [path for path in self.input_paths if path.lower().endswith(tuple(exts_to_show))]
        self.input_paths[:] = temp_paths

        # 重新插入数据
        for path in self.input_paths:               
            values = self.get_file_metadata(path)
            self.file_list_tree.insert('', tk.END, iid=path, 
                                        values=values)
        self.update_file_count()
    
    def update_quality_label(self, value):
        """更新质量值标签"""
        self.quality_value_label.config(text=str(int(float(value))))
    
    def clear_log(self):
        """清空日志 (保留在主框架中)"""
        self.log_text.delete(1.0, tk.END)
    
    def log_message(self, message):
        """添加消息到日志 (保留在主框架中)"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, text):
        """更新状态标签 (保留在主框架中)"""
        self.status_label.config(text=text)
        self.root.update_idletasks()
    
    def start_conversion(self):
        """开始转换过程 (保留在主框架中)"""
        if not self.input_paths:
            messagebox.showwarning("警告", "请先选择要转换的图片文件或文件夹")
            return
        
        if not self.output_dir_var.get():
            directory = os.path.dirname(self.input_paths[0])
            self.output_dir_var.set(directory)
            self.log_message(f"[警告] 未选择输出目录，结果将保存在输入文件的目录：{directory}")
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir_var.get()):
            try:
                os.makedirs(self.output_dir_var.get())
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出目录: {str(e)}")
                return
        
        # 禁用转换按钮，防止重复点击
        self.convert_button.config(state=DISABLED)
        self.update_status("转换中...")
        
        # 在新线程中执行转换
        thread = threading.Thread(target=self.convert_images, daemon=True)
        thread.start()
    
    def convert_images(self):
        """转换所有选中的图片为 JPG"""
        total_files = len(self.input_paths)
        converted_count = 0
        failed_count = 0
        skipped_count = 0
        
        self.log_message(f"[信息] 开始转换 {total_files} 个图片文件...")
        self.log_message(f"[信息] 重名处理模式: {self.rename_mode_var.get()}")
        self.progress_var.set(0)
        
        for i, input_path in enumerate(self.input_paths):
            try:
                # 更新进度
                progress = ((i + 1) / total_files) * 100
                self.progress_var.set(progress)
                self.update_status(f"处理中... ({i+1}/{total_files})")
                
                # 打开图像
                with Image.open(input_path) as img:
                    # 检查多页
                    if hasattr(img, 'n_frames') and img.n_frames > 1:
                        self.log_message(f"[警告] {os.path.basename(input_path)} 是多页图像 (共 {img.n_frames} 页)，仅转换第一页")
                    
                    # 转换为 RGB 模式（如果必要，特别是对于 GIF/TIFF 等）
                    img = img.convert('RGB')                           
                    
                    original_width, original_height = img.size
                    width_str = self.width_var.get().strip()
                    height_str = self.height_var.get().strip()
                    
                    new_width = original_width
                    new_height = original_height
                    resize_needed = False

                    # 1. 解析和计算目标尺寸 (基于百分比或像素)
                    try:
                        is_percent = self.is_percent_unit.get()
                        
                        target_w = None
                        target_h = None
                        # --- 解析输入 ---
                        if width_str:
                            val = int(width_str)
                            if val > 0:
                                if is_percent:  # 像素
                                    target_w = int(original_width * (val / 100.0))
                                else:
                                    target_w = int(val)
                            else: 
                                raise ValueError("宽度像素值必须大于 0。")

                                    
                        if height_str:
                            val = float(height_str)
                            if val > 0:
                                if is_percent: # 像素
                                    target_h = int(original_height * (val / 100.0))
                                else:
                                    target_h = int(val)
                            else: 
                                raise ValueError("高度像素值必须大于 0。")
                            
                        # --- 确定最终尺寸 (处理只输入了一个值的情况) ---
                        if target_w is not None or target_h is not None:
                            resize_needed = True

                            # 保持宽高比逻辑 (优先级最高)
                            if self.keep_aspect_var.get():
                                if target_w is not None and target_h is None:
                                    # 只指定了宽度，按宽度计算高度
                                    ratio = target_w / original_width
                                    new_width = target_w
                                    new_height = int(original_height * ratio)
                                elif target_h is not None and target_w is None:
                                    # 只指定了高度，按高度计算宽度
                                    ratio = target_h / original_height
                                    new_height = target_h
                                    new_width = int(original_width * ratio)
                                elif target_w is not None and target_h is not None:
                                    # 两个都指定了，取最小的缩放比例来保证不超出任何一个限制
                                    ratio_w = target_w / original_width
                                    ratio_h = target_h / original_height
                                    ratio = min(ratio_w, ratio_h)
                                    
                                    new_width = int(original_width * ratio)
                                    new_height = int(original_height * ratio)
                            
                            # 不保持宽高比 (或在保持宽高比后，如果两个都指定了，则按指定尺寸)
                            else:
                                if target_w is not None:
                                    new_width = target_w
                                if target_h is not None:
                                    new_height = target_h
                                    
                    except Exception as e:
                        self.log_message(f"[错误] 处理尺寸时发生未知错误 - {os.path.basename(input_path)}: {e}")
                        failed_count += 1
                        continue
                    # 2. 调整尺寸
                    if resize_needed and (new_width != original_width or new_height != original_height):
                        # 确保尺寸大于0
                        if new_width <= 0 or new_height <= 0:
                            self.log_message(f"[警告] 计算的尺寸无效 (W:{new_width}, H:{new_height})，跳过缩放 - {os.path.basename(input_path)}")
                        else:
                            try:
                                # 调整图像尺寸 (使用 LANCZOS 滤镜以获得高质量缩放)
                                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                self.log_message(f"[信息] 成功缩放 {os.path.basename(input_path)} 到 {new_width}x{new_height}")
                            except Exception as e:
                                self.log_message(f"[错误] 无法调整图像尺寸 - {os.path.basename(input_path)}: {e}")
                                failed_count += 1
                                continue
                    else:
                        self.log_message(f"[信息] 未指定尺寸变化或尺寸保持不变 - {os.path.basename(input_path)}")
                    
                    # 生成输出文件名
                    base_name = os.path.splitext(os.path.basename(input_path))[0]
                    output_filename = f"{base_name}.jpg"
                    output_path = os.path.join(self.output_dir_var.get(), output_filename)
                    
                    # 重名处理逻辑
                    rename_mode = self.rename_mode_var.get()
                    if rename_mode == "跳过重名文件":
                        if os.path.exists(output_path):
                            self.log_message(f"[信息] ⏭ 跳过重名文件: {os.path.basename(input_path)} -> {output_filename}")
                            skipped_count += 1
                            continue
                    
                    elif rename_mode == "自动重命名":
                        counter = 1
                        while os.path.exists(output_path):
                            stem = os.path.splitext(output_filename)[0]
                            output_filename = f"{stem}_{counter}.jpg"
                            output_path = os.path.join(self.output_dir_var.get(), output_filename)
                            counter += 1
                    
                    # elif rename_mode == "覆盖现有文件": 直接使用 output_path
                    
                    # 保存为 JPG
                    img.save(output_path, "JPEG", quality=self.quality_var.get())
                    
                    converted_count += 1
                    self.log_message(f"[信息] ✓ {os.path.basename(input_path)} -> {output_filename}")
            
            except Exception as e:
                failed_count += 1
                self.log_message(f"[警告] ✗ {os.path.basename(input_path)} - {str(e)}")
        
        
        # 完成
        self.progress_var.set(100)
        self.update_status("转换完成")
        
        # 显示结果摘要
        total = converted_count + failed_count + skipped_count
        self.log_message(f"[信息] === 转换完成! 成功: {converted_count}, 失败: {failed_count}, 跳过: {skipped_count}, 总计: {total} ===")
        
        # 重新启用转换按钮
        self.convert_button.config(state=NORMAL)
        
        if failed_count == 0 and skipped_count == 0:
            messagebox.showinfo("完成", f"所有 {total} 个文件已成功转换!")
        else:
            msg = f"转换完成!\n成功: {converted_count}\n失败: {failed_count}\n跳过: {skipped_count}\n总计: {total}"
            messagebox.showinfo("完成", msg)

def main():
    # 使用 ttkbootstrap 的 Window 作为根窗口
    # root = ttk.Window(themename="cosmo")
    # root = ttk.Window(themename="yeti")
    root = ttk.Window(themename="flatly")
    
    app = ImageBatchConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
