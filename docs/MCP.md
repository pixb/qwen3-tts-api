# Qwen3-TTS MCP Server 方案

## 概述

MCP (Model Context Protocol) Server 用于将 Qwen3-TTS API 服务暴露给 AI 工具（如 opencode、Claude Desktop 等），使 AI 能够自动调用 TTS 功能。

**注意：** `tts_generate` 工具被标记为耗时操作（openWorldHint=true），AI 工具会等待音频生成完成后再返回结果。MCP 服务器超时时间设置为 20 分钟。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                         AI (opencode)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ 调用工具
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (新建)                          │
│  - 接收 AI 的工具调用请求                                     │
│  - 调用 TTS 服务的 REST API                                   │
│  - 将结果返回给 AI                                            │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP 请求
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              TTS 服务 (现有项目)                              │
│              python -m uvicorn src.qwen3_tts_api.main:app   │
│              运行在 localhost:8001                           │
└─────────────────────────────────────────────────────────────┘
```

## 前置条件

1. **启动 TTS 服务**
   ```bash
   cd qwen3-tts-api
   python -m uvicorn src.qwen3_tts_api.main:app --host 0.0.0.0 --port 8001
   ```

2. **启动 MCP Server**
   ```bash
   cd qwen3-tts-api
   PYTHONPATH=. python -m qwen3_tts_mcp.server
   ```

## MCP 工具

| 工具名 | API 端点 | 功能 | 耗时操作 |
|--------|----------|------|----------|
| `text_split` | POST `/text/split` | 将长文本拆分为短片段 | - |
| `reference_list` | GET `/tts/reference/list` | 列出所有参考音频 | - |
| `tts_generate` | POST `/tts/generate` | 使用参考音频生成语音 | ✓ |
| `audio_merge` | POST `/audio/merge` | 合并多个音频片段 | - |

### 1. text_split

将长文本拆分为适合 TTS 处理的短片段。

**输入参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| text | string | 是 | - | 要拆分的文本 |
| max_length | integer | 否 | 200 | 单个片段最大字符数 (10-2000) |
| min_chunk_length | integer | 否 | 50 | 合并短片段的最小长度 (1-500) |

**返回：**
```json
{
  "success": true,
  "chunks": ["片段1", "片段2", "片段3"],
  "chunk_count": 3,
  "original_length": 500,
  "max_length": 200
}
```

### 2. reference_list

列出所有已保存的参考音频。

**输入参数：** 无

**返回：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "tianyuan",
      "language": "Chinese",
      "ref_text": "参考文本内容...",
      "exaggeration": 0.5,
      "temperature": 0.8,
      "speed_rate": 1.0,
      "instruct": "语音风格指令"
    }
  ]
}
```

### 3. tts_generate

使用保存的参考音频生成语音。这是一个耗时操作，AI 工具会等待处理完成。

**输入参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 要转换的文本 |
| reference_name | string | 是* | 参考音频名称（与 reference_id 二选一） |
| reference_id | integer | 是* | 参考音频 ID（与 reference_name 二选一） |
| ref_text | string | 是 | 参考音频对应的文本描述 |
| language | string | 否 | 语言（默认 Auto） |
| exaggeration | float | 否 | 情感夸张程度 0.0-1.0（覆盖参考音频默认值） |
| temperature | float | 否 | 采样温度 0.0-1.0（覆盖参考音频默认值） |
| instruct | string | 否 | 语音风格指令（覆盖参考音频默认值） |
| speed_rate | float | 否 | 语速倍率 0.5-2.0（覆盖参考音频默认值） |
| output_dir | string | 否 | 保存目录（不指定则返回二进制） |

**注意：**
- `ref_text` 为必填字段，描述参考音频的内容
- 如果未指定 `exaggeration`、`temperature`、`instruct`、`speed_rate`，会自动使用参考音频保存的默认值

**返回：**
- 指定 output_dir：保存音频文件，返回文件路径
- 未指定：返回音频二进制

### 4. audio_merge

合并多个音频片段为一个音频文件。合并后的文件保存在 output 目录，可通过 `/audio/{filename}` 访问。

**输入参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| files | string[] | 是 | 要合并的音频文件路径列表（至少2个） |
| output_dir | string | 否 | 保存目录（不指定则返回二进制） |

**返回：**
- 指定 output_dir：保存音频文件，返回文件路径
- 未指定：返回音频二进制

**注意**: 合并后的文件会自动保存到 output 目录，通过返回的音频可获取文件名，然后通过 `http://localhost:8001/audio/{filename}` 访问。

## AI 工作流示例

### 场景：将长文本转化为音频

```
用户: "将这段文字转化为音频"

AI 工作流:
1. text_split(长文本) 
   → 返回片段数组 ["片段1", "片段2", "片段3"]

2. 循环调用 tts_generate(每个片段)
   → 生成 1.wav, 2.wav, 3.wav

3. audio_merge([1.wav, 2.wav, 3.wav])
   → 合并为 merged_xxx.wav，保存到 output 目录

4. 返回给用户: "音频已生成: http://localhost:8001/audio/merged_xxx.wav"
```

### 场景：保存到指定目录

```
用户: "将这段文字保存到 /tmp/tts 目录"

AI 工作流:
1. text_split(长文本)
2. 循环 tts_generate(每个片段, output_dir=/tmp/tts)
3. audio_merge(files=[/tmp/tts/1.wav, ...], output_dir=/tmp/tts)
4. 返回: "音频已保存到 /tmp/tts/output.wav"
```

## 配置 opencode

在 opencode 配置文件中添加 MCP Server。编辑 `~/.config/opencode/opencode.json`：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "qwen3-tts": {
      "type": "local",
      "command": ["uv", "run", "python", "-m", "qwen3_tts_mcp.server"],
      "environment": {
        "PYTHONPATH": "/Volumes/data/dev/code/ai/qwen3-tts-api",
        "TTS_BASE_URL": "http://localhost:8001"
      }
    }
  }
}
```

**配置说明：**
- `type`: 使用本地 MCP 服务器
- `command`: 使用 uv run 启动（会自动读取项目依赖）
- `environment`: 环境变量

**重启 opencode 后生效。**

使用方式：在提示词中直接说 "将这段文字转为语音"

## 依赖

MCP Server 依赖：
- `mcp[fastapi]` >= 1.0.0
- `httpx` >= 0.27.0
- `pydantic` >= 2.0.0

## 目录结构

```
qwen3-tts-api/
├── docs/
│   └── MCP.md                    # 本文档
├── qwen3_tts_mcp/
│   ├── __init__.py
│   ├── server.py                  # FastMCP 主入口
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── text_split.py
│   │   ├── reference.py
│   │   ├── tts_generate.py
│   │   └── audio_merge.py
│   └── pyproject.toml             # MCP 依赖
└── src/
    └── qwen3_tts_api/
        └── api/routes/
            └── audio_merge.py     # 现有接口 + upload
```

## 扩展

### 添加新工具

1. 在 `qwen3_tts_mcp/tools/` 目录创建新工具文件
2. 实现工具函数，使用 `@mcp.tool` 装饰器
3. 在 `qwen3_tts_mcp/server.py` 中导入并注册

### 修改 API 地址

修改 `qwen3_tts_mcp/server.py` 中的常量：
```python
TTS_BASE_URL = "http://localhost:8001"  # 修改为实际地址
```
