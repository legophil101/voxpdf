import base64


def save_audio_file(base64_audio, index):
    audio_data = base64.b64decode(base64_audio)

    filename = f"outputs/chunk_{index}.mp3"

    with open(filename, "wb") as f:
        f.write(audio_data)

    return filename
