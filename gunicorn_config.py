import multiprocessing

# 绑定的地址和端口
bind = "127.0.0.1:8000"

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "eventlet"

# 超时时间
timeout = 300

# 访问日志和错误日志
accesslog = "logs/access.log"
errorlog = "logs/error.log"

# 日志级别
loglevel = "info"

# 守护进程模式
daemon = True

# 进程名称
proc_name = "paper_podcast" 