# 1. Use a lightweight Python base image
FROM python:3.10-slim

# 2. Install FFmpeg (Critical for pydub)
RUN apt-get update && apt-get install -y ffmpeg

# 3. Create a user (Hugging Face requires apps to run as a non-root user)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 4. Set the working directory
WORKDIR /app

# 5. Copy your project files into the container
COPY --chown=user . /app

# 6. Install your Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# 7. Expose the port Hugging Face uses
EXPOSE 7860

# 8. Start the Flask server on port 7860
CMD ["flask", "run", "--host=0.0.0.0", "--port=7860"]