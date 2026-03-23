import pdfplumber
import re

# --- CONFIGURATION (Extensible & Maintainable) ---

# We split these so "Chapter" REQUIRES a number, but "Prologue" doesn't.
# This fixes the "Ghost Header" bug where a standalone word "CHAPTER" at the top of a page
# would trigger a false positive.
NUMBERED_KEYWORDS = ["chapter", "episode", "section", "step"]
UNNUMBERED_KEYWORDS = [
    "prologue", "epilogue", "introduction", "preface",
    "foreword", "suggested reading", "acknowledgments", "appendix",
    "conclusion", "afterword", "notes", "references", "bibliography"
]

# Support for various textual representations of numbers
WORD_NUMBERS = [
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen", "twenty", "twenty-one", "twenty-two", "twenty-three",
    "twenty-four", "twenty-five", "thirty", "forty", "fifty"
]

ROMAN_NUMERALS = [
    "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x",
    "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx"
]

# --- TRANSLATION DICTIONARIES ---
# This maps "fourteen" -> 14, "fifteen" -> 15, etc.
WORD_TO_NUM = {word: i + 1 for i, word in enumerate(WORD_NUMBERS)}
ROMAN_TO_NUM = {roman: i + 1 for i, roman in enumerate(ROMAN_NUMERALS)}
COMBINED_NUM_DICT = {**WORD_TO_NUM, **ROMAN_TO_NUM}


def generate_spaced_regex(numbered, unnumbered):
    """
    Creates a robust regex that accounts for stylized formatting (like 'C H A P T E R').

    Returns:
        A compiled regex pattern that separates numbered sections from unnumbered ones.
    """

    def space_out(word_list):
        patterns = []
        for phrase in word_list:
            words = phrase.split()
            # Allow for optional spaces between letters to catch 'S P A C E D' text
            spaced_words = [r'\s*'.join(list(word)) for word in words]
            patterns.append(r'\s+'.join(spaced_words))
        return "|".join(patterns)

    numbered_joined = space_out(numbered)
    unnumbered_joined = space_out(unnumbered)

    # Capture digits, word-form numbers, or Roman numerals
    number_matches = r"[0-9]+(?:\.[0-9]+)?" + "|" + "|".join(WORD_NUMBERS) + "|" + "|".join(ROMAN_NUMERALS)

    # Combined Regex Logic: (Numbered Group + Mandatory Value) OR (Standalone Unnumbered Group)
    return rf'(?i)^\s*(?:(?:{numbered_joined})\s+({number_matches})|({unnumbered_joined}))\b'


# Pre-compile the pattern for performance
DYNAMIC_CHAPTER_PATTERN = generate_spaced_regex(NUMBERED_KEYWORDS, UNNUMBERED_KEYWORDS)


