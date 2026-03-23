def split_text(text, max_length=4500):
    """
    Splits text into chunks, ensuring we don't break sentences mid-way.
    """
    chunks = []

    while len(text) > 0:
        # If the remaining text is already short enough, just add it
        if len(text) <= max_length:
            chunks.append(text.strip())
            break

        # Look at the slice from 0 to max_length
        chunk_slice = text[:max_length]

        # Find the last punctuation mark to end the chunk naturally
        # We look for . ! or ?
        last_punctuation = max(
            chunk_slice.rfind("."),
            chunk_slice.rfind("!"),
            chunk_slice.rfind("?")
        )

        # If we found punctuation, we split there (+1 to include the mark)
        if last_punctuation != -1:
            end_index = last_punctuation + 1
        else:
            # If no punctuation (rare), find the last space so we don't break a word
            last_space = chunk_slice.rfind(" ")
            end_index = last_space if last_space != -1 else max_length

        # Extract the chunk and update the remaining text
        chunks.append(text[:end_index].strip())
        text = text[end_index:].strip()

    return chunks
