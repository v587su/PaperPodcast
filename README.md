# Paper Podcast

将学术论文转换为播客的应用。

## 设置

1. 克隆仓库：
```bash
git clone <repository-url>
cd paper-podcast
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置：
   - 复制 `config.ini.example` 为 `config.ini`
   - 在 `config.ini` 中填入你的 API keys：
     - Gemini API key
     - OpenAI API key

4. 运行应用：
```bash
python app.py
```

## 配置说明

`config.ini` 文件包含以下配置项：

- `[auth]`: 认证相关配置
  - `token`: 认证令牌

- `[podcast]`: 播客生成相关配置
  - `llm_model_name`: 使用的语言模型名称
  - `upload_folder`: 上传文件存储目录
  - `pdf_folder`: PDF 文件存储目录
  - `mp3_folder`: 生成的 MP3 文件存储目录

- `[gemini]`: Gemini API 配置
  - `api_key`: Gemini API key

- `[openai]`: OpenAI API 配置
  - `api_key`: OpenAI API key

## 安全说明

- 不要将包含实际 API keys 的 `config.ini` 提交到版本控制系统
- 保持 `config.ini.example` 作为配置模板
- 确保 `.gitignore` 正确配置，排除 `config.ini` 和敏感文件

## 部署指南

### 1. 服务器要求
- Python 3.8+
- Nginx
- 足够的磁盘空间用于存储上传的 PDF 和生成的 MP3 文件

### 2. 安装依赖
```bash
# 安装系统依赖
sudo apt-get update
sudo apt-get install python3-venv nginx

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 配置 Nginx
1. 复制 Nginx 配置文件：
```bash
sudo cp nginx.conf /etc/nginx/sites-available/paper_podcast
sudo ln -s /etc/nginx/sites-available/paper_podcast /etc/nginx/sites-enabled/
```

2. 修改配置文件中的域名和路径：
- 将 `your_domain.com` 替换为你的实际域名
- 将 `/path/to/your/project/frontend` 替换为实际的前端文件路径

3. 测试并重启 Nginx：
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 4. 启动应用
1. 创建日志目录：
```bash
mkdir logs
```

2. 使用 Gunicorn 启动应用：
```bash
gunicorn -c gunicorn_config.py app:app
```

### 5. 设置开机自启
创建 systemd 服务文件：
```bash
sudo nano /etc/systemd/system/paper_podcast.service
```

添加以下内容：
```ini
[Unit]
Description=Paper Podcast Application
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/your/project/venv/bin"
ExecStart=/path/to/your/project/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务：
```bash
sudo systemctl enable paper_podcast
sudo systemctl start paper_podcast
```

### 6. 监控和维护
- 查看应用日志：`tail -f logs/error.log`
- 查看 Nginx 日志：`tail -f /var/log/nginx/paper_podcast_error.log`
- 重启应用：`sudo systemctl restart paper_podcast`
- 重启 Nginx：`sudo systemctl restart nginx` 