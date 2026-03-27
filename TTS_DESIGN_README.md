# TTS Voice Design Management System

## 概述

语音设计管理系统，用于上传、管理和保存参考音频文件。

## 目录结构

```
qwen3-tts-api/
├── api.py                      # 主 API 文件
├── tts_design_db.py            # SQLite 数据库模块
├── tts_design_routes.py        # 语音设计管理路由
├── init_sample_data.py         # 初始化示例数据脚本
├── data/
│   └── tts_designs.db          # SQLite 数据库
├── res/
│   └── audio/                  # 上传音频存储目录
│       ├── liuyandong.mp3     # 示例音频 1
│       └── tianyuan.mp3       # 示例音频 2
```

## 数据模型

### tts_designs 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增主键 |
| name | TEXT | 音频名称 |
| file_path | TEXT | 文件路径 |
| language | TEXT | 语言（可选） |
| description | TEXT | 描述（可选） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

## API 接口

### 1. 上传音频

```
POST /tts/design/upload
Content-Type: multipart/form-data

参数:
- name: 音频名称 (必填)
- file: 音频文件 (必填，支持 mp3/wav/m4a/flac/ogg/aac)
- language: 语言 (可选)
- description: 描述 (可选)
```

### 2. 列出所有音频

```
GET /tts/design/designs
```

### 3. 获取单个音频详情

```
GET /tts/design/designs/{id}
```

### 4. 下载音频文件

```
GET /tts/design/designs/{id}/audio
```

### 5. 更新音频信息

```
POST /tts/design/designs/{id}
Content-Type: multipart/form-data

参数:
- name: 新名称 (可选)
- language: 语言 (可选)
- description: 描述 (可选)
```

### 6. 删除音频

```
DELETE /tts/design/designs/{id}
```

## 启动服务

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动服务
uvicorn api:app --host 0.0.0.0 --port 8001
```

## 初始化示例数据

```bash
python init_sample_data.py
```

## 测试示例

```bash
# 列出所有音频
curl http://localhost:8001/tts/design/designs

# 获取单个音频
curl http://localhost:8001/tts/design/designs/1

# 上传音频
curl -X POST http://localhost:8001/tts/design/upload \
  -F "name=我的声音" \
  -F "file=@/path/to/audio.mp3" \
  -F "language=Chinese"

# 更新音频
curl -X POST http://localhost:8001/tts/design/designs/1 \
  -F "name=新名称"

# 删除音频
curl -X DELETE http://localhost:8001/tts/design/designs/1
```
