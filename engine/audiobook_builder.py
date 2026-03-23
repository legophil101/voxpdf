import os
from pydub import AudioSegment

# 1. TELL SYSTEM WHERE FFMPEG LIVES
ffmpeg_path = r"D:\Programs\ffmpeg\bin"
os.environ["PATH"] += os.pathsep + ffmpeg_path

# 2. TELL PYDUB SPECIFICALLY
AudioSegment.converter = os.path.join(ffmpeg_path, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe.exe")


def build_audiobook(audio_files, output_path):
    """
    Combines multiple MP3 chunks into a single audio file and
    cleans up the temporary chunks to save server space.
    """
    if not audio_files:
        print("❌ No audio files provided to the builder.")
        return None

    # print("🎧 Merging audio chunks...")
    combined = AudioSegment.empty()

    # CRITICAL: Sort chunks numerically before merging!
    # Otherwise, Chunk 10 might come before Chunk 2.
    audio_files.sort()

    for file in audio_files:
        if file and os.path.exists(file):
            segment = AudioSegment.from_mp3(file)
            combined += segment

            # The 500ms pause is a great idea for pacing between chapters/sections!
            combined += AudioSegment.silent(duration=500)

    # Export directly to the exact path provided by the orchestrator
    print(f"💾 Saving final audiobook to {output_path}...")
    combined.export(output_path, format="mp3")

    # --- SERVER HYGIENE: AUTO-CLEANUP ---
    # Now that the final book is built, the individual chunks are useless.
    print("🧹 Cleaning up temporary chunk files...")
    for file in audio_files:
        if os.path.exists(file):
            os.remove(file)

    return output_path
