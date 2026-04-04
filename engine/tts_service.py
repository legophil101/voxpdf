import edge_tts
import asyncio
import os

# --- CONFIGURATION & CONSTANTS ---
# Standardizing these at the top makes the code maintainable (cleaner for portfolio reviews).
MAX_CONCURRENT_WORKERS = 8  # Limits how many chunks we process at once to avoid CPU/API spikes.
MAX_RETRIES = 3  # Number of times to attempt a chunk before giving up.


async def synthesize_speech(text_chunk, index, semaphore, output_path, voice):
    """
    Handles the TTS conversion for a single text chunk with error handling and retries.
    It now relies entirely on the 'output_path' passed to it by the orchestrator.

    Args:
        text_chunk (str): The cleaned text to be spoken.
        index (int): The sequence number (used for file naming/ordering).
        semaphore (asyncio.Semaphore): The 'gatekeeper' object that limits concurrent tasks.
    """

    # 'async with semaphore' ensures only MAX_CONCURRENT_WORKERS are active at any given time.
    # If 8 are already running, the 9th task waits here until one finishes.
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                # Initialize the Edge TTS Communication object.
                # 'rate="-5%"' slightly slows down the speech for better clarity.
                communicate = edge_tts.Communicate(
                    text_chunk,
                    voice,
                    rate="-5%"
                )

                # 'asyncio.wait_for' wraps the save operation with a 120s timeout.
                # This prevents a 'hanging' network request from blocking the entire pipeline.
                await asyncio.wait_for(
                    communicate.save(output_path),
                    timeout=120
                )

                # Success: Return the path to signal completion.
                print(f"✅ Chunk {index:03} saved to {output_path}")
                return output_path

            except asyncio.TimeoutError:
                print(f"⏱️ Chunk {index} timed out (attempt {attempt + 1}/{MAX_RETRIES})")
            except Exception as e:
                # Capture specific error messages to help with debugging cloud deployments.
                print(f"⚠️ Chunk {index} failed: {e} (attempt {attempt + 1}/{MAX_RETRIES})")

            # --- RETRY LOGIC (Exponential Backoff) ---
            if attempt < MAX_RETRIES - 1:
                # We calculate a backoff time: 2, 4, 8 seconds...
                # This 'polite' retry strategy prevents the server from being blacklisted by the API.
                backoff_time = 2 ** (attempt + 1)
                print(f"🔄 Retrying chunk {index} in {backoff_time} seconds...")

                # 'await asyncio.sleep' is non-blocking.
                # Other chunks will continue processing while this specific task 'naps'.
                await asyncio.sleep(backoff_time)
            else:
                # If all retries fail, we log it and raise the error to the parent function.
                print(f"❌ Chunk {index} permanently failed after {MAX_RETRIES} attempts.")
                raise


async def process_chunks_parallel(chunks, output_dir, voice="en-US-AvaNeural", update_progress=None):
    """
        The Orchestrator: Splits chunks, runs them, and tracks real-time progress.
        Now properly passes the isolated Job Directory to each worker.
        """
    print(f"The voice selected in tts_service.py is {voice}")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_WORKERS)

    total_chunks = len(chunks)
    completed_chunks = [0]  # Using a list allows mutability inside the async worker

    async def worker(chunk_text, idx, path):
        # 1. Generate the audio
        res = await synthesize_speech(chunk_text, idx, semaphore, path, voice)
        # 2. Increment completed count
        completed_chunks[0] += 1
        # 3. Fire the callback to Flask!
        if update_progress:
            update_progress(completed_chunks[0], total_chunks)
        return res

    tasks = []
    for index, chunk in enumerate(chunks):
        # 1. Construct the specific path inside the dynamic Job Directory
        chunk_path = os.path.join(output_dir, f"chunk_{index:03}.mp3")

        # 2. Pass all 5 required arguments to the worker
        tasks.append(worker(chunk, index, chunk_path))
    # asyncio.gather ensures the audio files stay in the exact correct order
    results = await asyncio.gather(*tasks)

    return results
