import os
import re

import stashapi.log as log


class FileInformation:
    """A class to extract information from a Stash file"""

    # Core/context
    file = None

    # Raw/basic fields
    id = None
    path = None
    basename = None
    parent_folder_id = None
    zip_file_id = None
    mod_time = None
    size = None
    format = None
    width = None
    height = None
    duration = None
    frame_rate = None
    created_at = None
    updated_at = None

    # Derived filesystem fields
    directory = None
    directory_split = None
    extension = None
    filename = None

    # Fingerprints
    oshash = None
    phash = None

    # Codecs and bit rate
    audio_codec = None
    video_codec = None
    bit_rate = None

    # Optional fields to mirror the example structure
    studio_code = None
    title = None
    date = None
    rating = None
    studio = None
    performers = None
    tags = None

    def __init__(self, file: dict):
        self.file = file or {}

        # Raw/basic fields
        self.id = str(self.file.get("id")) if self.file.get("id") is not None else None
        self.path = self.file.get("path")
        self.basename = self.file.get("basename") or (os.path.basename(self.path) if self.path else None)
        self.parent_folder_id = self.file.get("parent_folder_id")
        self.zip_file_id = self.file.get("zip_file_id")
        self.mod_time = self.file.get("mod_time")
        self.size = self.file.get("size")
        self.format = self.file.get("format")
        self.width = self.file.get("width")
        self.height = self.file.get("height")
        self.duration = self.file.get("duration")
        self.frame_rate = self.file.get("frame_rate")
        self.created_at = self.file.get("created_at")
        self.updated_at = self.file.get("updated_at")

        # Derived filesystem fields
        self.directory = self.path  # keep parity with the provided example structure
        self.directory_split = os.path.normpath(self.path).split(os.sep) if self.path else []
        self.extension = os.path.splitext(self.path)[1] if self.path else None
        self.filename = self.basename  # filename defaults to the basename

        # Fingerprints
        self.oshash = None
        self.phash = None
        for fp in self.file.get("fingerprints", []) or []:
            fp_type = fp.get("type")
            if fp_type == "oshash":
                self.oshash = fp.get("value")
            elif fp_type == "phash":
                self.phash = fp.get("value")

        # Codecs: normalized to upper-case
        self.audio_codec = (self.file.get("audio_codec") or "").upper() or None
        self.video_codec = (self.file.get("video_codec") or "").upper() or None

        # Bit rate: convert to Mbps string rounded to 2 decimals (e.g., "4.49")
        self.bit_rate = None
        try:
            if self.file.get("bit_rate") is not None:
                self.bit_rate = str(round(int(self.file["bit_rate"]) / 1_000_000, 2))
        except (ValueError, TypeError):
            # Leave as None if input is not numeric
            self.bit_rate = None

        # Optional fields to mirror the example structure (filled with sensible defaults)
        self.studio_code = ""
        self.title = None
        self.date = None
        self.rating = None
        self.studio = {"id": None}
        self.performers = []
        self.tags = []

    def __str__(self):
        return str(self.__dict__)


class SceneInformation:
    """A class to extract information from a Stash scene"""

    # Core/context
    log = None

    # Basic path-derived properties
    files = None
    directory = None
    directory_split = None
    extension = None
    filename = None

    # File codecs and bit rate
    audio_codec = None
    video_codec = None
    bit_rate = None

    # Hashes and checksums
    oshash = None
    phash = None
    checksum = None

    # IDs
    id = None
    studio_code = None

    # Title
    title = None

    # Date and year
    date = None

    # Rating
    rating = None

    # Studio information
    studio = None

    # Performers
    performers = None

    # Tags
    tags = None

    # Template-related fields
    template_split = None

    def __init__(self, scene: dict):
        # Basic path-derived properties
        # TODO: how to handle multiple files?
        self.files = [FileInformation(f) for f in (scene.get("files") or [])]
        self.directory = self.files[0].path
        self.directory_split = self.directory.split(os.sep)
        self.extension = self.files[0].extension

        # File codecs and bit rate
        self.audio_codec = self.files[0].audio_codec
        self.video_codec = self.files[0].video_codec
        self.bit_rate = self.files[0].bit_rate

        # Hashes and checksums
        self.oshash = self.files[0].oshash
        self.phash = self.files[0].phash

        # IDs
        self.id = scene.get("id")
        self.studio_code = scene.get("code")

        # Title
        raw_title = scene.get("title")
        if not raw_title and self.filename:
            raw_title = os.path.splitext(self.filename)[0]
        # Strip the extension from the title if present and matches the file extension
        if raw_title and self.extension:
            try:
                raw_title = re.sub(rf"{re.escape(self.extension)}$", "", raw_title)
            except re.error:
                pass
        self.title = raw_title
        self.filename = "{}{}".format(self.title, self.extension)

        # Date and year (date_format left for external formatting logic when available)
        self.date = scene.get("date")

        # Rating (raw rating100 if available)
        self.rating = scene.get("rating100")

        # Studio information
        self.studio = scene.get("studio")

        # Performers
        self.performers = scene.get("performers")

        # Tags
        self.tags = scene.get("tags")

        log.debug("Extracted '{}' pieces of information".format(len(self.__dict__)))

    def __str__(self):
        return str(self.__dict__)
