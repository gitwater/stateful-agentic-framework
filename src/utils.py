import re
import unicodedata

def normalize_folder_name(folder):
    """
    Normalize a string to be safe for use as a folder name.

    This function:
      - Normalizes Unicode characters to NFKC form.
      - Removes control characters.
      - Removes characters invalid in Windows folder names (e.g. <>:"/\\|?*).
      - Strips trailing spaces and dots (which can cause issues on Windows).

    Args:
        folder (str): The original folder name string.

    Returns:
        str: A normalized folder name.
    """
    # Normalize Unicode characters to NFKC form
    folder = unicodedata.normalize('NFKC', folder)

    # Remove any control characters (ASCII 0-31)
    folder = re.sub(r'[\x00-\x1f]', '', folder)

    # Remove invalid characters: <>:"/\\|?*
    folder = re.sub(r'[<>:"/\\|?*]', '', folder)

    # Strip trailing dots and spaces (avoid issues on Windows)
    folder = folder.rstrip('. ')

    # Optionally, if you want to replace inner spaces with underscores:
    # folder = folder.replace(' ', '_')

    return folder
