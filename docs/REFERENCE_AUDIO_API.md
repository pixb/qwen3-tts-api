# 参考音频管理系统 API 文档

## 概述

本文档描述了参考音频管理系统，提供统一的 `/tts/reference` 接口用于管理参考音频。

## 接口列表

### 参考音频管理接口 (`/tts/reference`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/tts/reference/upload` | 上传参考音频 |
| GET | `/tts/reference/list` | 列出所有参考音频 |
| GET | `/tts/reference/default` | 获取默认参考音频 |
| POST | `/tts/reference/default/{reference_id}` | 设置默认参考音频 |
| GET | `/tts/reference/{reference_id}` | 获取参考音频详情 |
| GET | `/tts/reference/{reference_id}/audio` | 下载参考音频 |
| POST | `/tts/reference/{reference_id}` | 更新参考音频 |
| DELETE | `/tts/reference/{reference_id}` | 删除参考音频 |

### TTS 生成接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/tts/generate` | 使用保存的参考音频生成语音 |
| POST | `/tts/clone` | 语音克隆 |

---

## 详细接口说明

### 1. 上传参考音频

**POST** `/tts/reference/upload`

上传参考音频并保存到数据库。

**参数 (Form Data):**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| name | string | 是 | - | 音频名称 |
| file | file | 是 | - | 音频文件 (mp3/wav/m4a/flac/ogg/aac) |
| ref_text | string | 是 | - | 参考文本（描述音频内容） |
| language | string | 否 | None | 语言 |
| exaggeration | float | 否 | 0.5 | 情感夸张值 (0.0-1.0) |
| temperature | float | 否 | 0.8 | 采样温度 (0.0-1.0) |
| instruct | string | 否 | None | 语音风格指令 |
| speed_rate | float | 否 | 1.0 | 语速 (0.5-2.0) |
| is_default | bool | 否 | false | 是否设为默认 |

**响应示例:**
```json
{
  "success": true,
  "message": "参考音频上传成功",
  "data": {
    "id": 1,
    "name": "我的参考音频",
    "file_path": "uuid.wav",
    "ref_text": "这是一段中文朗读",
    "language": "Chinese",
    "exaggeration": 0.5,
    "temperature": 0.8,
    "instruct": null,
    "speed_rate": 1.0,
    "is_default": false,
    "created_at": "2026-03-28T12:00:00",
    "updated_at": "2026-03-28T12:00:00"
  }
}
```

**错误响应:**
- `400`: 名称已存在或不支持的音频格式
- `500`: 保存文件或记录失败

---

### 2. 列出所有参考音频

**GET** `/tts/reference/list`

获取所有已保存的参考音频列表。

**响应示例:**
```json
{
  "success": true,
  "total": 2,
  "data": [
    {
      "id": 1,
      "name": "参考音频1",
      "file_path": "uuid.wav",
      "ref_text": "文本内容",
      "language": "Chinese",
      "exaggeration": 0.5,
      "temperature": 0.8,
      "instruct": null,
      "speed_rate": 1.0,
      "is_default": true,
      "created_at": "2026-03-28T12:00:00",
      "updated_at": "2026-03-28T12:00:00"
    }
  ]
}
```

---

### 3. 获取默认参考音频

**GET** `/tts/reference/default`

获取当前设置为默认的参考音频。

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "默认参考音频",
    ...
  }
}
```

**错误响应:**
- `404`: 未设置默认参考音频

---

### 4. 设置默认参考音频

**POST** `/tts/reference/default/{reference_id}`

将指定参考音频设为默认。

**参数:**
- `reference_id`: 参考音频 ID (路径参数)

**响应示例:**
```json
{
  "success": true,
  "message": "默认参考音频设置成功",
  "data": {
    "id": 1,
    "name": "默认参考音频",
    "is_default": true,
    ...
  }
}
```

**错误响应:**
- `404`: 参考音频不存在

---

### 5. 获取参考音频详情

**GET** `/tts/reference/{reference_id}`

获取单个参考音频的详细信息。

**参数:**
- `reference_id`: 参考音频 ID (路径参数)

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "参考音频1",
    "file_path": "uuid.wav",
    ...
  }
}
```

**错误响应:**
- `404`: 参考音频不存在

---

### 6. 下载参考音频

**GET** `/tts/reference/{reference_id}/audio`

下载参考音频文件。

**参数:**
- `reference_id`: 参考音频 ID (路径参数)

**响应:** 二进制音频文件

**响应头:**
- `Content-Type: audio/mpeg`
- `Content-Disposition: attachment; filename="{name}.{ext}"`

**错误响应:**
- `404`: 参考音频或文件不存在

---

### 7. 更新参考音频

**POST** `/tts/reference/{reference_id}`

更新参考音频的信息。

**参数 (Form Data):**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 新名称 |
| ref_text | string | 否 | 参考文本 |
| language | string | 否 | 语言 |
| exaggeration | float | 否 | 情感夸张值 (0.0-1.0) |
| temperature | float | 否 | 采样温度 (0.0-1.0) |
| instruct | string | 否 | 语音风格指令 |
| speed_rate | float | 否 | 语速 (0.5-2.0) |
| is_default | bool | 否 | 是否设为默认 |

