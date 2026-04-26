"""
Unit tests for renamerOnUpdate.py

Tests cover:
- _matches_pattern(): exact and regex matching
- is_excluded(): tag, studio, and path exclusion
- Date parsing: full, partial (YYYY-MM), and year-only (YYYY) dates

The functions under test are replicated here so that tests run without
a live Stash server or the full module import chain.
"""

import re
from datetime import datetime
import pytest


# ---------------------------------------------------------------------------
# Replicate the functions under test exactly as in renamerOnUpdate.py
# ---------------------------------------------------------------------------

def _matches_pattern(value: str, pattern_config: dict) -> bool:
    ptype = pattern_config.get("type", "exact")
    pattern = pattern_config.get("pattern", "")
    if ptype == "regex":
        return bool(re.search(pattern, value, re.IGNORECASE))
    return value.lower() == pattern.lower()


def is_excluded(stash_scene, exclude_enabled=True,
                exclude_tag_patterns=None, exclude_studio_patterns=None,
                exclude_path_patterns=None):
    if not exclude_enabled:
        return False
    exclude_tag_patterns = exclude_tag_patterns or {}
    exclude_studio_patterns = exclude_studio_patterns or {}
    exclude_path_patterns = exclude_path_patterns or {}

    if exclude_tag_patterns:
        scene_tags = [t.get("name", "") for t in stash_scene.get("tags", [])]
        for _key, pat in exclude_tag_patterns.items():
            for tag_name in scene_tags:
                if _matches_pattern(tag_name, pat):
                    return True

    if exclude_studio_patterns:
        studios_to_check = []
        if stash_scene.get("studio"):
            studios_to_check.append(stash_scene["studio"].get("name", ""))
            parent = stash_scene["studio"].get("parent_studio")
            if parent:
                studios_to_check.append(parent.get("name", ""))
        for _key, pat in exclude_studio_patterns.items():
            for studio_name in studios_to_check:
                if studio_name and _matches_pattern(studio_name, pat):
                    return True

    if exclude_path_patterns:
        current_path = stash_scene.get("path") or ""
        if not current_path and stash_scene.get("files"):
            current_path = stash_scene["files"][0].get("path", "")
        for _key, pat in exclude_path_patterns.items():
            if current_path and _matches_pattern(current_path, pat):
                return True

    return False


def _parse_date(raw: str):
    date_scene = None
    for fmt in (r"%Y-%m-%d", r"%Y-%m", r"%Y"):
        try:
            date_scene = datetime.strptime(raw, fmt)
            break
        except ValueError:
            continue
    return date_scene


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scene(tags=None, studio=None, parent_studio=None, path="/data/video.mkv"):
    scene = {
        "tags": [{"name": t} for t in (tags or [])],
        "studio": None,
        "path": path,
        "files": [{"path": path}],
    }
    if studio:
        scene["studio"] = {
            "name": studio,
            "parent_studio": {"name": parent_studio} if parent_studio else None,
        }
    return scene


# ---------------------------------------------------------------------------
# _matches_pattern
# ---------------------------------------------------------------------------

class TestMatchesPattern:
    def test_exact_match(self):
        assert _matches_pattern("Test Studio", {"type": "exact", "pattern": "Test Studio"})

    def test_exact_case_insensitive(self):
        assert _matches_pattern("test studio", {"type": "exact", "pattern": "Test Studio"})

    def test_exact_no_match(self):
        assert not _matches_pattern("Other Studio", {"type": "exact", "pattern": "Test Studio"})

    def test_exact_partial_no_match(self):
        assert not _matches_pattern("Test Studio Extra", {"type": "exact", "pattern": "Test Studio"})

    def test_regex_match(self):
        assert _matches_pattern("/data/temp/video.mkv", {"type": "regex", "pattern": r".*/temp/.*"})

    def test_regex_no_match(self):
        assert not _matches_pattern("/data/movies/video.mkv", {"type": "regex", "pattern": r".*/temp/.*"})

    def test_regex_case_insensitive(self):
        assert _matches_pattern("WIP Studio", {"type": "regex", "pattern": r"wip.*"})

    def test_regex_partial_match(self):
        assert _matches_pattern("Test Studio Extra", {"type": "regex", "pattern": r"Test Studio"})

    def test_default_type_is_exact(self):
        assert _matches_pattern("hello", {"pattern": "hello"})