def extract_text_from_pdf(pdf_path):
    """
    Main extraction pipeline. Uses a 2-pass approach:
    1. Pre-scan: Identify and blacklist recurring headers/footers (noise).
    2. Extraction: Identify chapters using coordinates and regex while cleaning body text.
    """
    full_text = ""
    last_chapter_detected = ""
    last_chapter_num = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:

            # --- ADD THIS TIER 2 GUARD HERE ---
            total_pages = len(pdf.pages)
            if total_pages > 850:
                raise ValueError(
                    f"Document has {total_pages} pages. The limit is 850 pages to ensure stable audio conversion.")

            # --- STAGE 1: DEEP UNIVERSAL PRE-SCAN ---
            # Identifies repeating text (running headers/titles) to prevent them from
            # polluting the audiobook narration.
            print("🔍 Scanning for repeating noise...")
            noise_frequency = {}
            scan_limit = min(20, len(pdf.pages))

            for i in range(scan_limit):
                page = pdf.pages[i]
                # Look specifically at the very top of the page
                header_zone = page.within_bbox((0, 0, page.width, 250))
                text = header_zone.extract_text()
                if text:
                    for line in text.split('\n')[:5]:
                        line = line.strip()
                        if 5 < len(line) < 50:
                            noise_frequency[line] = noise_frequency.get(line, 0) + 1

            # If a line appears in more than 25% of the scanned pages, it's considered noise.
            dynamic_blacklist = [txt.lower() for txt, count in noise_frequency.items() if count > (scan_limit * 0.25)]
            print(f"🚫 Automatically ignoring: {dynamic_blacklist}")

            # --- STAGE 2: PAGE-BY-PAGE PROCESSING ---
            print(f"📄 Processing {len(pdf.pages)} pages...")

            current_chapter_announcement = ""
            page_buffers = []  # 🔥 Buffer initialized for time-travel injection

            for page in pdf.pages:
                match = None
                is_late_detection = False  # 🔥 Reset for every page

                # --- LAYER 1: TOC DENSITY FILTER ---
                # Quick scan of the whole page text to count chapter-like matches
                page_text_temp = page.extract_text() or ""
                toc_matches = re.findall(DYNAMIC_CHAPTER_PATTERN, page_text_temp)
                is_toc_page = len(toc_matches) > 3

                # Skip front matter AND Table of Contents pages
                if page.page_number >= 1 and not is_toc_page:

                    # 2a. HEADER INSPECTION
                    # Look for chapter titles in the designated header area.
                    top_margin = (0, 0, page.width, 250)
                    header_area = page.within_bbox(top_margin)
                    header_text = header_area.extract_text(x_tolerance=5)

                    if header_text:
                        # Ensure header is not just a repeating book title from the blacklist
                        if not any(noise in header_text.lower() for noise in dynamic_blacklist):
                            match = re.search(DYNAMIC_CHAPTER_PATTERN, header_text)
                            if match:
                                is_late_detection = True  # 🔥 Found in header, means we missed it on the previous page

                    # 2b. DEEP SEARCH FALLBACK
                    # If no header match, check the first few lines of the body.
                    if not match:
                        body_top_area = page.within_bbox((0, 0, page.width, 200))
                        body_top_text = body_top_area.extract_text()

                        if body_top_text:
                            top_lines = body_top_text.split('\n')[:3]
                            for line in top_lines:
                                clean_line = line.strip()
                                # if not clean_line or any(noise in clean_line.lower() for noise in dynamic_blacklist):
                                if not clean_line or clean_line.lower() in dynamic_blacklist:
                                    continue

                                # Specialized fallback for simple "Chapter X" or numeric-only headers
                                fallback_pattern = rf'(?i)^\s*(Chapter|Episode|Step|Section)\s*(\d+|{"|".join(WORD_NUMBERS)}|{"|".join(ROMAN_NUMERALS)})|^\d+[\s.]*$'
                                match = re.search(fallback_pattern, clean_line)
                                if match:
                                    is_late_detection = False  # 🔥 Found in body, so it belongs on THIS page
                                    break

                    # 2c. CHAPTER METADATA EXTRACTION & VALIDATION
                    if match:
                        raw_match = match.group(0).strip()
                        # Clean inner spaces out of spaced text for processing (e.g. 'O N E' -> 'ONE')
                        clean_match_val = re.sub(r'\s+', '', raw_match).lower()
                        found_num = None

                        # Identify the numerical value of the chapter
                        digits = re.findall(r'\d+', clean_match_val)
                        if digits:
                            found_num = int(digits[0])
                        else:
                            # Convert 'One' or 'I' to 1 for sequence validation
                            for word, val in COMBINED_NUM_DICT.items():
                                if word.replace("-", "") in clean_match_val:
                                    found_num = val
                                    break

                        # --- SEQUENCE GUARD ---
                        # Logic: Prevent random numbers (page numbers, years) from triggering 'New Chapter'
                        if found_num is not None:

                            # LAYER 2: Early-Page Skepticism (Protects Episode 08)
                            if page.page_number <= 3 and found_num > 3:
                                match = None

                            # LAYER 3: Flexible Sequence (Replaces the "Must be 1" rule)
                            elif last_chapter_num == 0:
                                last_chapter_num = found_num

                            elif found_num == last_chapter_num + 1:
                                last_chapter_num = found_num

                            # else:
                            #     match = None

                        # --- TITLE NORMALIZATION ---
                        if match:
                            # Clean up spaced-out letters and enforce Title Case
                            clean_title = re.sub(r'(?<=[a-zA-Z])\s(?=[a-zA-Z]\b)', '', raw_match)
                            normalized_title = clean_title.title()

                            # Re-inject spaces for words that the title-caser might have squashed
                            for word in WORD_NUMBERS + ["Introduction", "Preface", "Foreword", "Suggested Reading"]:
                                pattern = re.compile(rf"{word}", re.IGNORECASE)
                                normalized_title = pattern.sub(f" {word}", normalized_title)

                            normalized_title = re.sub(r'(?i)chapter\s*', 'Chapter ', normalized_title)
                            normalized_title = re.sub(r'\s+', ' ', normalized_title).strip()

                            # Avoid duplicate announcements for the same chapter
                            comparison_key = re.sub(r'\s+', '', normalized_title).lower()
                            if comparison_key != last_chapter_detected:
                                pause_for_effect = ". . . . ."  # Verbal cues for TTS
                                current_chapter_announcement = f"{normalized_title}. {pause_for_effect}\n\n"
                                last_chapter_detected = comparison_key
                                print(f"📖 New Chapter Found: {normalized_title}")

                # =================================================================
                # 3. BODY EXTRACTION & CLEANING
                # =================================================================
                safe_bbox = (0, 60, page.width, page.height - 60)
                main_body = page.within_bbox(safe_bbox)
                main_text = main_body.extract_text(y_tolerance=5)

                if main_text:
                    # Clean the body text to prevent double-reading headers
                    lines = main_text.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        clean_line_lower = line.strip().lower()
                        # 🔥 FIX: Drop standalone noise lines (headers/footers) from the body!
                        if clean_line_lower in dynamic_blacklist:
                            continue

                        # 🔥 Normalization Bridge: Squeeze spaces temporarily just to see if it's a chapter header
                        line_to_check = re.sub(r'(?<=[a-zA-Z])\s(?=[a-zA-Z]\b)', '', line.strip())
                        # Because of [\s\.]* in the regex, this will correctly catch and drop lines with trailing dots
                        if not re.search(DYNAMIC_CHAPTER_PATTERN, line_to_check, re.IGNORECASE):
                            cleaned_lines.append(line)

                    cleaned_main_text = "\n".join(cleaned_lines).strip()

                    # 🔥 THE INJECTION FIX 🔥
                    if current_chapter_announcement:
                        if is_late_detection and len(page_buffers) > 0:
                            # Running header caught it late. Retroactively inject into the PREVIOUS page.
                            page_buffers[-1] = f"\n\n{current_chapter_announcement}\n\n" + page_buffers[-1]
                        else:
                            # On-time detection. Inject normally before current page.
                            cleaned_main_text = f"\n\n{current_chapter_announcement}\n\n" + cleaned_main_text

                        current_chapter_announcement = ""  # Clear it

                    page_buffers.append(cleaned_main_text)

            # Combine all buffered pages at the end
            full_text = "\n\n".join(page_buffers)

    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return ""

    return full_text.strip()
