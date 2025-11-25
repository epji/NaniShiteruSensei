import argparse
import pathlib
import requests


def call_ollama(prompt: str,
                model: str = "llama3.1",
                host: str = "http://localhost:11434") -> str:
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    resp = requests.post(url, json=payload, timeout=600)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()


def load_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Translate a Japanese text file into English using a local Ollama model."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the Japanese .txt file (e.g., Week 7_transcript_ja.txt)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3.1",
        help="Ollama model name (default: llama3.1)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="http://localhost:11434",
        help="Ollama host URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=3500,
        help="Approximate max characters per translation chunk (default: 3500)",
    )

    args = parser.parse_args()

    input_path = pathlib.Path(args.input_file)
    if not input_path.exists():
        print(f"File not found: {input_path}")
        return

    jp_text = load_text(input_path)

    # Simple manual chunking so we don't blow context limit
    text = jp_text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = text.split("\n\n")
    chunks = []
    current = []
    cur_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if cur_len + len(para) + 2 > args.max_chars and current:
            chunks.append("\n\n".join(current))
            current = [para]
            cur_len = len(para) + 2
        else:
            current.append(para)
            cur_len += len(para) + 2

    if current:
        chunks.append("\n\n".join(current))

    print(f"🔤 Translating {len(chunks)} chunk(s) JP → EN ...")

    translated_chunks = []
    for i, ch in enumerate(chunks, start=1):
        print(f"  → Chunk {i}/{len(chunks)}")
        prompt = f"""You are a careful bilingual assistant.

Translate the following Japanese academic text into clear, natural English.
It is a university lecture transcript or notes.

Requirements:
- Preserve technical terms (names, places, era names) accurately.
- Use full sentences.
- Keep paragraph breaks where it makes sense.
- Do NOT summarize; translate as faithfully as possible.
- Do NOT add explanations or comments, just the translation.

[Japanese text begins]
{ch}
[Japanese text ends]

Now provide the English translation:
"""
        en = call_ollama(prompt, model=args.model, host=args.host)
        translated_chunks.append(en)

    out_path = input_path.with_name(input_path.stem + "_EN.txt")
    out_path.write_text("\n\n".join(translated_chunks), encoding="utf-8")

    print("✅ Done!")
    print(f"Translated file saved to: {out_path}")


if __name__ == "__main__":
    main()
