import os
import asyncio
import uuid

# --- 1. FORCE THE PATH BEFORE IMPORTING PYDUB ---
if os.name == 'nt':
    ffmpeg_path = r"D:\Programs\ffmpeg\bin"
    if ffmpeg_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_path

# --- 2. NOW IMPORT PYDUB AND CONFIGURE ---
from pydub import AudioSegment

if os.name == 'nt':
    AudioSegment.converter = os.path.join(ffmpeg_path, "ffmpeg.exe")
    AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe.exe")
else:
    # Hugging Face / Linux
    AudioSegment.converter = "ffmpeg"
    AudioSegment.ffprobe = "ffprobe"

# --- 3. IMPORT ENGINE COMPONENTS ---
from engine.pdf_reader import extract_text_from_pdf
from engine.text_processor import clean_text
from engine.text_chunker import split_text
from engine.tts_service import process_chunks_parallel
from engine.audiobook_builder import build_audiobook


async def main(input_pdf_path=None, base_output_dir=None):
    r"""
        Main execution logic.
        Accepts paths explicitly so it can be safely run by a multithreaded web server.
        """
    # 1. Handle defaults for standalone CLI usage vs Web App usage
    if input_pdf_path is None:
        input_pdf_path = os.path.join("uploads", "input.pdf")
    if base_output_dir is None:
        base_output_dir = "outputs"

    # 2. Create a unique ID and establish the output directory for this run
    job_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(base_output_dir, job_id)
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_pdf_path):
        print(f"Error: {input_pdf_path} not found.")
        return

    print("📖 Reading PDF...")
    # Your extract_text_from_pdf now handles the scanning and normalization
    text = extract_text_from_pdf(input_pdf_path)

    if not text:
        print("No text found in PDF.")
        return

    # Debug print to see what was extracted before cleaning
    # print(f"Original: {text[:100000]}")

    print("🧹 Cleaning text...")
    text = clean_text(text, debug=False)

    # Debug print after cleaning
    # print(f"After control cleanup: {text[:100000]}")

    print("✂️ Splitting text into chunks...")
    chunks = split_text(text)

    # Loop and await the async synthesize_speech function
    print(f"🚀 Starting parallel processing for {len(chunks)} chunks...")

    # You need to pass the output_dir so chunks save in the right folder
    audio_files = await process_chunks_parallel(chunks, output_dir)

    print("🏗️ Building final audiobook...")

    # 1. Construct the ACTUAL full path for the final file
    final_output_path = os.path.join(output_dir, f"audiobook_{job_id}.mp3")

    # 2. Pass that full path to the builder
    final_audio = build_audiobook(audio_files, final_output_path)

    print(f"✅ Audiobook created at: {final_audio}")

    # NEW: Return the ID so Flask knows exactly what folder to look for
    return job_id


if __name__ == "__main__":
    asyncio.run(main())
