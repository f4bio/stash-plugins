import os
import sqlite3
from datetime import datetime


def db_rename(_stash_db: sqlite3.Connection, scene_info):
  cursor = _stash_db.cursor()
  # Database rename
  cursor.execute(
    "UPDATE scenes SET path=? WHERE id=?;",
    [scene_info["final_path"], scene_info["scene_id"]],
  )
  _stash_db.commit()
  # Close DB
  cursor.close()


def db_rename_refactor(_stash_db: sqlite3.Connection, scene_info):
  cursor = _stash_db.cursor()
  # 2022-09-17T11:25:52+02:00
  mod_time = datetime.now().astimezone().isoformat("T", "seconds")

  # get the next id that we should use if needed
  cursor.execute("SELECT MAX(id) from folders")
  new_id = cursor.fetchall()[0][0] + 1

  # get the old folder id
  cursor.execute(
    "SELECT id FROM folders WHERE path=?", [scene_info["current_directory"]]
  )
  old_folder_id = cursor.fetchall()[0][0]

  # check if the folder of file is created in db
  cursor.execute("SELECT id FROM folders WHERE path=?", [scene_info["new_directory"]])
  folder_id = cursor.fetchall()
  if not folder_id:
    _dir = scene_info["new_directory"]
    # reduce the path to find a parent folder
    for _ in range(1, len(scene_info["new_directory"].split(os.sep))):
      _dir = os.path.dirname(_dir)
      cursor.execute("SELECT id FROM folders WHERE path=?", [_dir])
      parent_id = cursor.fetchall()
      if parent_id:
        # create a new row with the new folder with the parent folder find above
        cursor.execute(
          "INSERT INTO 'main'.'folders'('id', 'path', 'parent_folder_id', 'mod_time', 'created_at', 'updated_at', 'zip_file_id') VALUES (?, ?, ?, ?, ?, ?, ?);",
          [
            new_id,
            scene_info["new_directory"],
            parent_id[0][0],
            mod_time,
            mod_time,
            mod_time,
            None,
          ],
        )
        _stash_db.commit()
        folder_id = new_id
        break
  else:
    folder_id = folder_id[0][0]
  if folder_id:
    cursor.execute(
      "SELECT file_id from scenes_files WHERE scene_id=?",
      [scene_info["scene_id"]],
    )
    file_ids = cursor.fetchall()
    file_id = None
    for f in file_ids:
      # it can have multiple file for a scene
      cursor.execute("SELECT parent_folder_id from files WHERE id=?", [f[0]])
      check_parent = cursor.fetchall()[0][0]
      # if the parent id is the one found above section, we find our file.s
      if check_parent == old_folder_id:
        file_id = f[0]
        break
    if file_id:
      # log.debug(f"UPDATE files SET basename={scene_info['new_filename']}, parent_folder_id={folder_id}, updated_at={mod_time} WHERE id={file_id};")
      cursor.execute(
        "UPDATE files SET basename=?, parent_folder_id=?, updated_at=? WHERE id=?;",
        [scene_info["new_filename"], folder_id, mod_time, file_id],
      )
      cursor.close()
      _stash_db.commit()
    else:
      raise Exception("Failed to find file_id")
  else:
    cursor.close()
    raise Exception(
      f"You need to setup a library with the new location ({scene_info['new_directory']}) and scan at least 1 file"
    )


class DBOperations:
  """Class with all the file operations"""
  config = None
  log = None
  stash = None

  def __init__(self, log, config, stash):
    self.config = config
    self.log = log
    self.stash = stash


  def checking_duplicate_db(self, scene_info: dict):
    # find scenes in db with the same path
    _scenes = self.stash.find_scenes(
      f={"path": {"modifier": "EQUALS", "value": scene_info["final_path"]}},
      filter={"direction": "ASC", "page": 1, "per_page": 40, "sort": "updated_at"},
      get_count=True,
    )
    if _scenes[0] > 0:
      self.log.error("Duplicate path detected")
      for dupl_row in _scenes[1]:
        self.log.warning(f"Identical path: [{dupl_row}]")
      return 1  # TODO: is this needed?

    # the result type of find_scenes with get_count: (<number>, <list>); <number> is the count of scenes
    _scenes = self.stash.find_scenes(
      f={"path": {"modifier": "EQUALS", "value": scene_info["new_filename"]}},
      filter={"direction": "ASC", "page": 1, "per_page": 40, "sort": "updated_at"},
      get_count=True,
    )
    if _scenes[0] > 0:
      for dupl_row in _scenes[1]:
        if dupl_row["id"] != scene_info["scene_id"]:
          self.log.warning(f"Duplicate filename: [{dupl_row}]")
    return None
