# Kinlin AI Service

Python AI服务，提供AI能力

## 技术栈

- FastAPI
- 麒麟AI SDK
- Python 3.9+

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

创建 `.env` 文件：

```
KYLIN_AI_API_KEY=your_api_key
KYLIN_AI_ENDPOINT=https://api.kylin.ai
```

## 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API接口

- `POST /ai/chat/text` - 文本对话
- `POST /ai/chat/voice` - 语音对话
- `POST /ai/tts` - 文本转语音

