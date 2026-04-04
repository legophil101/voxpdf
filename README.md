---
title: VoxPDF
emoji: 📚
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

<!-- Hugging Face Spaces configuration above -->

# 🎧 VoxPDF v1.1 – PDF to Audiobook Generator

A robust, full-stack web application that converts PDF documents into **natural-sounding audiobooks** using an
asynchronous processing pipeline.

🌐 **Live Demo:**  
👉 https://huggingface.co/spaces/legophil101/VoxPDF

---

## 📌 Overview

PDFs are designed for visual layout—not for listening.

VoxPDF transforms PDFs into a **single continuous audiobook**, while intelligently handling:

- Broken formatting
- Repeating headers/footers
- Inconsistent chapter structures
- Hidden artifacts that break TTS

Instead of aiming for perfect parsing (which is unrealistic), this system focuses on **robustness, stability, and
real-world usability**.

---

## ♿ Why This Matters (Real Use Cases)

This project is not just a utility—it’s an **accessibility and productivity tool**.

### Accessibility

- Enables **hands-free reading** for users with:
    - Physical limitations (e.g., injury, mobility constraints)
    - Eye strain or visual fatigue
- Converts static documents into **auditory learning experiences**

### Everyday Use Cases

- 🎧 Listen while commuting or walking
- 🏋️ Learn while exercising
- 📚 Consume long-form content passively
- 🧠 Reinforce learning through audio repetition

This aligns with real-world needs where **time, attention, and physical constraints matter**.

---

## 🎥 Demo Flow

1. Upload a PDF
2. Wait on the live progress page
3. Download your audiobook

---

## 🚀 Key Features (v1.1)

- 📄 **PDF Upload via Web Interface**
- 🧠 **Dual-Mode Extraction Engine**
    - **Clean Mode:** Removes noise for smooth narration
    - **Raw Mode:** Preserves full content for dense PDFs
- 🔊 **Expanded Voice Support**
    - US, UK, and **Philippine voices (Filipino-compatible)**
    - Male and female options
- ⚡ **Asynchronous Background Processing (Non-blocking)**
- 📊 **Real-Time Progress Tracking (Chunk-Based)**
- 🎧 **Single Continuous Audiobook Output**
- 🧹 **Automatic Temporary File Cleanup**
- 🧱 **Job-Based Isolation for Multi-User Safety**
- 🎨 **Improved UI Feedback**
    - Fixed flash messages (Hugging Face + mobile)
    - Clearer error states

---

## ⚙️ Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Backend          | Python, Flask, Threading            |
| PDF Processing   | pdfplumber, Advanced Regex          |
| TTS Engine       | Microsoft Edge TTS (edge-tts)       |
| Audio Processing | FFmpeg, pydub                       |
| Frontend         | HTML5, CSS3, Bootstrap, Vanilla JS  |
| File Handling    | Job-based isolation, `/tmp` routing |
| Deployment       | Docker, Hugging Face Spaces         |

---

## 🧠 System Architecture

Designed to handle long-running workloads **without freezing the UI or crashing the server**.

### 1. Job-Based Isolation

- Each upload gets a unique **job ID**
- Runs in its own workspace
- Prevents file conflicts between users

---

### 2. Asynchronous Background Processing

- Flask immediately responds
- Heavy work runs in a **background thread**
- User is redirected to a progress page

---

### 3. Chunk-Based Processing

- Text is split into manageable chunks
- Each chunk is processed independently

**Why this matters:**

- Prevents large-input failures
- Improves TTS reliability
- Enables scalable processing

---

### 4. Real-Time Progress Tracking (v1.1 Upgrade)

- Frontend polls `/status/<job_id>`
- Tracks **actual chunk progress**
- Displays more accurate feedback instead of a simple loader

---

### 5. Audio Merge & Cleanup

- Chunks merged via FFmpeg
- Temporary files deleted automatically
- Only final audiobook remains

---

## 🧹 PDF Processing Engine (Core Highlight)

Handling real-world PDFs is the hardest part of this project.

### Dual-Mode Strategy

- **Clean Mode**
    - Removes headers, footers, and noise
    - Best for books and long-form reading

- **Raw Mode**
    - Preserves all extracted text
    - Useful for study materials and dense layouts

---

### Capabilities

- 🔁 Removes repeating headers/footers
- 📚 Filters Table of Contents pages
- 🔍 Detects chapters via flexible regex
- 🔠 Handles spaced text (`C H A P T E R`)
- ✂️ Fixes hyphenation (`extra-\nordinary`)
- 🔤 Fixes drop caps (`N early → Nearly`)
- 🚫 Removes control characters (prevents TTS cutoffs)
- 🔢 Strips footnote artifacts (`word7 → word`)
- 📏 Uses **dynamic margin percentages** (not hardcoded)

---

## 🧠 Engineering Challenges & Solutions

### Spaced Text Problem

Handled stylized text using dynamic regex spacing.

---

### Header “Time-Travel” Injection

Retroactively injects chapter announcements when detected late.

---

### Noisy PDF Data

Two-stage filtering:

- Pre-scan for repeated noise
- Line-level filtering (avoids content corruption)

---

### TTS Stability Issues

Removed hidden control characters causing silent failures.

---

### Browser Timeout Problem

Solved via background threading + polling.

---

### Hugging Face Constraints (v1.1)

**Challenge:**  
Uploads failing or breaking on mobile/cloud environments.

**Solution:**

- File size validation (client-side)
- `/tmp` routing for temporary storage
- Improved error messaging for clarity

---

### UX & Feedback Improvements

- Fixed flash message visibility on mobile
- Improved error message clarity:
    - `"An unexpected error occurred during processing."`
- More user-friendly feedback loop

---

## ⚠️ Limitations (Intentional Trade-offs)

- Chapter detection is heuristic-based
    - May mislabel or delay detection
- Some PDFs have unpredictable formatting
- Optimized for **text-based, single-column PDFs**
- No OCR support (image PDFs not supported)

---

## 🧪 Testing

- Tested with large PDFs (hundreds of pages)
- Verified:

    - Correct chunk ordering
    - Stable audio generation
    - Successful merging

- Stress-tested with multiple long documents

---

## 🖥️ Local Setup

```bash
git clone https://github.com/legophil101/voxpdf.git
cd voxpdf

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt

python app.py
```

---

## 🌐 Usage

1. Open:

```
http://127.0.0.1:5000
```

2. Upload a PDF
3. Wait for processing
4. Download audiobook

---

## 🌐 Deployment

Platform: Hugging Face Spaces

- Uses `/tmp` for temporary storage
- Designed for low-concurrency usage
- Automatic cleanup prevents storage issues

---

## 🔮 Future Improvements

- Job cancellation
- OCR support (image PDFs)
- Optional chapter splitting

---

## 🎯 What This Project Demonstrates

- End-to-end system design
- Handling messy real-world data
- Async processing in web apps
- File/resource management
- Debugging edge cases
- Practical engineering trade-offs

---

## 💬 Final Notes

Built as part of a transition into software development, focusing on solving **real-world problems**, not just
tutorials.

---

## 🔥 For Recruiters / Reviewers

This is a **complete pipeline**:

**PDF → Processing → Transformation → Audiobook**

Built with real-world constraints:

- Performance
- Stability
- Imperfect data
- Accessibility

