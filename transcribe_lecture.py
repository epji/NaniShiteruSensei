import argparse
import subprocess
import pathlib
import sys

import whisper
import torch
import re


def split_audio(input_path: pathlib.Path, chunk_seconds: int = 600) -> list[pathlib.Path]:
    """
    Use ffmpeg to split audio into N-second chunks.
    Returns list of chunk file paths.
    """
    chunk_dir = input_path.parent / f"{input_path.stem}_chunks"
    chunk_dir.mkdir(exist_ok=True)

    # use .m4a so we can copy the original AAC audio without re-encoding
    output_pattern = chunk_dir / "chunk_%03d.m4a"

    cmd = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-c",
        "copy",  # copy AAC into m4a segments
        str(output_pattern),
    ]

    print("▶️ Splitting audio with ffmpeg...")
    subprocess.run(cmd, check=True)

    chunks = sorted(chunk_dir.glob("chunk_*.m4a"))
    if not chunks:
        print("No chunks were created. Check your input file.")
        sys.exit(1)

    print(f"🎧 Created {len(chunks)} chunks in {chunk_dir}")
    return chunks


def looks_like_japanese(text: str, threshold: float = 0.3) -> bool:
    """
    Very rough heuristic:
    Return True if at least `threshold` fraction of characters
    are Japanese (hiragana/katakana/kanji).
    """
    if not text:
        return False

    jp_chars = re.findall(r"[ぁ-んァ-ン一-龯]", text)
    ratio = len(jp_chars) / max(len(text), 1)
    return ratio >= threshold


def transcribe_chunks(
    chunks: list[pathlib.Path],
    model_name: str = "large",
    language: str = "ja",
) -> str:
    """
    Transcribe each chunk with Whisper and return the combined transcript as a string.
    Forces:
      - language = Japanese
      - task = transcribe (no translation)
    Uses MPS on Apple Silicon if available.
    """
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"🧠 Loading Whisper model '{model_name}' on device '{device}'...")
    model = whisper.load_model(model_name, device=device)

    all_texts = []

    for i, chunk_path in enumerate(chunks, start=1):
        print(f"📝 [{i}/{len(chunks)}] Transcribing {chunk_path.name} ...")

        # Force Japanese + transcription mode
        result = model.transcribe(
            str(chunk_path),
            language=language,
            task="transcribe",
            fp16=False,
        )
        text = result.get("text", "").strip()

        # Optional tiny filter: skip completely non-Japanese gibberish
        if not text:
            print("   ↳ (empty result, skipping)")
            continue
        if not looks_like_japanese(text):
            print("   ↳ (looks non-Japanese / noisy, keeping but marking)")
            all_texts.append(f"\n[? 非日本語っぽいチャンク {i}] {text}\n")
            continue

        all_texts.append(f"\n----- [Chunk {i}] {chunk_path.name} -----\n{text}\n")

    full_text = "\n".join(all_texts).strip()
    return full_text


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe long Japanese lecture audio using Whisper with chunking (forced Japanese)."
    )
    parser.add_argument(
        "audio_file",
        type=str,
        help="Path to the lecture audio file (mp3/m4a/wav/etc.)",
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=600,
        help="Chunk length in seconds (default: 600 = 10 min)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="large",
        help="Whisper model name (e.g., tiny, base, small, medium, large)",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="ja",
        help="Language code to force (default: ja for Japanese)",
    )

    args = parser.parse_args()

    audio_path = pathlib.Path(args.audio_file)
    if not audio_path.exists():
        print(f"Input file not found: {audio_path}")
        sys.exit(1)

    # 1) Split
    chunks = split_audio(audio_path, chunk_seconds=args.chunk)

    # 2) Transcribe with forced Japanese + transcribe mode
    full_text = transcribe_chunks(
        chunks,
        model_name=args.model,
        language=args.language,
    )

    # 3) Save final transcript
    out_path = audio_path.with_name(audio_path.stem + "_transcript_ja.txt")
    out_path.write_text(full_text, encoding="utf-8")

    print("✅ Transcription complete.")
    print(f"Final transcript saved to: {out_path}")


if __name__ == "__main__":
    main()
