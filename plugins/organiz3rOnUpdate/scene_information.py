import os
import re


class SceneInformation:
    """A simple example class"""

    scene = None
    log = None

    path = None
    audio_codec = None
    bit_rate = None
    checksum = None
    date_format = None
    directory = None
    directory_split = None
    extension = None
    filename = None
    id = None
    movie_index = None
    movie_scene = None
    movie_title = None
    movie_year = None
    oshash = None
    parent_studio = None
    performer = None
    performer_path = None
    rating = None
    stashid_performer = None
    studio = None
    studio_code = None
    studio_family = None
    studio_hierarchy = None
    tags = None
    template_split = None
    title = None
    video_codec = None
    year = None

    def __init__(self, log, scene: dict):
        self.log = log
        self.scene = scene or {}

        file_info = self.scene.get("file") or {}
        files_list = self.scene.get("files") or []

        # Basic path-derived properties
        self.path = str(self.scene.get("path")) if self.scene.get("path") is not None else None
        self.directory = os.path.dirname(self.path) if self.path else None
        self.directory_split = os.path.normpath(self.path).split(os.sep) if self.path else None
        self.extension = os.path.splitext(self.path)[1] if self.path else None
        self.filename = os.path.basename(self.path) if self.path else None

        # File codecs and bit rate
        self.audio_codec = (file_info.get("audio_codec") or "").upper() if file_info.get("audio_codec") else None
        self.video_codec = (file_info.get("video_codec") or "").upper() if file_info.get("video_codec") else None
        self.bit_rate = (
            str(round(int(file_info.get("bit_rate")) / 1000000, 2))
            if file_info.get("bit_rate") not in (None, "")
            else None
        )

        # Hashes and checksums
        self.checksum = self.scene.get("checksum")
        self.oshash = self.scene.get("oshash")

        # IDs
        self.id = (self.scene.get("stash_ids") or [{}])[0].get("stash_id") if self.scene.get("stash_ids") else None
        self.studio_code = self.scene.get("code")

        # Title
        raw_title = self.scene.get("title")
        if not raw_title and self.filename:
            raw_title = os.path.splitext(self.filename)[0]
        # Strip the extension from title if present and matches the file extension
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
            self.movie_year = movie.get("date", None)[:4] if movie.get("date") else None
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

        self.log.debug("Extracting information from scene: {}".format(self.scene))
