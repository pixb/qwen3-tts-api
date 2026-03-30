#!/usr/bin/env bash

COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
FILE_NAME="$(basename "${BASH_SOURCE[0]}" .sh)"

TEXT=$(
  cat <<'EOF'
我在骑车时听播客，听到 Godot 的核心开发者抱怨：自从程序员大量使用 AI 之后，Godot 大部分提交的 PR 都是 AI 生成的，提交者甚至不看具体内容，这严重占据了维护者的精力。再联想到前几天 Linus 拒绝了 MMC 驱动的合并请求，未将其纳入 Linux 内核主线，原因是提交者同样使用 AI 生成代码，结果根本无法运行，简直把 Linus 当成了测试人员。还有一个叫 Gentoo 的 Linux 发行版，也遭遇了类似 AI "DDoS 攻击" 的事件——机器人疯狂提交 PR，导致核心开发者身心俱疲。
当然，我不是为了给这些用 AI 提交代码的人洗地，但从另一个方面来说，Git 可能已经不适合 AI 编程的时代了。
程序员不能没有大模型，就像西方不能没有耶路撒冷。听说，榜一大哥目前无法解决的问题是：打赏一停，爱情归零；AI 编程目前无法解决的问题是：会话一停，推理归零。我们往往“只知代码发生了改变，却不知代码为何发生改变”。
EOF
)

REFERENCE_NAME="tianyuan"

BASE_URL="http://localhost:8001"
OUTPUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${COLOR_GREEN}[1/3]${COLOR_NC} 调用 /text/split 接口拆分文本..."

MAX_LENGTH=250

SPLIT_RESPONSE=$(curl -s -X POST "${BASE_URL}/text/split" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg text "$TEXT" --argjson max_length "$MAX_LENGTH" '{text: $text, max_length: $max_length}')")

echo "拆分响应: $SPLIT_RESPONSE"

