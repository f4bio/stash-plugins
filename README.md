# f4bio's stash plugins

## Index/Source URL:

```bash
https://f4bio.github.io/stash-plugins/main/index.yml
```

<small>_This repo was created based on [feederbox826](https://github.com/feederbox826)'s [repo](https://github.com/feederbox826/plugins) - thanks!_</small>

## Table of Contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
*generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Plugins](#plugins)
  - [`renamerOnUpdate`](#renameronupdate)
  - [`renamerOnUpdateDevelop`](#renameronupdatedevelop)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Deps

### docker

```bash
docker exec stash sh -c "apk update && apk add py3-unidecode"
```

## Plugins

### `renamerOnUpdate`

- Almost 1:1 copy of once official, now deprecated [upstream stash-plugin](https://github.com/stashapp/CommunityScripts/tree/main/archive/renamerOnUpdate)
- Using metadata from your Stash to rename/move your file.
- Further development happens in `renamerOnUpdateDevelop`

### `renamerOnUpdateDevelop`

- A fork of the original `renamerOnUpdate` plugin
- Refactoring, new features, bugfixes will happen here
- Using metadata from your Stash to rename/move your file.

## Dummy/Dev Data

```bash
echo "Downloading dummy data..."
curl -fSL --progress-bar -o /tmp/bbb_sunflower_1080p_30fps_stereo_abl.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_stereo_abl.mp4.zip
curl -fSL --progress-bar -o /tmp/bbb_sunflower_1080p_30fps_normal.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4.zip
curl -fSL --progress-bar -o /tmp/bbb_sunflower_1080p_60fps_normal.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_60fps_normal.mp4.zip
curl -fSL --progress-bar -o /tmp/bbb_sunflower_2160p_30fps_normal.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_2160p_30fps_normal.mp4.zip
curl -fSL --progress-bar -o /tmp/bbb_sunflower_2160p_60fps_normal.mp4.zip https://download.blender.org/demo/movies/BBB/bbb_sunflower_2160p_60fps_normal.mp4.zip

echo "Unzipping dummy data..."
mkdir -p ./dummydata/
unzip /tmp/bbb_sunflower_1080p_30fps_stereo_abl.mp4.zip -d ./dummydata/
unzip /tmp/bbb_sunflower_1080p_30fps_normal.mp4.zip -d ./dummydata/
unzip /tmp/bbb_sunflower_1080p_60fps_normal.mp4.zip -d ./dummydata/
unzip /tmp/bbb_sunflower_2160p_30fps_normal.mp4.zip -d ./dummydata/
unzip /tmp/bbb_sunflower_2160p_60fps_normal.mp4.zip -d ./dummydata/

echo "Copying dummy data to stash..."
docker cp ./dummydata/bbb_sunflower_1080p_30fps_stereo_abl.mp4 stash:/data/
docker cp ./dummydata/bbb_sunflower_1080p_30fps_normal.mp4 stash:/data/
docker cp ./dummydata/bbb_sunflower_1080p_60fps_normal.mp4 stash:/data/
docker cp ./dummydata/bbb_sunflower_2160p_30fps_normal.mp4 stash:/data/
docker cp ./dummydata/bbb_sunflower_2160p_60fps_normal.mp4 stash:/data/
```
