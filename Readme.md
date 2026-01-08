# 1. 多格式图片批量转换器

## 1.1. 主要功能

- 批量转换图片文件至JPG格式，可以指定长宽和质量

## 1.2. 使用方法

- 使用很简单，略

## 1.3. 打包命令

- 生成单文件格式
  `pyinstaller -F -w ImageBatchConverter.py --clean -n 多格式图片批量转换器`

- 生成单文件格式（Nuitka --onefile自动压缩）
  
  `python -m nuitka --mingw64 --onefile --lto=yes --show-progress --output-dir=dist --remove-output --plugin-enable=tk-inter --windows-console-mode=disable --windows-icon-from-ico=liug.ico ImageBatchConverter.py`

- 生成单文件格式（Nuitka --使用upx 压缩）
  
  `python -m nuitka --mingw64 --onefile --onefile-no-compression --plugin-enable=upx  --lto=yes --show-progress --output-dir=dist --remove-output --plugin-enable=tk-inter --windows-console-mode=disable --windows-icon-from-ico=liug.ico ImageBatchConverter.py`
