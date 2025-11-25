import argparse
import pathlib
import requests


# =========================
# Ollama client
# =========================

def call_ollama(prompt: str,
                model: str = "llama3.1",
                host: str = "http://localhost:11434") -> str:
    """
    Call a local Ollama model with the given prompt and return the response text.
    Requires Ollama to be installed and running.
    """
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


# =========================
# Text utilities
# =========================

def load_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def chunk_text(text: str, max_chars: int = 3500) -> list[str]:
    """
    Roughly chunk text by character length so it fits in the model context.
    Tries to split on line boundaries.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    chunks = []
    current = []
    current_len = 0

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            line = ""

        if current_len + len(line) + 1 > max_chars and current:
            chunks.append("\n".join(current).strip())
            current = [line]
            current_len = len(line) + 1
        else:
            current.append(line)
            current_len += len(line) + 1

    if current:
        chunks.append("\n".join(current).strip())

    return [c for c in chunks if c]


# =========================
# Summarization pipeline
# =========================

def summarize_chunk(chunk_text: str,
                    part_idx: int,
                    total_parts: int,
                    model: str,
                    host: str) -> str:
    """
    Ask the model for a short bullet summary of one chunk.
    """
    prompt = f"""あなたは日本の大学講義ノートを作るアシスタントです。
以下は講義文字起こしの一部です。（Part {part_idx}/{total_parts}）

この部分だけについて、後で全体をまとめるための「メモ用の箇条書き」を作ってください。

条件:
- 日本語で書く
- 箇条書き 3〜6 個
- 重要な用語・人名・地名・時代名はできるだけそのまま残す
- 簡潔に要点だけまとめる
- 文章の順番は、流れが分かりやすいように並べる

=== Transcript Part {part_idx}/{total_parts} ===
{chunk_text}
==========================================

出力は、日本語の箇条書きだけにしてください。
「Part ○○」などの余計なヘッダーや説明文は書かないでください。
"""

    return call_ollama(prompt, model=model, host=host)


def build_final_notes_from_summaries(summaries: list[str],
                                     model: str,
                                     host: str) -> str:
    """
    Given a list of chunk-level summaries, ask the model to create
    the full structured lecture notes (JP only).
    """
    merged_summaries = "\n\n".join(
        f"[Part {i+1}]\n{summaries[i]}"
        for i in range(len(summaries))
    )

    prompt = f"""あなたは、日本の大学で勉強している留学生のための
「分かりやすい講義ノート作成アシスタント」です。

以下に、講義全体の要約メモ（各パートごとの箇条書き）が与えられます。
これらをもとに、１つの講義ノートを作ってください。

学生は:
- 日本語が第３言語
- テスト対策とレポート作成に使いたい
- 歴史や概念の因果関係を理解したい
- 重要な用語は日本語でしっかり覚えたい

出力フォーマットは**必ず**次の見出し・順番で作ってください。
見出しは「### 見出し名」の形で書いてください。

1. 今日のテーマ
2. 重要キーワード
3. 理解ポイント
4. 試験に出そうなところ
5. Definitions Cheat Sheet
6. 要点5行まとめ
7. Q&A Flashcards
8. メモ：先生の強調ポイント

それぞれのセクションの指示:

### 今日のテーマ
- 講義全体が何についてだったかを、日本語で2〜4文でまとめる。

### 重要キーワード
- 箇条書き。
- 形式の例:
  ・用語: 日本語で1〜2行の説明
- 人名・地名・時代名・概念を中心に。

### 理解ポイント
- 日本語で、因果関係や流れが分かるように説明。
- 箇条書きでも短い段落でもOK。
- 「なぜ〜が起きたか」「どの勢力がどう動いたか」「結果どうなったか」を意識する。

### 試験に出そうなところ
- 記述式や小論文で出そうな設問を日本語で3〜6個作る。
- 「〜について説明せよ」「〜の特徴を述べよ」などの形。

### Definitions Cheat Sheet
- 用語辞書（超短く）。
- 形式:
  用語: 一言で意味（日本語）
- 5〜10語程度でOK。

### 要点5行まとめ
- 日本語で5つの文にまとめる。
- ①〜⑤の番号付きで。

### Q&A Flashcards
- 暗記用の質問と答えを3〜8セット作る。
- 形式:
  Q: （日本語の質問）
  A: （日本語の答え）

### メモ：先生の強調ポイント
- 講義の中で強調されていそうなテーマや、何度も出てきた考え方を日本語で箇条書き。

--------------------------------
【講義メモ（パートごと）】
{merged_summaries}
--------------------------------

それでは、指示したフォーマットに従って講義ノートを作成してください。
"""

    return call_ollama(prompt, model=model, host=host)


# =========================
# Main CLI
# =========================

def main():
    parser = argparse.ArgumentParser(
        description="Generate structured JP-only lecture notes from a Japanese transcript using a local Ollama model."
    )
    parser.add_argument(
        "transcript_file",
        type=str,
        help="Path to the transcript .txt file (e.g., Week 7_transcript_ja.txt)",
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
        "--chunk-chars",
        type=int,
        default=3500,
        help="Approximate max characters per chunk before summarizing (default: 3500)",
    )

    args = parser.parse_args()

    transcript_path = pathlib.Path(args.transcript_file)
    if not transcript_path.exists():
        print(f"File not found: {transcript_path}")
        return

    print(f"📖 Loading transcript: {transcript_path.name}")
    text = load_text(transcript_path)

    print("🔪 Splitting transcript into chunks...")
    chunks = chunk_text(text, max_chars=args.chunk_chars)
    print(f"  → {len(chunks)} chunk(s)")

    # 1) Summarize each chunk
    summaries = []
    for i, chunk in enumerate(chunks, start=1):
        print(f"📝 Summarizing chunk {i}/{len(chunks)} ...")
        summary = summarize_chunk(
            chunk,
            part_idx=i,
            total_parts=len(chunks),
            model=args.model,
            host=args.host,
        )
        summaries.append(summary)

    # 2) Build final notes
    print("📚 Building final structured notes from chunk summaries...")
    final_notes = build_final_notes_from_summaries(
        summaries,
        model=args.model,
        host=args.host,
    )

    # 3) Save output
    out_path = transcript_path.with_name(
        transcript_path.stem + "_NOTES_ollama.txt"
    )
    out_path.write_text(final_notes, encoding="utf-8")

    print("✅ Done!")
    print(f"Notes saved to: {out_path}")


if __name__ == "__main__":
    main()
