# 使用 pydub 自动剔除非语音段（基于音量阈值）
import argparse
from pydub import AudioSegment
from pydub.silence import detect_nonsilent


def clean_audio(input_path: str, output_path: str, max_duration_ms: int = 12000, 
                silence_thresh: int = -40, min_silence_len: int = 500):
    ext = input_path.split(".")[-1].lower()
    audio = AudioSegment.from_file(input_path, format=ext)

    nonsilent_ranges = detect_nonsilent(
        audio, 
        min_silence_len=min_silence_len, 
        silence_thresh=silence_thresh
    )

    if not nonsilent_ranges:
        print("No speech segments detected, keeping original audio")
        audio.export(output_path, format="wav")
        return

    clean_audio = AudioSegment.empty()
    for start, end in nonsilent_ranges:
        clean_audio += audio[start:end]

    original_len = len(clean_audio)
    if original_len > max_duration_ms:
        clean_audio = clean_audio[:max_duration_ms]
        print(f"Audio truncated from {original_len}ms to {max_duration_ms}ms")

    clean_audio.export(output_path, format="wav")
    print(f"Cleaned audio saved to {output_path} ({len(clean_audio)}ms)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean audio by removing non-speech segments")
    parser.add_argument("input", help="Input audio file path")
    parser.add_argument("output", help="Output audio file path")
    parser.add_argument("--max-duration", type=int, default=12000, help="Max duration in milliseconds (default: 12000)")
    args = parser.parse_args()

    clean_audio(args.input, args.output, args.max_duration)
