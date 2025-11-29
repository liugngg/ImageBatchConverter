import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
from PIL import Image
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import platform

class ImageBatchConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("🔄 多格式图片批量转换器 for dingla")
        self.root.geometry("1020x1100")
        
        # 存储文件路径和输出目录
        self.input_paths = []
        self.output_dir = ""
        
        # 支持的图片格式
        self.supported_exts = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp']

        # 图片宽度/高度/质量/重命名模式
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.keep_aspect_var = tk.BooleanVar(value=True)
        self.quality_var = tk.IntVar(value=90)
        self.rename_mode_var = tk.StringVar(value="自动重命名")
        
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
        
        # 选择文件/文件夹部分
        selection_frame = ttk.Labelframe(main_frame, text="1.选择输入", bootstyle=SUCCESS, padding=10)
        selection_frame.pack(fill=X, pady=(0, 10))
        
        # 选择按钮框架
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(expand=True, pady=(0, 10))
        
        # 文件选择按钮
        file_button = ttk.Button(button_frame, text="🎬 选择图片文件", bootstyle=INFO,
                                command=self.select_files, width=20)
        file_button.pack(side=LEFT, padx=10)
        
        # 文件夹选择按钮
        folder_button = ttk.Button(button_frame, text="📂 选择文件夹", 
                                command=self.select_folder, width=20)
        folder_button.pack(side=LEFT, padx=10)
        
        # 清除选择按钮
        clear_button = ttk.Button(button_frame, bootstyle=SECONDARY, text="🧹 清除选择", 
                                command=self.clear_selection, width=20)
        clear_button.pack(side=LEFT, padx=10)        

        
        # 文件列表框架
        list_frame = ttk.Frame(selection_frame)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
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
                                        state="readonly", width=12)
        self.filter_combo.pack(side=RIGHT)      

        ttk.Label(list_header_frame, text="格式过滤:").pack(side=RIGHT, padx=(20, 5))

        # 递归选项
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_check = ttk.Checkbutton(list_header_frame, text="递归搜索子文件夹", 
                                        variable=self.recursive_var, bootstyle=INFO)
        recursive_check.pack(side=RIGHT, padx=20)      

        
        # 文件列表框和滚动条 
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(list_container, height=6, font=("Consolas", 9))
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.file_listbox.bind('<Double-Button-1>', self.remove_selected_file)
        
        list_scroll = ttk.Scrollbar(list_container, command=self.file_listbox.yview)
        list_scroll.pack(side=RIGHT, fill=Y)
        self.file_listbox.config(yscrollcommand=list_scroll.set)
        
        # 输出目录选择
        output_frame = ttk.Labelframe(main_frame, text="2.输出设置", bootstyle=INFO, padding=10)
        output_frame.pack(fill=X, pady=(0, 10))
        
        output_dir_frame = ttk.Frame(output_frame)
        output_dir_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(output_dir_frame, text="输出目录:").pack(side=LEFT)
        
        self.output_dir_var = tk.StringVar()
        output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.output_dir_var)
        output_dir_entry.pack(side=LEFT, padx=(10, 0), fill=X, expand=True)
        
    
        # 重名处理选项
        rename_frame = ttk.Frame(output_frame)
        rename_frame.pack(fill=X, pady=(10, 0))
        ttk.Label(rename_frame, text="重名文件:").pack(side=LEFT, padx=(0, 5))
        rename_combo = ttk.Combobox(rename_frame, textvariable=self.rename_mode_var,
                                    values=["自动重命名", "覆盖现有文件", "跳过重名文件"],
                                    state="readonly", width=15)
        rename_combo.pack(side=LEFT,padx=5)

        output_dir_button = ttk.Button(rename_frame, text="🔍 浏览", bootstyle=SUCCESS, 
                                    command=self.select_output_dir, width=20)
        output_dir_button.pack(side=RIGHT, padx=(0,10), pady=(0, 10))
        
        # 转换选项
        options_frame = ttk.Labelframe(main_frame, text="3.转换", bootstyle=PRIMARY, padding=10)
        options_frame.pack(fill=X, pady=(0, 10))
        
        # 尺寸设置
        size_frame = ttk.Frame(options_frame)
        size_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(size_frame, text="输出尺寸:").pack(side=LEFT)
        
        # 宽度和高度输入
        size_subframe = ttk.Frame(size_frame)
        size_subframe.pack(side=LEFT, padx=(10, 0))
        
        ttk.Label(size_subframe, text="宽度:").grid(row=0, column=0, padx=(0, 5), sticky="e")
        width_entry = ttk.Entry(size_subframe, textvariable=self.width_var, width=8)
        width_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(size_subframe, text="高度:").grid(row=0, column=2, padx=(0, 5), sticky="e")
        height_entry = ttk.Entry(size_subframe, textvariable=self.height_var, width=8)
        height_entry.grid(row=0, column=3, padx=(0, 10))
        
        # 保持宽高比复选框
        keep_aspect_check = ttk.Checkbutton(size_frame, text="保持宽高比", 
                                            variable=self.keep_aspect_var)
        keep_aspect_check.pack(side=LEFT, padx=(20, 0))
        
        # 质量设置
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(quality_frame, text="JPEG 质量:").pack(side=LEFT)        
        quality_scale = ttk.Scale(quality_frame, from_=1, to=100, 
                                variable=self.quality_var, orient=HORIZONTAL, bootstyle=WARNING)
        quality_scale.pack(side=LEFT, padx=(10, 10), fill=X, expand=True)
        
        self.quality_value_label = ttk.Label(quality_frame, text="90")
        self.quality_value_label.pack(side=RIGHT)
        
        # 绑定质量滑块值变化事件
        quality_scale.configure(command=self.update_quality_label)
        
        # 按钮框架
        command_frame = ttk.Frame(options_frame)
        command_frame.pack(pady=(0, 10))
        
        # 打开输出目录按钮
        open_dir_button = ttk.Button(command_frame, text="📂 打开输出目录", 
                                    command=self.open_output_dir, bootstyle=PRIMARY, width=20)
        open_dir_button.pack(side=LEFT, padx=10)
        
        # 开始转换按钮
        self.convert_button = ttk.Button(command_frame, text="🍭 开始转换", 
                                        command=self.start_conversion, bootstyle=WARNING, width=20)
        self.convert_button.pack(side=LEFT, padx=10)
        
        # 清空日志按钮
        clear_log_button = ttk.Button(command_frame, text="🧹 清空日志", 
                                    command=self.clear_log, bootstyle=SECONDARY, width=20)
        clear_log_button.pack(side=LEFT, padx=10)
        
        # 进度和日志
        progress_frame = ttk.Labelframe(main_frame, text="4.进度与日志", bootstyle=INFO, padding=10)
        progress_frame.pack(fill=BOTH, expand=True, pady=(0, 0))
        
        # 日志文本框
        log_container = ttk.Frame(progress_frame)
        log_container.pack(fill=BOTH, expand=True)
        
        self.log_text = ScrolledText(log_container, height=12, font=("Consolas", 9))
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        
        # 状态栏 - 进度条
        status_frame = ttk.Frame(self.root, padding=(10, 0))
        status_frame.pack(fill=X, side=BOTTOM)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100, bootstyle=INFO)
        self.progress_bar.pack(fill=X, pady=(0, 5))
        
        self.status_label = ttk.Label(status_frame, text="就绪", bootstyle=INFO)
        self.status_label.pack()
        
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
        """添加路径，去重并排序"""
        added_count = 0
        seen = set(self.input_paths)
        for path in paths:
            if path not in seen:
                self.input_paths.append(path)
                seen.add(path)
                added_count += 1
        if added_count > 0:
            self.input_paths.sort(key=lambda x: os.path.basename(x).lower())
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
                mode = "递归" if self.recursive_var.get() else "当前文件夹"
                self.log_message(f"[信息] 从 {mode} '{os.path.basename(folder)}' 中添加了 {added} 个 {filter_desc}")
            else:
                self.log_message(f"[警告] 所选文件夹中没有找到 {filter_desc} ！")
    
    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir = directory
            self.output_dir_var.set(directory)
    
    def open_output_dir(self):
        """打开输出目录"""
        if not self.output_dir:
            messagebox.showwarning("警告", "请先选择输出目录")
            return
        if not os.path.exists(self.output_dir):
            messagebox.showwarning("警告", "输出目录不存在")
            return
        try:
            if platform.system() == 'Windows':
                os.startfile(self.output_dir)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{self.output_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{self.output_dir}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {str(e)}")
    
    def clear_selection(self):
        """清除所有选择的文件"""
        self.input_paths.clear()
        self.update_file_list()
        self.log_message("[信息] 已清除所有文件选择")
    
    def remove_selected_file(self, event):
        """双击移除选中的文件"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            removed_path = self.input_paths.pop(index)
            self.update_file_list()
            self.log_message(f"[信息] 已移除: {os.path.basename(removed_path)}")
    
    def update_file_list(self):
        """更新文件列表框"""
        self.file_listbox.delete(0, tk.END)
        for path in self.input_paths:
            self.file_listbox.insert(tk.END, os.path.basename(path))
        
        # 更新文件计数
        count = len(self.input_paths)
        self.file_count_label.config(text=f"({count} 个文件)")
    
    def update_quality_label(self, value):
        """更新质量值标签"""
        self.quality_value_label.config(text=str(int(float(value))))
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def log_message(self, message):
        """添加消息到日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, text):
        """更新状态标签"""
        self.status_label.config(text=text)
        self.root.update_idletasks()
    
    def start_conversion(self):
        """开始转换过程"""
        if not self.input_paths:
            messagebox.showwarning("警告", "请先选择要转换的图片文件或文件夹")
            return
        
        if not self.output_dir:
            directory = os.path.dirname(self.input_paths[0])
            self.output_dir = directory
            self.output_dir_var.set(directory)
            self.log_message(f"[警告] 未选择输出目录，结果将保存在输入文件的目录：{directory}")
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
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
                    
                    # 转换为 RGB 模式（如果必要）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 调整尺寸（如果指定了尺寸）
                    width_str = self.width_var.get().strip()
                    height_str = self.height_var.get().strip()
                    
                    if width_str or height_str:
                        original_width, original_height = img.size
                        
                        # 解析宽度和高度
                        try:
                            if width_str and height_str:
                                new_width = int(width_str)
                                new_height = int(height_str)
                            elif width_str:
                                new_width = int(width_str)
                                new_height = int(original_height * (new_width / original_width))
                            elif height_str:
                                new_height = int(height_str)
                                new_width = int(original_width * (new_height / original_height))
                            
                            # 如果要求保持宽高比，调整为适应尺寸
                            if self.keep_aspect_var.get():
                                ratio = min(new_width / original_width, new_height / original_height)
                                new_width = int(original_width * ratio)
                                new_height = int(original_height * ratio)
                            
                            # 调整图像尺寸
                            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            
                        except ValueError:
                            self.log_message(f"[错误] 无效的尺寸设置 - {os.path.basename(input_path)}")
                            failed_count += 1
                            continue
                    
                    # 生成输出文件名
                    base_name = os.path.splitext(os.path.basename(input_path))[0]
                    output_filename = f"{base_name}.jpg"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
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
                            output_path = os.path.join(self.output_dir, output_filename)
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
        
        # 显示完成消息框
        if failed_count == 0 and skipped_count == 0:
            messagebox.showinfo("完成", f"所有 {total} 个文件已成功转换!")
        else:
            msg = f"转换完成!\n成功: {converted_count}\n失败: {failed_count}\n跳过: {skipped_count}\n总计: {total}"
            messagebox.showinfo("完成", msg)

def main():
    root = ttk.Window(themename="cosmo")
    app = ImageBatchConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
