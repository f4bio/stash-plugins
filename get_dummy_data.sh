#!/usr/bin/env bash

echo "Downloading dummy data..."
curl -fsSL -o /tmp/bbb_sunflower_1080p_30fps_stereo_abl.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_stereo_abl.mp4.zip
curl -fsSL -o /tmp/bbb_sunflower_1080p_30fps_normal.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4.zip
curl -fsSL -o /tmp/bbb_sunflower_1080p_60fps_normal.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_60fps_normal.mp4.zip
curl -fsSL -o /tmp/bbb_sunflower_2160p_30fps_normal.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_2160p_30fps_normal.mp4.zip
curl -fsSL -o /tmp/bbb_sunflower_2160p_60fps_normal.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_2160p_60fps_normal.mp4.zip

echo "Unzipping dummy data..."
mkdir -p ./dummy/
unzip /tmp/bbb_sunflower_1080p_30fps_stereo_abl.mp4.zip -d ./dummy/
unzip /tmp/bbb_sunflower_1080p_30fps_normal.mp4.zip -d ./dummy/
unzip /tmp/bbb_sunflower_1080p_60fps_normal.mp4.zip -d ./dummy/
unzip /tmp/bbb_sunflower_2160p_30fps_normal.mp4.zip -d ./dummy/
unzip /tmp/bbb_sunflower_2160p_60fps_normal.mp4.zip -d ./dummy/
