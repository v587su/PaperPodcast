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