**响应示例:**
```json
{
  "success": true,
  "message": "参考音频更新成功",
  "data": {
    "id": 1,
    "name": "新名称",
    ...
  }
}
```

**错误响应:**
- `400`: 名称已存在
- `404`: 参考音频不存在

---

### 8. 删除参考音频

**DELETE** `/tts/reference/{reference_id}`

删除参考音频及其文件。

**参数:**
- `reference_id`: 参考音频 ID (路径参数)

**响应示例:**
```json
{
  "success": true,
  "message": "参考音频删除成功"
}
```

**错误响应:**
- `404`: 参考音频不存在

---

### 9. 使用参考音频生成语音

**POST** `/tts/generate`

使用保存的参考音频生成语音。

**参数 (Form Data):**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| text | string | 是 | - | 要转换的文本 |
| reference_id | int | 是* | - | 参考音频 ID (二选一) |
| reference_name | string | 是* | - | 参考音频名称 (二选一) |
| language | string | 否 | Auto | 语言 (默认自动检测) |
| ref_text | string | 是 | - | 参考文本 (描述参考音频的内容) |
| exaggeration | float | 否 | 参考音频默认值 | 情感夸张值 (覆盖默认值) |
| temperature | float | 否 | 参考音频默认值 | 采样温度 (覆盖默认值) |
| instruct | string | 否 | 参考音频默认值 | 语音风格指令 (覆盖默认值) |
| speed_rate | float | 否 | 参考音频默认值 | 语速 (覆盖默认值) |

注意: `reference_id` 和 `reference_name` 必须提供其中一个

**响应:** 二进制音频文件 (WAV)

**响应头:**
- `Content-Type: audio/wav`
- `Content-Disposition: attachment; filename="tts_{lang}.wav"`

**错误响应:**
- `400`: 未提供文本或未指定参考音频
- `404`: 参考音频不存在或文件不存在
- `500`: 服务端错误

---

## 数据模型

### 数据库表: `tts_references`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| name | TEXT | 音频名称，唯一 |
| file_path | TEXT | 文件路径（相对路径） |
| ref_text | TEXT | 参考文本 (必填) |
| language | TEXT | 语言 (可选) |
| exaggeration | REAL | 默认情感夸张值 |
| temperature | REAL | 默认采样温度 |
| instruct | TEXT | 默认语音风格指令 (可选) |
| speed_rate | REAL | 默认语速 |
| is_default | INTEGER | 是否默认 (0/1) |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

---

## 使用示例

### cURL 示例

```bash
# 1. 上传参考音频（ref_text 必填）
curl -X POST "http://localhost:8001/tts/reference/upload" \
  -F "name=我的音色" \
  -F "file=@audio.wav" \
  -F "ref_text=这是参考文本" \
  -F "language=Chinese" \
  -F "exaggeration=0.5" \
  -F "temperature=0.8"

# 2. 列出所有参考音频
curl http://localhost:8001/tts/reference/list

# 3. 获取默认参考音频
curl http://localhost:8001/tts/reference/default

# 4. 设置默认参考音频
curl -X POST "http://localhost:8001/tts/reference/default/1"

# 5. 获取单个参考音频详情
curl http://localhost:8001/tts/reference/1

# 6. 下载参考音频
curl "http://localhost:8001/tts/reference/1/audio" -o download.wav

# 7. 更新参考音频
curl -X POST "http://localhost:8001/tts/reference/1" \
  -F "name=新名称" \
  -F "exaggeration=0.7"

# 8. 删除参考音频
curl -X DELETE "http://localhost:8001/tts/reference/1"

# 9. 使用参考音频生成语音 (通过ID，ref_text 必填)
curl -X POST "http://localhost:8001/tts/generate" \
  -F "text=你好，世界" \
  -F "reference_id=1" \
  -F "ref_text=这是参考音频的文本内容" \
  --output output.wav

# 10. 使用参考音频生成语音 (通过名称，ref_text 必填)
curl -X POST "http://localhost:8001/tts/generate" \
  -F "text=Hello world" \
  -F "reference_name=我的音色" \
  -F "ref_text=这是参考音频的文本内容" \
  -F "exaggeration=0.7" \
  --output output2.wav
```

### Python 示例

```python
import requests

# 上传参考音频（ref_text 必填）
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8001/tts/reference/upload",
        data={
            "name": "我的音色",
            "ref_text": "这是参考文本",
            "language": "Chinese",
            "exaggeration": 0.5,
            "temperature": 0.8,
        },
        files={"file": f}
    )
    print(response.json())

# 使用保存的参考音频生成（ref_text 必填）
response = requests.post(
    "http://localhost:8001/tts/generate",
    data={
        "text": "你好，世界",
        "reference_id": 1,
        "ref_text": "这是参考音频的文本内容",
    },
)

with open("output.wav", "wb") as f:
    f.write(response.content)
```
