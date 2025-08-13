import os
import re
import stashapi.log as log

class SceneInformation:
    """A simple example class"""

    # Core/context
    scene = None
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
        self.scene = scene or {}

        # Basic path-derived properties
        # TODO: how to handle multiple files?
        self.files = self.scene.get("files")
        self.directory = self.files[0].get("path")
        self.directory_split = self.directory.split(os.sep)
        self.extension = os.path.splitext(self.files[0].get("basename"))[1]
        self.filename = self.files[0].get("basename")

        # File codecs and bit rate
        self.audio_codec = (self.files[0].get("audio_codec") or "").upper()
        self.video_codec = (self.files[0].get("video_codec") or "").upper()
        self.bit_rate = (
            str(round(int(self.files[0].get("bit_rate")) / 1000000, 2))
            if self.files[0].get("bit_rate") not in (None, "")
            else None
        )

        # Hashes and checksums
        self.oshash = self.files[0].get("fingerprints")[0].get("value")
        self.phash = self.files[0].get("fingerprints")[1].get("value")

        # IDs
        self.id = self.scene.get("id")
        self.studio_code = self.scene.get("code")

        # Title
        raw_title = self.scene.get("title")
        if not raw_title and self.filename:
            raw_title = os.path.splitext(self.filename)[0]
        # Strip the extension from the title if present and matches the file extension
        if raw_title and self.extension:
            try:
                raw_title = re.sub(rf"{re.escape(self.extension)}$", "", raw_title)
            except re.error:
                pass
        self.title = raw_title

        # Date and year (date_format left for external formatting logic when available)
        self.date = self.scene.get("date")

        # Rating (raw rating100 if available)
        self.rating = self.scene.get("rating100")

        # Studio information
        self.studio = self.scene.get("studio")

        # Performers
        self.performers = self.scene.get("performers")

        # Tags
        self.tags = self.scene.get("tags")

        log.debug("Extracted information: {}".format(self))
