# NaniShiteruSensei
Offline Japanese lecture transcriber + note generator for students who have no idea what Sensei is saying.

### _"Sensei… what the hell are you saying?"_  
A fully offline Japanese lecture transcriber + note generator for students who have no idea what Sensei is saying.

NaniShiteruSensei is designed for students in Japanese universities (especially international students) who struggle with fast, unclear, mumbled, or chaotic lectures.

This toolkit listens to your lecture audio → transcribes it → converts it into clean study notes → (optionally) translates it to English.

All free. All offline. All suffering included.

---

## Features

- **Whisper-based transcription**
  - Forces Japanese language (`language=ja`)
  - Forces transcription mode (`task="transcribe"`)
  - Automatic chunking for long audio files (1–2 hours)
  - Handles .m4a / .mp3 / .wav

- **Japanese lecture note generator (Ollama)**
  Produces structured notes with:
  - 今日のテーマ  
  - 重要キーワード  
  - 理解ポイント  
  - 試験に出そうなところ  
  - Definitions Cheat Sheet  
  - 要点5行まとめ  
  - Q&A Flashcards  
  - メモ：先生の強調ポイント  

- **Optional JP → EN translator (Ollama)**
  - Accurate academic translation
  - Preserves technical terms
  - Fully offline

- **100% offline**
  Whisper + LLaMA run locally, so no API keys required.

- **Optimized for Apple Silicon (M1–M4)**
  - Fast MPS acceleration
  - Perfect for long lecture recordings

---

## Quick Start

### 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
brew install ffmpeg
````

### 2️⃣ Install Whisper

```bash
pip install openai-whisper
```

### 3️⃣ Install Ollama

Download from:
[https://ollama.com/](https://ollama.com/)

Then pull a model (recommended):

```bash
ollama pull llama3.1
```

---

##  Project Structure
```
NaniShiteruSensei/
│
├── transcribe_lecture.py          # Whisper transcription (Japanese forced)
├── lecture_notes_ollama.py        # Japanese lecture note generator
├── translate_jp_to_en_ollama.py   # JP → EN translator
├── requirements.txt
└── examples/
    ├── sample_transcript.txt
    └── sample_notes.txt
```
---

##  1. Transcribe Your Lecture

Put your audio file in the folder, then run:

```bash
python transcribe_lecture.py "Week7.m4a"
```

This creates:

```
Week7_transcript_ja.txt
```

---

## 2. Generate Lecture Notes (Japanese)

```bash
python lecture_notes_ollama.py "Week7_transcript_ja.txt"
```

This outputs:

```
Week7_transcript_ja_NOTES_ollama.txt
```

---

## 3. Optional: Translate JP → EN

```bash
python translate_jp_to_en_ollama.py "Week7_transcript_ja.txt"
```

Produces:

```
Week7_transcript_ja_EN.txt
```

---

##  Example Output

```
### 今日のテーマ
本講義では〜〜〜について説明された。特に〇〇の歴史的背景と役割が強調された。

### 重要キーワード
・〇〇：〜〜〜  
・△△：〜〜〜  
・□□：〜〜〜  
```

More examples available in `/examples`.

---

## Why This Exists

Because sometimes lectures sound like:

> 「えー……こちらが……あー……まぁ大事です。」

and you're sitting there thinking:

> **なにしてる先生？？？？？**

This tool helps students who:

* study in Japanese as a 2nd/3rd language
* struggle with unclear lectures
* need transcripts for later review
* want exam-focused summaries
* want to understand what Sensei is actually saying

---

## Future Improvements

* GUI version
* PDF export
* Slide extraction
* Multiple summary levels (N3/N2/N1 difficulty)
* Keyword frequency graphs

---

## 📄 License

MIT License — free to use, remix, and improve.

---

## ⭐ Support

If this project saves your GPA, consider giving it a ⭐ on GitHub!
