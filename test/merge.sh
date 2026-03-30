#!/usr/bin/env bash

COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_NC='\033[0m'

BASE_URL="http://localhost:8001"
OUTPUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${COLOR_GREEN}[3/3]${COLOR_NC} 调用 /audio/merge 接口合并音频..."

AUDIO_FILES=()
for f in "${OUTPUT_DIR}"/[0-9]*.wav; do
  if [ -f "$f" ]; then
    SIZE=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
    if [ "$SIZE" -gt 1000 ]; then
      AUDIO_FILES+=("$f")
    else
      echo -e "${COLOR_YELLOW}  跳过无效文件: $(basename "$f") ($SIZE bytes)${COLOR_NC}"
    fi
  fi
done

if [ ${#AUDIO_FILES[@]} -eq 0 ]; then
  echo -e "${COLOR_RED}Error: 没有找到要合并的音频文件${COLOR_NC}"
  exit 1
fi

echo "找到 ${#AUDIO_FILES[@]} 个音频文件需要合并"

MERGE_FILES=()
for f in "${AUDIO_FILES[@]}"; do
  MERGE_FILES+=("-F")
  MERGE_FILES+=("files=@$f")
done

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
