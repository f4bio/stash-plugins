import json
import sys

import stashapi.log as log
from stashapi.stashapp import StashInterface

from plugins.organiz3rOnUpdate.scene_information import SceneInformation

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
log.info("config: %s " % (settings,))


def process_scene(stash_scene: SceneInformation):
    log.debug("processing single scene: id=%s".format(stash_scene.id))

    # if the scene has [organiz3rOnUpdate: Skip] then skip it
    if skip_tag in stash_scene.tags:
        log.debug("skipping scene")
        return None

    if settings["useStudioHierarchy"]:
        process_studio_hierarchy(stash_scene)

    return None


def process_studio_hierarchy(stash_scene):
    log.debug("process_studio_hierarchy(stash_scene):" + json.dumps(stash_scene, indent=4))

    return None


def process_scenes():
    log.debug("processing all scenes")
    all_scenes = stash.find_scenes({}, {}, get_count=True)
    log.info("%d scenes to process.".format(len(all_scenes)))


if "mode" in json_input["args"]:
    PLUGIN_ARGS = json_input["args"]["mode"]
    log.debug(json_input)
    if "processScenes" in PLUGIN_ARGS:
        if "scene_id" in json_input["args"]:
            _stash_scene = stash.find_scene(json_input["args"]["scene_id"])
            process_scene(_stash_scene)
        else:
            process_scenes()

elif "hookContext" in json_input["args"]:
    scene_id = json_input["args"]["hookContext"]["id"]
    if json_input["args"]["hookContext"]["type"] == "Scene.Update.Post":
        stash.run_plugin_task("organiz3rOnUpdate", "Process all", args={"scene_id": scene_id})
#        stash_scene = stash.find_scene(id)
#        process_scene(stash_scene)
