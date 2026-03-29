# Qwen3-TTS FastAPI Server

基于 Qwen3-TTS 实现的文字转语音 API 服务。

## 功能特性

- **语音克隆 (Voice Clone)**: 使用参考音频进行语音克隆
- **参考音频管理**: 上传和管理预设参考音频（含 ref_text）
- **TTS 生成**: 使用保存的参考音频快速生成语音

## 项目结构

```
qwen3-tts-api/
├── src/
│   └── qwen3_tts_api/           # 源码包
│       ├── config.py             # 配置
│       ├── main.py              # FastAPI 应用入口
│       ├── models/              # 数据模型
│       ├── services/            # 业务逻辑
│       ├── db/                  # 数据库层
│       ├── api/routes/          # API 路由
│       └── resources/           # 资源管理
├── tests/                       # 测试
├── scripts/                     # 脚本
├── res/                         # 静态资源
│   └── audio/                   # 示例音频
├── data/                        # 数据存储
│   └── *.db                     # SQLite 数据库
├── api.py                       # 向后兼容入口
└── pyproject.toml              # 项目配置
```

## 支持语言

- Chinese (中文)
- English (英语)
- Japanese (日语)
- Korean (韩语)
- German (德语)
- French (法语)
- Russian (俄语)
- Portuguese (葡萄牙语)
- Spanish (西班牙语)
- Italian (意大利语)

## 安装

```bash
uv sync
```

## 启动服务

```bash
# 方式1: 使用启动脚本
./start.sh

# 方式2: 向后兼容入口
python -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload

# 方式3: 直接运行（推荐）
python -m uvicorn src.qwen3_tts_api.main:app --host 0.0.0.0 --port 8001 --reload

# 方式4: 编程式启动
python -m qwen3_tts_api
```

## API 文档

详细 API 文档请参考 [docs/REFERENCE_AUDIO_API.md](docs/REFERENCE_AUDIO_API.md)

## API 端点

### 健康检查

```bash
GET /health
```

### 获取支持的语言列表

```bash
GET /languages
```

### 语音克隆

```bash
POST /tts/clone
```

参数:

- `text` (必填): 要转换的文本
- `audio_prompt` (必填): 参考音频文件
- `language` (可选): 语言，默认自动检测
- `ref_text` (可选): 参考音频对应的文本
- `exaggeration` (可选): 情感夸张程度 0.0-1.0，默认 0.5
- `temperature` (可选): 采样温度 0.0-1.0，默认 0.8
- `instruct` (可选): 语音风格指令
- `speed_rate` (可选): 语速倍率 0.5-2.0，默认 1.0

### 参考音频管理

```bash
# 上传参考音频
POST /tts/reference/upload
# 参数: name, file, ref_text, language, exaggeration, temperature, instruct, speed_rate

# 列出所有参考音频
GET /tts/reference/list

# 获取默认参考音频
GET /tts/reference/default

# 设置默认参考音频
POST /tts/reference/default/{id}

# 获取单个参考音频详情
GET /tts/reference/{id}

# 下载参考音频
GET /tts/reference/{id}/audio

# 更新参考音频信息
POST /tts/reference/{id}
# 参数: name, ref_text, language, exaggeration, temperature, instruct, speed_rate

# 删除参考音频
DELETE /tts/reference/{id}
```

### TTS 生成 (使用保存的参考音频)

```bash
POST /tts/generate
```

参数:

- `text` (必填): 要转换的文本
- `reference_id` (可选): 参考音频 ID
- `reference_name` (可选): 参考音频名称
- `language` (可选): 语言，默认自动检测
- `exaggeration` (可选): 情感夸张程度 0.0-1.0
- `temperature` (可选): 采样温度 0.0-1.0
- `instruct` (可选): 语音风格指令
- `speed_rate` (可选): 语速倍率 0.5-2.0

注意: `reference_id` 和 `reference_name` 二选一，参数可覆盖默认值

### 长文本拆分

```bash
POST /text/split
```

参数 (JSON Body):

- `text` (必填): 要拆分的长文本
- `max_length` (可选): 单个片段的最大字符数，默认 200，范围 10-2000
- `min_chunk_length` (可选): 合并短片段的最小长度阈值，默认 50，范围 1-500
- `merge_short` (可选): 是否合并过短的片段，默认 True

拆分策略:
1. 首先按段落拆分
2. 对于超出大小的段落，按句子拆分
3. 对于仍然超出大小的句子，尝试按子句拆分
4. 合并过短的片段

