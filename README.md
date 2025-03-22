# f4bio's stash plugins

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Index/Source URL:

```bash
https://f4bio.github.io/stash-plugins/main/index.yml
```

<small>_This repo was created based on [feederbox826](https://github.com/feederbox826)'s [template plugin repo](https://github.com/feederbox826/plugins) - thanks!_</small>

## Plugins

`renamerOnUpdate`

- Continuation of once official, now deprecated [upstream stash-plugin](https://github.com/stashapp/CommunityScripts/tree/main/archive/renamerOnUpdate)
- Using metadata from your Stash to rename/move your file.

## Stash tips

### `scene` schema

```python
{
    "id": "1",
    "title": "BBB Sunflower33333",
    "code": "",
    "details": "",
    "director": "",
    "urls": [],
    "date": "2025-03-17",
    "rating100": None,
    "organized": True,
    "o_counter": 0,
    "interactive": False,
    "interactive_speed": None,
    "captions": None,
    "created_at": "2025-03-14T18:22:47Z",
    "updated_at": "2025-03-22T14:25:54Z",
    "last_played_at": None,
    "resume_time": 0,
    "play_duration": 0,
    "play_count": 0,
    "play_history": [],
    "o_history": [],
    "paths": {
        "screenshot": "http://localhost:9999/scene/1/screenshot?t=1742653554",
        "preview": "http://localhost:9999/scene/1/preview",
        "stream": "http://localhost:9999/scene/1/stream",
        "webp": "http://localhost:9999/scene/1/webp",
        "vtt": "http://localhost:9999/scene/c4f54a04ebd161b2_thumbs.vtt",
        "sprite": "http://localhost:9999/scene/c4f54a04ebd161b2_sprite.jpg",
        "funscript": "http://localhost:9999/scene/1/funscript",
        "interactive_heatmap": "http://localhost:9999/scene/1/interactive_heatmap",
        "caption": "http://localhost:9999/scene/1/caption",
    },
    "scene_markers": [],
    "galleries": [],
    "studio": {"id": "1"},
    "groups": [],
    "tags": [],
    "performers": [{"id": "1"}],
    "stash_ids": [],
    "sceneStreams": [
        {
            "url": "http://localhost:9999/scene/1/stream",
            "mime_type": "video/mp4",
            "label": "Direct stream",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mp4?resolution=ORIGINAL",
            "mime_type": "video/mp4",
            "label": "MP4",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mp4?resolution=FULL_HD",
            "mime_type": "video/mp4",
            "label": "MP4 Full HD (1080p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mp4?resolution=STANDARD_HD",
            "mime_type": "video/mp4",
            "label": "MP4 HD (720p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mp4?resolution=STANDARD",
            "mime_type": "video/mp4",
            "label": "MP4 Standard (480p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mp4?resolution=LOW",
            "mime_type": "video/mp4",
            "label": "MP4 Low (240p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.webm?resolution=ORIGINAL",
            "mime_type": "video/webm",
            "label": "WEBM",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.webm?resolution=FULL_HD",
            "mime_type": "video/webm",
            "label": "WEBM Full HD (1080p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.webm?resolution=STANDARD_HD",
            "mime_type": "video/webm",
            "label": "WEBM HD (720p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.webm?resolution=STANDARD",
            "mime_type": "video/webm",
            "label": "WEBM Standard (480p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.webm?resolution=LOW",
            "mime_type": "video/webm",
            "label": "WEBM Low (240p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.m3u8?resolution=ORIGINAL",
            "mime_type": "application/vnd.apple.mpegurl",
            "label": "HLS",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.m3u8?resolution=FULL_HD",
            "mime_type": "application/vnd.apple.mpegurl",
            "label": "HLS Full HD (1080p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.m3u8?resolution=STANDARD_HD",
            "mime_type": "application/vnd.apple.mpegurl",
            "label": "HLS HD (720p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.m3u8?resolution=STANDARD",
            "mime_type": "application/vnd.apple.mpegurl",
            "label": "HLS Standard (480p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.m3u8?resolution=LOW",
            "mime_type": "application/vnd.apple.mpegurl",
            "label": "HLS Low (240p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mpd?resolution=ORIGINAL",
            "mime_type": "application/dash+xml",
            "label": "DASH",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mpd?resolution=FULL_HD",
            "mime_type": "application/dash+xml",
            "label": "DASH Full HD (1080p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mpd?resolution=STANDARD_HD",
            "mime_type": "application/dash+xml",
            "label": "DASH HD (720p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mpd?resolution=STANDARD",
            "mime_type": "application/dash+xml",
            "label": "DASH Standard (480p)",
        },
        {
            "url": "http://localhost:9999/scene/1/stream.mpd?resolution=LOW",
            "mime_type": "application/dash+xml",
            "label": "DASH Low (240p)",
        },
    ],
    "path": "/data/BunnyRecords/BBB Sunflower3333333 (2025-03-17) - Bunny.mp4",
    "file": {
        "id": "1",
        "path": "/data/BunnyRecords/BBB Sunflower3333333 (2025-03-17) - Bunny.mp4",
        "basename": "BBB Sunflower3333333 (2025-03-17) - Bunny.mp4",
        "parent_folder_id": "4",
        "zip_file_id": None,
        "mod_time": "2025-03-13T15:25:29Z",
        "size": 355856562,
        "fingerprints": [
            {"type": "oshash", "value": "c4f54a04ebd161b2"},
            {"type": "phash", "value": "de83a3120f3eb2ac"},
        ],
        "format": "mp4",
        "width": 1920,
        "height": 1080,
        "duration": 634.57,
        "video_codec": "h264",
        "audio_codec": "mp3",
        "frame_rate": 60,
        "bit_rate": 4486293,
        "created_at": "2025-03-14T18:22:47Z",
        "updated_at": "2025-03-17T22:14:08+01:00",
        "framerate": 60,
    },
}
```
