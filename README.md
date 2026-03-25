# Qwen3-TTS FastAPI Server

基于 Qwen3-TTS 实现的文字转语音 API 服务。

## 功能特性

- **文字转语音 (TTS)**: 支持基础的文字转语音功能
- **语音克隆 (Voice Clone)**: 使用参考音频进行语音克隆
- **预设说话人 (Custom Voice)**: 使用预设的说话人声音
- **语音设计 (Voice Design)**: 使用自然语言描述生成语音

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
cd /home/pix/dev/code/ai/qwen3-tts
pip install -r requirements.txt
```

## 启动服务

```bash
# 方式1: 使用启动脚本
./start.sh

# 方式2: 直接运行
python -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

## API 端点

### 健康检查

```bash
GET /health
```

返回:
```json
{
  "status": "healthy",
  "device": "cuda",
  "model": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
  "supported_languages": [...]
}
```

### 获取支持的语言列表

```bash
GET /languages
```

### 文字转语音 (Voice Clone 方式)

```bash
POST /tts
```

参数:
- `text` (必填): 要转换的文本
- `language` (可选): 语言，默认自动检测
- `exaggeration` (可选): 情感夸张程度 0.0-1.0，默认 0.5
- `temperature` (可选): 采样温度 0.0-1.0，默认 0.8
- `instruct` (可选): 语音风格指令，用于控制语速、情感、语气等，用于控制语速、情感、语气等
- `audio_prompt` (可选): 参考音频文件

### 预设说话人 TTS

```bash
POST /tts/custom
```

参数:
- `text` (必填): 要转换的文本
- `language` (可选): 语言，默认自动检测
- `speaker` (必填): 预设说话人名称
- `exaggeration` (可选): 情感夸张程度 0.0-1.0
- `temperature` (可选): 采样温度 0.0-1.0
- `instruct` (可选): 语音风格指令，用于控制语速、情感、语气等

### 语音设计

```bash
POST /tts/design
```

参数:
- `text` (必填): 要转换的文本
- `language` (可选): 语言，默认自动检测
- `instruct` (必填): 自然语言声音描述
- `exaggeration` (可选): 情感夸张程度 0.0-1.0
- `temperature` (可选): 采样温度 0.0-1.0

### 语音克隆

```bash
POST /tts/clone
```

参数:
- `text` (必填): 要转换的文本
- `audio_prompt` (必填): 参考音频文件
- `language` (可选): 语言，默认自动检测
- `ref_text` (可选): 参考音频对应的文本
- `exaggeration` (可选): 情感夸张程度 0.0-1.0
- `temperature` (可选): 采样温度 0.0-1.0
- `instruct` (可选): 语音风格指令，用于控制语速、情感、语气等

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
# 基础 TTS
curl -X POST "http://localhost:8001/tts" \
  -F "text=Hello, this is a test." \
  -F "language=English" \
  --output output.wav

# 语音克隆
curl -X POST "http://localhost:8001/tts/clone" \
  -F "text=Hello, this is a test." \
  -F "audio_prompt=@reference.wav" \
  -F "ref_text=The text spoken in the reference audio" \
  --output clone_output.wav

# 语音设计
curl -X POST "http://localhost:8001/tts/design" \
  -F "text=Hello, this is a test." \
  -F "instruct=A warm and friendly male voice" \
  --output design_output.wav
```

### Python 示例

```python
import requests

# 基础 TTS
with open("text.txt") as f:
    text = f.read()

response = requests.post(
    "http://localhost:8001/tts",
    data={"text": text, "language": "English"},
)

with open("output.wav", "wb") as f:
    f.write(response.content)
```

## 技术细节

- **模型**: Qwen/Qwen3-TTS-12Hz-0.6B-Base
- **设备**: 自动检测 CUDA，可用则使用 GPU
- **懒加载**: 模型在首次请求时加载
- **临时文件清理**: 自动后台清理上传和输出文件
- **语言检测**: 支持自动检测 10 种语言