# ---------------------------------------------------------------------------
# is_excluded – disabled
# ---------------------------------------------------------------------------

class TestIsExcludedDisabled:
    def test_disabled_always_false(self):
        scene = _scene(tags=["SomeTag"])
        assert not is_excluded(
            scene,
            exclude_enabled=False,
            exclude_tag_patterns={"t": {"type": "exact", "pattern": "SomeTag"}},
        )


# ---------------------------------------------------------------------------
# is_excluded – tags
# ---------------------------------------------------------------------------

class TestIsExcludedByTag:
    def test_excluded_exact_tag(self):
        assert is_excluded(_scene(tags=["WIP"]), exclude_tag_patterns={"wip": {"type": "exact", "pattern": "WIP"}})

    def test_not_excluded_tag_mismatch(self):
        assert not is_excluded(_scene(tags=["Blowjob"]), exclude_tag_patterns={"wip": {"type": "exact", "pattern": "WIP"}})

    def test_excluded_regex_tag(self):
        assert is_excluded(_scene(tags=["TempContent"]), exclude_tag_patterns={"temp": {"type": "regex", "pattern": r"temp.*"}})

    def test_no_tags_not_excluded(self):
        assert not is_excluded(_scene(tags=[]), exclude_tag_patterns={"wip": {"type": "exact", "pattern": "WIP"}})

    def test_multiple_tags_one_matches(self):
        assert is_excluded(_scene(tags=["Blowjob", "WIP"]), exclude_tag_patterns={"wip": {"type": "exact", "pattern": "WIP"}})


# ---------------------------------------------------------------------------
# is_excluded – studios
# ---------------------------------------------------------------------------

class TestIsExcludedByStudio:
    def test_excluded_exact_studio(self):
        assert is_excluded(_scene(studio="Test Studio"), exclude_studio_patterns={"ts": {"type": "exact", "pattern": "Test Studio"}})

    def test_excluded_by_parent_studio(self):
        assert is_excluded(_scene(studio="Brazzers", parent_studio="MindGeek"), exclude_studio_patterns={"mg": {"type": "exact", "pattern": "MindGeek"}})

    def test_not_excluded_studio_mismatch(self):
        assert not is_excluded(_scene(studio="Real Studio"), exclude_studio_patterns={"ts": {"type": "exact", "pattern": "Test Studio"}})

    def test_no_studio_not_excluded(self):
        assert not is_excluded(_scene(), exclude_studio_patterns={"ts": {"type": "exact", "pattern": "Test Studio"}})

    def test_excluded_regex_studio(self):
        assert is_excluded(_scene(studio="TempStudio"), exclude_studio_patterns={"tmp": {"type": "regex", "pattern": r"temp.*"}})


# ---------------------------------------------------------------------------
# is_excluded – paths
# ---------------------------------------------------------------------------

class TestIsExcludedByPath:
    def test_excluded_regex_path(self):
        assert is_excluded(_scene(path="/data/loeschen/video.mkv"), exclude_path_patterns={"del": {"type": "regex", "pattern": r".*/loeschen/.*"}})

    def test_not_excluded_path_mismatch(self):
        assert not is_excluded(_scene(path="/data/zugeord/video.mkv"), exclude_path_patterns={"del": {"type": "regex", "pattern": r".*/loeschen/.*"}})

    def test_excluded_exact_path(self):
        assert is_excluded(
            _scene(path="/data/loeschen/video.mkv"),
            exclude_path_patterns={"sp": {"type": "exact", "pattern": "/data/loeschen/video.mkv"}},
        )

    def test_path_from_files_fallback(self):
        scene = {"tags": [], "studio": None, "path": "", "files": [{"path": "/data/loeschen/video.mkv"}]}
        assert is_excluded(scene, exclude_path_patterns={"del": {"type": "regex", "pattern": r".*/loeschen/.*"}})


