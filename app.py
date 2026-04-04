import os
import traceback

# --- STEP 1: FORCE THE PATH BEFORE ANYTHING ELSE ---
if os.name == 'nt':
    ffmpeg_path = r"D:\Programs\ffmpeg\bin"
    if ffmpeg_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_path

# --- STEP 2: NOW IMPORT EVERYTHING ELSE ---
import asyncio
import threading
import uuid
import shutil
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, jsonify
from dotenv import load_dotenv
from pydub import AudioSegment

# --- STEP 3: CONFIGURE PYDUB ---
if os.name == 'nt':
    AudioSegment.converter = os.path.join(ffmpeg_path, "ffmpeg.exe")
    AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe.exe")
else:
    AudioSegment.converter = "ffmpeg"
    AudioSegment.ffprobe = "ffprobe"

# Now import your CLI logic
from cli import main

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# --- ADD THIS TIER 1 GUARD HERE ---
# 6 Megabytes = 6 * 1024 * 1024 bytes. Flask will auto-reject anything larger.
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024

# --- DIRECTORY SETUP ---
# If we are on a Linux server (like Hugging Face), use /tmp.
# If on Windows (local dev), use the current project folder.
if os.name == 'nt':
    BASE_DIR = os.getcwd()
else:
    BASE_DIR = "/tmp"

# Now everything builds relative to the "safe" zone
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
JOBS_FOLDER = os.path.join(BASE_DIR, "jobs")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(JOBS_FOLDER, exist_ok=True)

# Global tracker for background tasks
active_tasks = {}


@app.route("/ping")
def ping():
    try:
        return "OK", 200
    except Exception as e:
        # Logs the error to Render so you can see why it failed
        app.logger.error(f"Health check failed: {e}")
        return "Website Offline", 500


@app.errorhandler(413)
def request_entity_too_large(error):
    # Flash the message so it appears on index.html
    flash(f"File is too large! Maximum limit is 6MB.\nPlease compress your PDF or choose a smaller one.", "warning")
    # Redirect them back to the start
    return redirect(url_for('index'))


@app.route("/", methods=["GET", "POST"])
def index():
    # If we redirected back from an error in progress.html
    error_msg = request.args.get("error")
    if error_msg:
        flash(error_msg, "warning")
    if request.method == "POST":
        file = request.files.get("pdf")
        # Grab mode from form (default to 'clean')
        selected_mode = request.form.get("extraction_mode", "clean")
        selected_voice = request.form.get("voice_choice", "en-US-AvaNeural")

        if file and file.filename.endswith('.pdf'):
            # 1. Generate a truly unique session ID
            session_id = str(uuid.uuid4())[:8]

            # 2. CREATE A SHADOW WORKING DIRECTORY
            # This is the secret sauce to avoid PermissionError
            job_work_dir = os.path.join(BASE_DIR, "jobs", session_id)
            job_upload_dir = os.path.join(job_work_dir, "uploads")
            os.makedirs(job_upload_dir, exist_ok=True)

            # Save the file exactly where cli.py expects it: uploads/input.pdf
            input_path = os.path.join(job_upload_dir, "input.pdf")
            file.save(input_path)

            active_tasks[session_id] = {"status": "processing", "final_file": None}

            # 3. Background worker (Thread-Safe Context)
            def run_cli_logic(sid, work_dir, pdf_file_path, mode, voice):
                print(f"The mode selected in app.py is {mode}")
                print(f"The voice selected in app.py is {voice}")

                # 🔥 THE BRIDGE: This updates the global dictionary in real-time
                def update_progress(completed, total):
                    active_tasks[sid]["completed_chunks"] = completed
                    active_tasks[sid]["total_chunks"] = total

                try:
                    # NEW: Pass absolute paths directly to main().
                    # No os.chdir() needed. This is completely thread-safe!
                    inner_job_id = asyncio.run(
                        main(input_pdf_path=pdf_file_path, base_output_dir=work_dir, mode=mode, voice=voice,
                             progress_callback=update_progress))

                    if not inner_job_id:
                        raise Exception("CLI failed to process the PDF.")

                    # Use the returned ID to find the exact file
                    local_outputs = os.path.join(work_dir, inner_job_id)
                    final_source = os.path.join(local_outputs, f"audiobook_{inner_job_id}.mp3")

                    # Move the final file to the GLOBAL outputs folder so we can serve it
                    global_job_dir = os.path.join(OUTPUT_FOLDER, inner_job_id)
                    os.makedirs(global_job_dir, exist_ok=True)

                    # Copy to the global outputs folder
                    shutil.copy(final_source, os.path.join(global_job_dir, f"audiobook_{inner_job_id}.mp3"))

                    # Update status for progress.html to read
                    active_tasks[sid]["job_id"] = inner_job_id
                    active_tasks[sid]["final_file"] = f"audiobook_{inner_job_id}.mp3"
                    active_tasks[sid]["status"] = "completed"

                except ValueError as ve:
                    # This catches your "850 pages" error specifically
                    active_tasks[sid]["status"] = "error"
                    active_tasks[sid]["message"] = str(ve)  # Store the "Document has X pages..." message
                except Exception as e:
                    # --- NEW DIAGNOSTIC LOGGING ---
                    print(f"❌ CRITICAL ENGINE FAILURE for session {sid}:", flush=True)
                    print(f"Error Type: {type(e).__name__}", flush=True)
                    print(f"Error Message: {str(e)}", flush=True)
                    traceback.print_exc()  # This prints the full 'Stack Trace' to HF logs

                    active_tasks[sid]["status"] = "error"
                    active_tasks[sid]["message"] = "An unexpected error occurred during processing."
                    # This is the 'Yellow' trigger for Flask
                    flash("An unexpected error occurred during processing.", "warning")

            # Start the thread, passing the input_path explicitly
            threading.Thread(target=run_cli_logic,
                             args=(session_id, job_work_dir, input_path, selected_mode, selected_voice)).start()

            return redirect(url_for("progress_page", session_id=session_id))

        flash("Invalid file. Please upload a PDF.")
        return redirect(request.url)

    # Success landing
    success_file = request.args.get("file")
    job_id = request.args.get("jid")
    return render_template("index.html", success_file=success_file, job_id=job_id)


@app.route("/progress/<session_id>")
def progress_page(session_id):
    return render_template("progress.html", session_id=session_id)


@app.route("/status/<session_id>")
def get_status(session_id):
    return jsonify(active_tasks.get(session_id, {"status": "not_found"}))


@app.route('/download/<job_id>/<filename>')
def download_file(job_id, filename):
    job_output_path = os.path.join(OUTPUT_FOLDER, job_id)
    return send_from_directory(job_output_path, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
