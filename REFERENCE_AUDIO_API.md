# 参考音频管理系统 API 文档

## 概述

本文档描述了重构后的参考音频管理系统，将原有的 `/tts/design` 和 `/tts/custom` 管理接口合并为统一的 `/tts/reference` 接口。

## 接口列表

### 1. 参考音频管理接口 (`/tts/reference`)

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

### 2. TTS 生成接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/tts/generate` | 使用保存的参考音频生成语音 |
| POST | `/tts/clone` | 语音克隆 (保留，不更改) |
| POST | `/tts/custom` | 使用内置预设说话人 (保留，不更改) |
| POST | `/tts/design` | Voice Design (保留，不更改) |

---

## 详细接口说明

### 1. 上传参考音频

**POST** `/tts/reference/upload`

上传参考音频并保存到数据库。

**参数 (Form Data):**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 音频名称 |
| file | file | 是 | 音频文件 (mp3/wav/m4a/flac/ogg/aac) |
| ref_text | string | 否 | 参考文本（描述音频内容） |
| language | string | 否 | 语言 |
| exaggeration | float | 否 | 默认情感夸张值 (0.0-1.0, 默认 0.5) |
| temperature | float | 否 | 默认采样温度 (0.0-1.0, 默认 0.8) |
| instruct | string | 否 | 默认语音风格指令 |
| speed_rate | float | 否 | 默认语速 (0.5-2.0, 默认 1.0) |
| is_default | bool | 否 | 是否设为默认 (默认 false) |

**响应示例:**
```json
{
  "success": true,
  "message": "参考音频上传成功",
  "data": {
    "id": 1,
    "name": "我的参考音频",
    "file_path": "res/references/xxx.wav",
    "ref_text": "这是一段中文朗读",
    "language": "Chinese",
    "exaggeration": 0.5,
    "temperature": 0.8,
    "instruct": null,
    "speed_rate": 1.0,
    "is_default": 0,
    "created_at": "2026-03-28T12:00:00",
    "updated_at": "2026-03-28T12:00:00"
  }
}
```

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
      "file_path": "res/references/xxx.wav",
      "ref_text": "文本内容",
      "language": "Chinese",
      "exaggeration": 0.5,
      "temperature": 0.8,
      "instruct": null,
      "speed_rate": 1.0,
      "is_default": 1,
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
    "is_default": 1,
    ...
  }
}
```

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
    "file_path": "res/references/xxx.wav",
    ...
  }
}
```

---

### 6. 下载参考音频

**GET** `/tts/reference/{reference_id}/audio`

下载参考音频文件。

**参数:**
- `reference_id`: 参考音频 ID (路径参数)

**响应:** 二进制音频文件

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

---

### 9. 使用参考音频生成语音

**POST** `/tts/generate`

使用保存的参考音频生成语音。

**参数 (Form Data):**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 要转换的文本 |
| reference_id | int | 是* | 参考音频 ID (二选一) |
| reference_name | string | 是* | 参考音频名称 (二选一) |
| language | string | 否 | 语言 (默认自动检测) |
| ref_text | string | 否 | 参考文本 (覆盖默认值) |
| exaggeration | float | 否 | 情感夸张值 (覆盖默认值) |
| temperature | float | 否 | 采样温度 (覆盖默认值) |
| instruct | string | 否 | 语音风格指令 (覆盖默认值) |
| speed_rate | float | 否 | 语速 (覆盖默认值) |

**响应:** 二进制音频文件 (WAV)

**响应头:**
- `Content-Type: audio/wav`
- `Content-Disposition: attachment; filename="tts_xxx.wav"`

---

## 数据模型

### 数据库表: `tts_references`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | TEXT | 音频名称 |
| file_path | TEXT | 文件路径 |
| ref_text | TEXT | 参考文本 (可选) |
| language | TEXT | 语言 |
| exaggeration | REAL | 默认情感夸张值 |
| temperature | REAL | 默认采样温度 |
| instruct | TEXT | 默认语音风格指令 |
| speed_rate | REAL | 默认语速 |
| is_default | INTEGER | 是否默认 (0/1) |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

---

## 迁移说明

如果需要从旧系统迁移数据，可以运行迁移脚本:

```bash
python migrate_references.py
```

该脚本会将 `tts_designs.db` 和 `tts_custom.db` 中的数据迁移到新的 `tts_references.db` 数据库。

**注意:** 迁移后旧数据库不会被删除，请手动确认迁移结果后再决定是否删除旧数据库文件。
