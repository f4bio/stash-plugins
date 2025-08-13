import json
import sys

import stashapi.log as log
from stashapi.stashapp import StashInterface

from scene_information import SceneInformation

per_page = 100
skip_tag = "[organiz3rOnUpdate: Skip]"

# Defaults if nothing has changed in the stash ui
settings = {"useStudioHierarchy": True}

json_input = json.loads(sys.stdin.read())

FRAGMENT_SERVER = json_input["server_connection"]
stash = StashInterface(FRAGMENT_SERVER)
config = stash.get_configuration()["plugins"]
if "organiz3rOnUpdate" in config:
    settings.update(config["organiz3rOnUpdate"])
log.info("config: {} ".format(settings))


def make_filename(filename: str):
    _filename = filename.lower()

    return _filename


def make_directory(directory: str):
    _directory = directory.lower()

    return _directory


def process_single_scene(stash_scene: SceneInformation):
    log.debug("processing single scene: id={}".format(stash_scene.id))

    # if the scene has [organiz3rOnUpdate: Skip] then skip it
    if skip_tag in stash_scene.tags:
        log.debug("skipping scene")
        return None

    if settings["useStudioHierarchy"]:
        log.debug("useStudioHierarchy(stash_scene):" + json.dumps(stash_scene, indent=4))

    return None


def process_all_scenes():
    log.debug("processing all scenes")
    all_scenes = stash.find_scenes({}, {}, get_count=True)
    log.info("{} scenes to process.".format(len(all_scenes)))

    for scene in all_scenes[1]:
        log.debug("processing scene: {}".format(scene))
        scene_information = SceneInformation(scene)

        log.debug("extracted scene information: {}".format(json.dumps(scene_information)))

        _studio = stash.find_studio(scene_information.studio)
        log.debug("found studio: {}".format(_studio))

        _new_filename = make_filename(scene_information.filename)
        _new_directory = make_directory(scene_information.directory)

        log.debug("_new_filename: {}".format(_new_filename))
        log.debug("_new_directory: {}".format(_new_directory))

        _result = stash.move_files(dict({
            "ids": [
                scene_information.id
            ],
            "destination_folder": scene_information.studio,
            "destination_basename": _new_filename
        }))
        log.debug("move result: {}".format(_result))

    return None


if "mode" in json_input["args"]:
    PLUGIN_ARGS = json_input["args"]["mode"]
    log.debug("PLUGIN_ARGS: {}".format(PLUGIN_ARGS))
    if "processScenes" in PLUGIN_ARGS:
        if "scene_id" in json_input["args"]:
            _stash_scene = stash.find_scene(json_input["args"]["scene_id"])
            _stash_scene_information = SceneInformation(_stash_scene)
            process_single_scene(_stash_scene_information)
        else:
            process_all_scenes()

elif "hookContext" in json_input["args"]:
    scene_id = json_input["args"]["hookContext"]["id"]
    if json_input["args"]["hookContext"]["type"] == "Scene.Update.Post":
        stash.run_plugin_task("organiz3rOnUpdate", "Process all", args={"scene_id": scene_id})
#        stash_scene = stash.find_scene(id)
#        process_scene(stash_scene)
