import difflib
import re

class StringOperations:
  """Class with all the string operations"""
  config = None
  log = None
  stash = None

  def __init__(self, log, config, stash):
    self.config = config
    self.log = log
    self.stash = stash

  def find_diff_text(self, a: str, b: str):
    addi = minus = stay = ""
    minus_ = addi_ = 0
    for _, s in enumerate(difflib.ndiff(a, b)):
      if s[0] == " ":
        stay += s[-1]
        minus += "*"
        addi += "*"
      elif s[0] == "-":
        minus += s[-1]
        minus_ += 1
      elif s[0] == "+":
        addi += s[-1]
        addi_ += 1
    if minus_ > 20 or addi_ > 20:
      self.log.debug(f"Diff Checker: +{addi_}; -{minus_};")
      self.log.debug(f"OLD: {a}")
      self.log.debug(f"NEW: {b}")
    else:
      self.log.debug(
        f"Original: {a}\n- Character: {minus}\n+ Character: {addi}\n  Result: {b}"
      )
    return

  def check_long_path(self, path: str):
    # Trying to prevent error with long paths for Win10
    # https://docs.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=cmd
    if len(path) > 240:
      self.log.error(
        f"The path is too long ({len(path)} > 240). You can look at 'order_field'/'ignore_path_length' in config."
      )
      return 1
    return None

  def capitalize_words(self, s: str) -> str:
    """
    Converts a filename to title case. Capitalizes all words except for certain
    conjunctions, prepositions, and articles, unless they are the first or
    last word of a segment of the filename. Recognizes standard apostrophes, right
    single quotation marks (U+2019), and left single quotation marks (U+2018) within words.

    Ignores all caps words and abbreviations, e.g., MILF, BBW, VR, PAWGs.
    Ignores words with mixed case, e.g., LaSirena69, VRCosplayX, xHamster.
    Ignores resolutions, e.g., 1080p, 4k.

    Args:
        s (str): The string to capitalize.

    Returns:
        str: The capitalized string.

    Raises:
        ValueError: If the input is not a string.

    About the regex:
        The first \b marks the starting word boundary.
        [A-Z]? Allows for an optional initial uppercase letter.
        [a-z\'\u2019\u2018]+ matches one or more lowercase letters, apostrophes, right single quotation marks, or left single quotation marks.
            If a word contains multiple uppercase letters, it does not match.
        The final \b marks the ending word boundary, ensuring the expression matches whole words.
    """
    if not isinstance(s, str):
      raise ValueError("Input must be a string.")

    self.log.debug("capitalize_words(s): {}".format(s))

    # Function to capitalize words based on their position and value.
    def process_word(match):
      word = match.group(0)
      preceding_char, following_char = None, None

      # List of words to avoid capitalizing if found between other words.
      exceptions = {"and", "of", "the"}

      # Find the nearest non-space character before the current word
      if match.start() > 0:
        for i in range(match.start() - 1, -1, -1):
          if not match.string[i].isspace():
            preceding_char = match.string[i]
            break

      # Find the nearest non-space character after the current word
      if match.end() < len(s):
        for i in range(match.end(), len(s)):
          if not match.string[i].isspace():
            following_char = match.string[i]
            break

      # Determine capitalization based on the position and the exception rules
      if (
        match.start() == 0
        or match.end() == len(s)
        or word.lower() not in exceptions
        or (preceding_char and not preceding_char.isalnum())
        or (following_char and not following_char.isalnum())
      ):
        return word.capitalize()
      else:
        return word.lower()
    # Apply the regex pattern and the process_word function.
    return re.sub(r"\b[A-Z]?[a-z\'\u2019\u2018]+\b", process_word, s)
