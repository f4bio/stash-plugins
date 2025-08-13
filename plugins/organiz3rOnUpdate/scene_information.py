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
    date_format = None
    year = None

    # Rating
    rating = None

    # Studio information
    studio = None
    parent_studio = None
    studio_family = None
    studio_hierarchy = None

    # Movie info
    movie_title = None
    movie_year = None
    movie_index = None
    movie_scene = None

    # Performers
    performer = None
    performer_path = None
    stashid_performer = None

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
        date_str = self.scene.get("date")
        self.date_format = None
        self.year = date_str[:4] if isinstance(date_str, str) and len(date_str) >= 4 else None

        # Rating (raw rating100 if available)
        self.rating = self.scene.get("rating100")

        # Studio information
        studio_obj = self.scene.get("studio") or {}
        self.studio = studio_obj.get("name")
        self.parent_studio = (studio_obj.get("parent_studio") or {}).get("name") if studio_obj.get(
            "parent_studio") else None
        self.studio_family = self.parent_studio or self.studio
        # Minimal hierarchy (best-effort without external lookups)
        if self.studio or self.parent_studio:
            hierarchy = []
            if self.parent_studio:
                hierarchy.append(self.parent_studio)
            if self.studio:
                hierarchy.append(self.studio)
            self.studio_hierarchy = hierarchy
        else:
            self.studio_hierarchy = None

        # Movie info
        self.movie_title = None
        self.movie_year = None
        self.movie_index = None
        self.movie_scene = None
        movies = self.scene.get("movies") or []
        if movies:
            movie = movies[0].get("movie") or {}
            self.movie_title = movie.get("name")
            self.movie_year = movie.get("date")[:4] if movie.get("date") else None
            idx = movies[0].get("scene_index")
            self.movie_index = idx
            self.movie_scene = f"scene {idx}" if isinstance(idx, int) else None

        # Performers
        performers = self.scene.get("performers") or []
        perf_names = [p.get("name") for p in performers if p.get("name")]
        self.performer = ", ".join(perf_names) if perf_names else None
        self.performer_path = perf_names[0] if perf_names else None
        perf_stash_ids = []
        for p in performers:
            sid = (p.get("stash_ids") or [{}])[0].get("stash_id") if p.get("stash_ids") else None
            if sid is not None:
                perf_stash_ids.append(str(sid))
        self.stashid_performer = ", ".join(perf_stash_ids) if perf_stash_ids else None

        # Tags
        tags_list = self.scene.get("tags") or []
        self.tags = ", ".join([t.get("name") for t in tags_list if t.get("name")]) if tags_list else None

        # Template-related fields (not resolvable here)
        self.template_split = None
        self.date_format = None  # placeholder if external formatting applies later

        log.debug("Extracted information: {}".format(self))