CHUNKS=$(echo "$SPLIT_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('\n'.join(data.get('chunks', [])))
" 2>/dev/null || echo "$SPLIT_RESPONSE" | grep -oP '"chunks":\s*\[\s*(\K[^\]]+)' | tr ',' '\n' | sed 's/"//g')

if [ -z "$CHUNKS" ]; then
  echo -e "${COLOR_RED}Error: 无法解析拆分结果${COLOR_NC}"
  exit 1
fi

CHUNK_ARRAY=()
while IFS= read -r line; do
  [ -n "$line" ] && CHUNK_ARRAY+=("$line")
done <<<"$CHUNKS"

echo -e "${COLOR_GREEN}拆分完成，共 ${#CHUNK_ARRAY[@]} 个片段${COLOR_NC}"

echo -e "${COLOR_GREEN}[1.5/3]${COLOR_NC} 查询预设 ${REFERENCE_NAME} 的参数..."

REF_RESPONSE=$(curl -s -X GET "${BASE_URL}/tts/reference/list")
echo "预设列表响应: $REF_RESPONSE"

REFERENCE_DATA=$(echo "$REF_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
refs = data.get('data', [])
target = '$REFERENCE_NAME'
for ref in refs:
    if ref.get('name') == target:
        print(json.dumps(ref))
        break
" 2>/dev/null)

if [ -z "$REFERENCE_DATA" ]; then
  echo -e "${COLOR_RED}Error: 未找到预设 ${REFERENCE_NAME}${COLOR_NC}"
  exit 1
fi

REF_ID=$(echo "$REFERENCE_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
REF_TEXT=$(echo "$REFERENCE_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ref_text',''))")
REF_EXAGGERATION=$(echo "$REFERENCE_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('exaggeration',0.5))")
REF_TEMPERATURE=$(echo "$REFERENCE_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('temperature',0.8))")
REF_SPEED_RATE=$(echo "$REFERENCE_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('speed_rate',1.0))")
REF_INSTRUCT=$(echo "$REFERENCE_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('instruct','') or '')")
REF_LANGUAGE=$(echo "$REFERENCE_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('language','') or 'Auto')")

echo -e "${COLOR_GREEN}预设参数: id=${REF_ID}, ref_text=${REF_TEXT:0:30}..., exaggeration=${REF_EXAGGERATION}, temperature=${REF_TEMPERATURE}, speed_rate=${REF_SPEED_RATE}, language=${REF_LANGUAGE}${COLOR_NC}"

echo -e "${COLOR_GREEN}[2/3]${COLOR_NC} 循环调用 /tts/generate 接口生成音频..."

AUDIO_FILES=()
for i in "${!CHUNK_ARRAY[@]}"; do
  CHUNK="${CHUNK_ARRAY[$i]}"
  echo -e "${COLOR_YELLOW}  生成第 $((i + 1))/${#CHUNK_ARRAY[@]} 个片段...${COLOR_NC}"

  OUTPUT_FILE="${OUTPUT_DIR}/$((i + 1)).wav"

  INSTRUCT_FLAG=""
  if [ -n "$REF_INSTRUCT" ]; then
    INSTRUCT_FLAG="-F"
    INSTRUCT_FLAG="$INSTRUCT_FLAG instruct=$REF_INSTRUCT"
  fi

  CURL_CMD=(curl -s -X POST "${BASE_URL}/tts/generate")
  CURL_CMD+=(-F "text=${CHUNK}")
  CURL_CMD+=(-F "reference_id=${REF_ID}")
  CURL_CMD+=(-F "reference_name=${REFERENCE_NAME}")
  CURL_CMD+=(-F "ref_text=${REF_TEXT}")
  CURL_CMD+=(-F "language=${REF_LANGUAGE}")
  CURL_CMD+=(-F "exaggeration=${REF_EXAGGERATION}")
  CURL_CMD+=(-F "temperature=${REF_TEMPERATURE}")
  CURL_CMD+=(-F "speed_rate=${REF_SPEED_RATE}")
  if [ -n "$REF_INSTRUCT" ]; then
    CURL_CMD+=(-F "instruct=${REF_INSTRUCT}")
  fi
  CURL_CMD+=(-o "$OUTPUT_FILE")

  "${CURL_CMD[@]}"

  if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    AUDIO_FILES+=("$OUTPUT_FILE")
    echo -e "    ${COLOR_GREEN}✓${COLOR_NC} 保存为 $((i + 1)).wav"
  else
    echo -e "    ${COLOR_RED}✗${COLOR_NC} 生成失败"
    rm -f "$OUTPUT_FILE"
  fi
done

if [ ${#AUDIO_FILES[@]} -eq 0 ]; then
  echo -e "${COLOR_RED}Error: 没有生成任何音频文件${COLOR_NC}"
  exit 1
fi

echo -e "${COLOR_GREEN}[3/3]${COLOR_NC} 调用 /audio/merge 接口合并音频..."

MERGE_FILES=()
for f in "${AUDIO_FILES[@]}"; do
  SIZE=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
  if [ "$SIZE" -gt 1000 ]; then
    MERGE_FILES+=("-F")
    MERGE_FILES+=("files=@$f")
  else
    echo -e "${COLOR_YELLOW}  跳过无效文件: $(basename "$f") ($SIZE bytes)${COLOR_NC}"
  fi
done

if [ $((${#MERGE_FILES[@]} / 2)) -lt 2 ]; then
  echo -e "${COLOR_RED}Error: 有效的音频文件少于2个，无法合并${COLOR_NC}"
  exit 1
fi

curl -s -X POST "${BASE_URL}/audio/merge" \
  "${MERGE_FILES[@]}" \
  -o "${OUTPUT_DIR}/output.wav"

if [ -f "${OUTPUT_DIR}/output.wav" ] && [ -s "${OUTPUT_DIR}/output.wav" ]; then
  echo -e "${COLOR_GREEN}✓${COLOR_NC} 合并完成，保存为 output.wav"

  echo -e "${COLOR_GREEN}片段音频文件已保留在: ${OUTPUT_DIR}/${COLOR_NC}"
  ls -la "${OUTPUT_DIR}"/[0-9]*.wav 2>/dev/null | awk '{print "  " $NF " (" $5 " bytes)"}'

  echo -e "${COLOR_GREEN}完成!${COLOR_NC}"
else
  echo -e "${COLOR_RED}Error: 合并失败${COLOR_NC}"
  exit 1
fi