响应示例:
```json
{
  "success": true,
  "chunks": ["片段1", "片段2", "片段3"],
  "chunk_count": 3,
  "original_length": 500,
  "max_length": 200
}
```

### 音频合并

```bash
POST /audio/merge
```

使用 ffmpeg concat 合并多个音频文件为单个音频文件。

参数 (multipart/form-data):

- `files` (必填): 音频文件列表，至少需要2个文件
- 支持格式: wav, mp3, m4a, flac, ogg, aac

响应: 返回合并后的 WAV 音频文件

示例:
```bash
curl -X POST "http://localhost:8001/audio/merge" \
  -F "files=@1.wav" \
  -F "files=@2.wav" \
  -F "files=@3.wav" \
  --output merged.wav
```

## 风格提示词示例

### 语速节奏

- "Speak at a relaxed, conversational pace"
- "Speak with natural rhythm, not too fast"
- "Slow down for important points"
- "Speak deliberately with measured pauses"
- "语速适中，自然流畅"

### 情感表达

- "Speak with warmth and friendliness"
- "Sound enthusiastic and energetic"
- "Speak in a calm, professional manner"
- "Add a touch of excitement to your voice"
- "温柔亲切，富有情感"

### 语气语调

- "Use a gentle, soothing tone"
- "Speak with a cheerful inflection"
- "Add some emphasis on key words"
- "Sound natural with varied intonation"
- "像朋友聊天一样自然"

### 具体场景

- "Tell this story with emotion and expression"
- "Read this like a friendly podcast host"
- "Explain this clearly and patiently"
- "Announce this with gravitas"
- "专业播音员的感觉"

### 停顿控制

- 使用标点符号（逗号、句号、问号、感叹号）自动添加停顿
- 使用 `...` 添加额外停顿，可叠加使用（如 `.....`）增加停顿时长

### 参数配合

建议结合 `exaggeration` 参数（0.0-1.0）一起使用：

- 值越高情感越夸张
- 较低的值（0.2-0.4）更适合专业场景
- 较高的值（0.6-0.8）适合富有表现力的内容

## 使用示例

### cURL 示例

```bash
# 1. 上传参考音频（含ref_text和默认参数）
curl -X POST "http://localhost:8001/tts/reference/upload" \
  -F "name=我的音色" \
  -F "file=@audio.wav" \
  -F "ref_text=这是参考文本" \
  -F "language=Chinese" \
  -F "exaggeration=0.5" \
  -F "temperature=0.8"

# 2. 列出所有参考音频
curl http://localhost:8001/tts/reference/list

# 3. 使用保存的参考音频生成语音
curl -X POST "http://localhost:8001/tts/generate" \
  -F "text=你好，世界" \
  -F "reference_id=1" \
  --output output.wav

# 4. 使用名称查找并生成（可覆盖默认参数）
curl -X POST "http://localhost:8001/tts/generate" \
  -F "text=Hello world" \
  -F "reference_name=我的音色" \
  -F "exaggeration=0.7" \
  --output output2.wav

# 5. 长文本拆分
curl -X POST "http://localhost:8001/text/split" \
  -H "Content-Type: application/json" \
  -d '{"text": "这是一个很长的文本，需要拆分成多个片段...", "max_length": 200}'
```

### Python 示例

```python
import requests

# 使用保存的参考音频生成
response = requests.post(
    "http://localhost:8001/tts/generate",
    data={
        "text": "你好，世界",
        "reference_id": 1,
    },
)

with open("output.wav", "wb") as f:
    f.write(response.content)

# 长文本拆分
response = requests.post(
    "http://localhost:8001/text/split",
    json={
        "text": "这是一个很长的文本，需要拆分成多个片段...",
        "max_length": 200,
    },
)

result = response.json()
print(f"拆分结果: {result['chunk_count']} 个片段")
for i, chunk in enumerate(result["chunks"]):
    print(f"片段 {i+1}: {chunk}")
```

## 技术细节

- **模型**: Qwen/Qwen3-TTS-12Hz-0.6B-Base
- **设备**: 自动检测 CUDA，可用则使用 GPU
- **懒加载**: 模型在首次请求时加载
- **临时文件清理**: 自动后台清理上传和输出文件
- **语言检测**: 支持自动检测 10 种语言
- **数据存储**: SQLite 数据库管理参考音频
- **代码结构**: 符合 Python 最佳实践，分层设计
