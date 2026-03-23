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

# 🎧 VoxPDF – PDF to Audiobook Generator

A robust, full-stack web application that converts PDF documents into **natural-sounding audiobooks** using an asynchronous processing pipeline.

Built to handle the *messy reality of PDFs*—including inconsistent formatting, repeating headers, spaced-out text, and structural noise—this project focuses on **stability, scalability, and real-world usability**, not just ideal cases.

---

## 📌 Overview

PDFs are designed for visual layout—not for listening.

This project transforms PDFs into a **single continuous audiobook**, while intelligently handling:

* Broken formatting
* Repeating headers/footers
* Inconsistent chapter structures
* Hidden artifacts that break TTS

Instead of aiming for perfect parsing (which is unrealistic), the system is designed for **robust, end-to-end processing that works reliably on real documents**.

---

## 🚀 Key Features

* 📄 **PDF Upload via Web Interface**
* 🧠 **Intelligent Text Extraction Engine**
* 🔊 **Text-to-Speech Pipeline (Edge-TTS)**
* ⚡ **Asynchronous Background Processing (Non-blocking)**
* 📊 **Real-Time Progress Tracking (Polling)**
* 🎧 **Single Final Audiobook Output**
* 🧹 **Automatic Temporary File Cleanup**
* 🧱 **Job-Based Isolation for Multi-User Safety**

---

## ⚙️ Tech Stack

| Layer            | Technology                               |
| ---------------- | ---------------------------------------- |
| Backend          | Python, Flask, Threading                 |
| PDF Processing   | pdfplumber, Advanced Regex               |
| TTS Engine       | Microsoft Edge Text-to-Speech (edge-tts) |
| Audio Processing | FFmpeg, pydub                            |
| Frontend         | HTML5, CSS3, Bootstrap, Vanilla JS       |
| File Handling    | Job-based isolation, `/tmp` routing      |

---

## 🧠 System Architecture

Designed to handle long-running workloads **without freezing the UI or crashing the server**.

---

### 1. Job-Based Isolation

Each upload:

* Gets a unique **job ID**
* Runs in its own workspace
* Prevents file conflicts between users

---

### 2. Asynchronous Background Processing

* Flask immediately returns a response
* Heavy processing runs in a **background thread**
* User is redirected to a progress page

---

### 3. Chunk-Based Processing

* Extracted text is split into chunks
* Each chunk is converted into audio

**Why this matters:**

* Prevents large-input failures
* Improves TTS reliability
* Enables scalable processing

---

### 4. Real-Time Progress Tracking

* Frontend polls `/status/<job_id>`
* UI updates dynamically while processing continues

---

### 5. Audio Merge & Cleanup

* All chunks are merged into one audiobook using FFmpeg
* Temporary files are deleted automatically
* Only the final output is retained

---

## 🧹 PDF Processing Engine (Core Highlight)

This is the most complex and important part of the project.

### Capabilities

* 🔁 Detects and removes repeating headers/footers
* 📚 Filters out Table of Contents pages
* 🔍 Detects chapters using flexible regex
* 🔠 Handles spaced text (`C H A P T E R`)
* ✂️ Fixes hyphenation (`extra-\nordinary → extraordinary`)
* 🔤 Fixes drop caps (`N early → Nearly`)
* 🚫 Removes hidden control characters (prevents TTS cutoffs)
* 🔢 Strips footnote artifacts (`word7 → word`)

---

## 🧠 Engineering Challenges & Solutions

### 1. The “Spaced Text” Problem

**Challenge:**
PDFs often use stylized headers like `C H A P T E R  O N E`.

**Solution:**
Built a dynamic regex generator that tolerates flexible spacing while preserving structure.

---

### 2. Header “Time-Travel” Injection

**Challenge:**
Chapter titles sometimes appear in headers of the *next page*, not where the chapter starts.

**Solution:**
Implemented a buffer system that **retroactively injects chapter announcements** into the correct page.

---

### 3. Noisy PDF Data

**Challenge:**
Headers, page numbers, and repeated titles pollute the text.

**Solution:**
Two-stage filtering:

* Pre-scan to detect repeating noise
* Line-level filtering to avoid corrupting real content

---

### 4. TTS Stability Issues

**Challenge:**
Hidden control characters caused silent audio cutoffs.

**Solution:**
Sanitization layer removes non-printable characters before TTS processing.

---

### 5. Browser Timeout Problem

**Challenge:**
Long-running requests break web apps.

**Solution:**
Background threading + client-side polling.

---

### 6. Resource & Stability Guards

**Challenge:**
Large files can crash servers or break audio merging.

**Solution:**

* File size limits (Flask layer)
* Page limits (engine layer)
* Controlled chunking strategy

---

## ⚠️ Limitations (Honest & Intentional)

This project prioritizes **practical robustness over perfect accuracy**.

* Chapter detection is heuristic-based:

  * May mislabel or delay detection
* Some PDFs have unpredictable formatting
* Optimized for **text-based, single-column PDFs**
* Does not support scanned/image PDFs (no OCR yet)

These trade-offs were intentional to avoid over-engineering and maintain performance.

---

## 🧪 Testing

* Tested on large PDFs (hundreds of pages)
* Verified:

  * Correct chunk ordering
  * Stable audio generation
  * Successful merging
* Stress-tested with multiple long documents

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

1. Open browser at:

   ```
   http://127.0.0.1:5000
   ```
2. Upload a PDF
3. Wait on the progress page
4. Download the generated audiobook

---

## 🌐 Deployment

Target platform:

* Hugging Face Spaces

Key considerations:

* Use `/tmp` for temporary storage
* Designed for lightweight, low-concurrency usage
* Automatic cleanup prevents storage issues

---

## 🔮 Future Improvements

* Job cancellation (stop processing mid-task)
* Improved chapter detection accuracy
* OCR support for scanned PDFs
* Voice customization
* Progress percentage tracking
* Optional chapter-based audio splitting

---

## 🎯 What This Project Demonstrates

* End-to-end system design
* Handling real-world messy data
* Asynchronous processing in web applications
* File and resource management
* Debugging complex edge cases
* Making practical engineering trade-offs

---

## 💬 Final Notes

This project was built as part of a transition into software development, with a focus on solving real-world problems rather than following tutorials.

It reflects:

* Strong problem-solving ability
* Iterative development and debugging
* Practical system design thinking

---

## 🔥 For Recruiters / Reviewers

This is not just a script—it is a **complete pipeline**:

* Input (PDF) → Processing → Transformation → Output (Audiobook)

Built with real constraints in mind:

* Performance
* Stability
* Imperfect data
