# 1. 获取 drive 中新 pdf
# 2. 生成 podcast，包括mp3和mp4
# 3. 上传到 drive

#!/usr/bin/env python3
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 配置部分
WATCH_DIRECTORY = "./data/pdfs"  
RUN_SCRIPT = "run.py"

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        """当有新文件创建时触发"""
        if event.is_directory:
            return
        if event.src_path.lower().endswith('.pdf'):
            print(f"检测到新PDF文件: {event.src_path}")
            self.run_script(event.src_path)

    def on_moved(self, event):
        """当有文件被移动/重命名到监控目录时触发"""
        if event.is_directory:
            return
        if event.dest_path.lower().endswith('.pdf'):
            print(f"检测到移动/重命名的PDF文件: {event.dest_path}")
            self.run_script(event.dest_path)

    def run_script(self, pdf_path):
        """运行指定的Python脚本并传入PDF文件路径"""
        try:
            print(f"正在运行脚本: {RUN_SCRIPT} 参数: {pdf_path}")
            subprocess.run(["python", RUN_SCRIPT, "--url", pdf_path], check=True)
            print("脚本运行完成")
        except subprocess.CalledProcessError as e:
            print(f"运行脚本时出错: {e}")
        except Exception as e:
            print(f"发生未知错误: {e}")

def main():
    # 检查监控目录是否存在
    if not os.path.isdir(WATCH_DIRECTORY):
        print(f"错误: 目录 {WATCH_DIRECTORY} 不存在")
        return

    # 检查要运行的脚本是否存在
    if not os.path.isfile(RUN_SCRIPT):
        print(f"错误: 脚本 {RUN_SCRIPT} 不存在")
        return

    print(f"开始监控目录: {WATCH_DIRECTORY}")
    print(f"当检测到新PDF文件时，将运行: {RUN_SCRIPT} 并传入PDF路径")
    print("按 Ctrl+C 停止监控...")

    event_handler = PDFHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
