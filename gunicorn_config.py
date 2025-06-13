import multiprocessing

# 绑定的地址和端口
bind = "127.0.0.1:8082"

# 工作进程数
workers = 1  # 减少worker数量以便调试

# 工作模式
worker_class = "sync"  # 使用默认的sync worker

# 超时时间
timeout = 300

# 访问日志和错误日志
accesslog = "logs/access.log"
errorlog = "logs/error.log"

# 日志级别
loglevel = "debug"  # 改为debug级别以获取更多信息

# 守护进程模式
daemon = True  # 改为后台运行

# 进程名称
proc_name = "paper_podcast" 