# ---------------------------------------------------------------------------
# is_excluded – no patterns
# ---------------------------------------------------------------------------

class TestIsExcludedNoPatterns:
    def test_no_patterns_not_excluded(self):
        assert not is_excluded(_scene(tags=["Blowjob"], studio="Any Studio", path="/data/video.mkv"))


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

class TestDateParsing:
    def test_full_date(self):
        assert _parse_date("2019-12-01") == datetime(2019, 12, 1)

    def test_year_month(self):
        assert _parse_date("2012-07") == datetime(2012, 7, 1)

    def test_year_only(self):
        assert _parse_date("2023") == datetime(2023, 1, 1)

    def test_invalid_returns_none(self):
        assert _parse_date("not-a-date") is None

    def test_empty_string_returns_none(self):
        assert _parse_date("") is None


# ---------------------------------------------------------------------------
# get_missing_required_fields
# ---------------------------------------------------------------------------

def get_missing_required_fields(template_str: str, scene_info: dict) -> list:
    """Replicated from renamerOnUpdate.py for isolated testing."""
    import re
    required_part = re.sub(r"\{[^{}]*\}", "", template_str)
    required_fields = re.findall(r"\$(\w+)", required_part)
    missing = []
    for field in required_fields:
        key = field.strip("_")
        if not scene_info.get(key):
            missing.append(f"${field}")
    return missing


class TestGetMissingRequiredFields:

    def _info(self, **kwargs):
        base = {"title": None, "date": None, "studio": None, "height": None, "performer": None}
        base.update(kwargs)
        return base

    def test_all_required_present(self):
        info = self._info(title="My Scene", date="2024-01-01", height="1080p")
        assert get_missing_required_fields("$title - $date [$height]", info) == []

    def test_title_missing(self):
        info = self._info(date="2024-01-01", height="1080p")
        missing = get_missing_required_fields("$title - $date [$height]", info)
        assert "$title" in missing

    def test_date_missing(self):
        info = self._info(title="My Scene", height="1080p")
        missing = get_missing_required_fields("$title - $date [$height]", info)
        assert "$date" in missing

    def test_optional_fields_not_checked(self):
        # $studio and $date are optional (inside {}), only $title is required
        info = self._info(title="My Scene")  # no studio, no date
        template = "{[$studio] }{$date - }$title"
        missing = get_missing_required_fields(template, info)
        assert missing == []

    def test_optional_field_missing_ignored(self):
        info = self._info(title="My Scene")
        template = "{$studio - }$title"
        assert get_missing_required_fields(template, info) == []

    def test_multiple_missing(self):
        info = self._info()  # all None
        missing = get_missing_required_fields("$title - $date [$height]", info)
        assert "$title" in missing
        assert "$date" in missing
        assert "$height" in missing

    def test_empty_template(self):
        info = self._info(title="My Scene")
        assert get_missing_required_fields("", info) == []

    def test_all_optional(self):
        # entire template is optional
        info = self._info()
        template = "{[$studio] }{$date - }{$title}"
        assert get_missing_required_fields(template, info) == []

    def test_path_template(self):
        info = {"studio": "BangBros", "year": "2024"}
        template = "/data/zugeord/$studio/$year"
        assert get_missing_required_fields(template, info) == []

    def test_path_template_missing_studio(self):
        info = {"studio": None, "year": "2024"}
        template = "/data/zugeord/$studio/$year"
        assert "$studio" in get_missing_required_fields(template, info)
