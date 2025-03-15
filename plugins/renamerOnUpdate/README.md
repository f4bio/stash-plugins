# *renamerOnUpdate*

Using metadata from your Stash to rename/move your file.

## Table of Contents  

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Requirement](#requirement)
- [Installation (manually)](#installation-manually)
- [Installation (via manager)](#installation-via-manager)
- [Usage](#usage)
- [Configuration](#configuration)
- [Custom configuration file](#custom-configuration-file)
- [renamerOnUpdate_config.py explained](#renameronupdate_configpy-explained)
  - [Template](#template)
  - [Filename](#filename)
    - [Filename - Based on a Tag](#filename---based-on-a-tag)
    - [Filename - Based on a Studio](#filename---based-on-a-studio)
    - [Filename - Change filename no matter what](#filename---change-filename-no-matter-what)
  - [Path](#path)
    - [Path - Based on a Tag](#path---based-on-a-tag)
    - [Path - Based on a Studio](#path---based-on-a-studio)
    - [Path - Based on a Path](#path---based-on-a-path)
    - [Path - Change path no matter what](#path---change-path-no-matter-what)
    - [Path - Special Variables](#path---special-variables)
  - [Advanced](#advanced)
    - [Groups](#groups)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Requirement

- Stash (v0.24+)
- Python 3.6+ (Tested LIGHTLY on Python v3.12)
- Request Module (<https://pypi.org/project/requests/>)

## Installation (manually)

- Download the whole folder '**renamerOnUpdate**' (renamerOnUpdate_config.py, log.py, renamerOnUpdate.py/.yml)
- Place it in your **plugins** folder (where the `config.yml` is)
- Reload plugins (Settings > Plugins > Reload)
- *renamerOnUpdate* appears

**_ :exclamation: Make sure to configure the plugin by editing `renamerOnUpdate_config.py` before running it :exclamation: _**

## Installation (via manager)

- Go to Settings > Plugins
- Find **Available Plugins** and expand the package called **Community (stable)**.
- Select `renamerOnUpdate` and click **Install**

**_ :exclamation: Make sure to configure the plugin by editing `renamerOnUpdate_config.py` before running it :exclamation: _**

## Usage

- Everytime you update a scene, it will check/rename your file. An update can be:
  - Saving in **Scene Edit**.
  - Clicking the **Organized** button.
  - Running a scan that **updates** the path.

- By pressing the button in the Task menu.
  - It will go through each of your scenes.
  - :warning: It's recommended to understand correctly how this plugin works, and use **DryRun** first.

## Configuration

- Read/Edit `config.py`
  - Change template filename/path
  - Add `log_file` path

- There are multiple buttons in Task menu:
  - Enable: (default) Enable the trigger update
  - Disable: Disable the trigger update
  - Dry-run: A switch to enable/disable dry-run mode

- Dry-run mode:
  - It prevents editing the file, only shows in your log.
  - This mode can write into a file (`dryrun_renamerOnUpdate.txt`), the change that the plugin will do.
    - You need to set a path for `log_file` in `renamerOnUpdate_config.py`
    - The format will be: `scene_id|current path|new path`. (e.g. `100|C:\Temp\foo.mp4|C:\Temp\bar.mp4`)
    - This file will be overwritten everytime the plugin is triggered.

## Custom configuration file

Due to the nature of how plugin updates work, your `renamerOnUpdate_config.py` file will get replaced with the fresh copy resetting it to default values. To work around that you can create a custom config file and use it instead.

- Create a copy of `renamerOnUpdate_config.py`
- Rename your copy to `config.py`
- Use the `config.py`(it will default to `renamerOnUpdate_config.py` if not found)

> **Note**: Since `config.py` file is not tracked it won't get updated with new configuration options, so you will need to update it manually.

## renamerOnUpdate_config.py explained

### Template

To modify your path/filename, you can use **variables**. These are elements that will change based on your **metadata**.

- Variables are represented with a word preceded with a `$` symbol. (E.g. `$date`)
- If the metadata exists, this term will be replaced by it:
  - Scene date = 2006-01-02, `$date` = 2006-01-02
- You can find the list of available variables in `renamerOnUpdate_config.py`

-----
In the example below, we will use:

- Path: `C:\Temp\QmlnQnVja0J1bm55.mp4`
- This file is [Big Buck Bunny](https://en.wikipedia.org/wiki/Big_Buck_Bunny).

### Filename

Change your filename (C:\Temp\\**QmlnQnVja0J1bm55.mp4**)

-----

**Priority** : Tags > Studios > Default

#### Filename - Based on a Tag

```py
tag_templates  = {
 "rename_tag": "$year $title - $studio $resolution $video_codec",
 "rename_tag2": "$title"
}
```

| tag         | new path                                                         |
| ----------- | ---------------------------------------------------------------- |
| rename_tag  | `C:\Temp\2008 Big Buck Bunny - Blender Institute 1080p H264.mp4` |
| rename_tag2 | `C:\Temp\Big Buck Bunny.mp4`                                     |

#### Filename - Based on a Studio

```py
studio_templates  = {
 "Blender Institute": "$date - $title [$studio]",
 "Pixar": "$title [$studio]"
}
```

| studio            | new path                                                      |
| ----------------- | ------------------------------------------------------------- |
| Blender Institute | `C:\Temp\2008-05-20 - Big Buck Bunny [Blender Institute].mp4` |
| Pixar             | `C:\Temp\Big Buck Bunny [Pixar].mp4`                          |

#### Filename - Change filename no matter what

```py
use_default_template  =  True
default_template  =  "$date $title"
```

The file became: `C:\Temp\2008-05-20 - Big Buck Bunny.mp4`

### Path

Change your path (**C:\Temp**\\QmlnQnVja0J1bm55.mp4)

#### Path - Based on a Tag

```py
p_tag_templates  = {
 "rename_tag": r"D:\Video\",
 "rename_tag2": r"E:\Video\$year"
}
```

| tag         | new path                             |
| ----------- | ------------------------------------ |
| rename_tag  | `D:\Video\QmlnQnVja0J1bm55.mp4`      |
| rename_tag2 | `E:\Video\2008\QmlnQnVja0J1bm55.mp4` |

#### Path - Based on a Studio

```py
p_studio_templates  = {
 "Blender Institute": r"D:\Video\Blender\",
 "Pixar": r"E:\Video\$studio\"
}
```

| studio            | new path                                |
| ----------------- | --------------------------------------- |
| Blender Institute | `D:\Video\Blender\QmlnQnVja0J1bm55.mp4` |
| Pixar             | `E:\Video\Pixar\QmlnQnVja0J1bm55.mp4`   |

#### Path - Based on a Path

```py
p_path_templates = {
 r"C:\Temp": r"D:\Video\",
 r"C:\Video": r"E:\Video\Win\"
}
```

| file path  | new path                            |
| ---------- | ----------------------------------- |
| `C:\Temp`  | `D:\Video\QmlnQnVja0J1bm55.mp4`     |
| `C:\Video` | `E:\Video\Win\QmlnQnVja0J1bm55.mp4` |

#### Path - Change path no matter what

```py
p_use_default_template  =  True
p_default_template  =  r"D:\Video\"
```

The file is moved to: `D:\Video\QmlnQnVja0J1bm55.mp4`

#### Path - Special Variables

`$studio_hierarchy` - Create the entire hierarchy of studio as folder (E.g. `../MindGeek/Brazzers/Hot And Mean/video.mp4`). Use your parent studio.

`^*` - The current directory of the file.
Explanation:

- **If**: `p_default_template = r"^*\$performer"`
- It creates a folder with a performer name in the current directory where the file is.
- `C:\Temp\video.mp4` so  `^*=C:\Temp\`, result: `C:\Temp\Jane Doe\video.mp4`
- If you don't use `prevent_consecutive` option, the plugin will create a new folder everytime (`C:\Temp\Jane Doe\Jane Doe\...\video.mp4`).

### Advanced

#### Groups

You can group elements in the template with `{}`, it's used when you want to remove a character if a variable is null.

Example:

**With** date in Stash:

- `[$studio] $date - $title` -> `[Blender] 2008-05-20 - Big Buck Bunny`

**Without** date in Stash:

- `[$studio] $date - $title` -> `[Blender] - Big Buck Bunny`

If you want to use the `-` only when you have the date, you can group the `-` with `$date`
**Without** date in Stash:

- `[$studio] {$date -} $title` -> `[Blender] Big Buck Bunny`
