import json
import sys

import requests
import stashapi.log as log


def exit_plugin(msg=None, err=None):
    if msg is None and err is None:
        msg = "plugin ended"
    output_json = {"output": msg, "error": err}
    print(json.dumps(output_json))
    sys.exit()


def callGraphQL(FRAGMENT_SERVER, query, variables=None):
    # Session cookie for authentication
    response = None
    graphql_port = str(FRAGMENT_SERVER["Port"])
    graphql_scheme = FRAGMENT_SERVER["Scheme"]
    graphql_cookies = {"session": FRAGMENT_SERVER["SessionCookie"]["Value"]}
    graphql_headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "DNT": "1",
    }
    graphql_domain = FRAGMENT_SERVER["Host"]
    if graphql_domain == "0.0.0.0":
        graphql_domain = "localhost"
    # Stash GraphQL endpoint
    graphql_url = f"{graphql_scheme}://{graphql_domain}:{graphql_port}/graphql"

    _json = {"query": query}
    if variables is not None:
      _json["variables"] = variables
    try:
        response = requests.post(
            graphql_url,
            json=_json,
            headers=graphql_headers,
            cookies=graphql_cookies,
            timeout=20,
        )
    except Exception as e:
        exit_plugin(err=f"[FATAL] Error with the graphql request {e}")
    if response.status_code == 200:
        result = response.json()
        if result.get("error"):
            for error in result["error"]["errors"]:
                raise Exception(f"GraphQL error: {error}")
            return None
        if result.get("data"):
            return result.get("data")
    elif response.status_code == 401:
        exit_plugin(err="HTTP Error 401, Unauthorised.")
    else:
        raise ConnectionError(
            f"GraphQL query failed: {response.status_code} - {response.content}"
        )


def graphql_getScene(FILE_QUERY, scene_id):
    query = (
        """
query FindScene($id: ID!, $checksum: String) {
    findScene(id: $id, checksum: $checksum) {
        ...SceneData
    }
}
fragment SceneData on Scene {
    id
    title
    date
    rating100
    stash_ids {
        endpoint
        stash_id
    }
    organized"""
        + FILE_QUERY
        + """
        studio {
            id
            name
            parent_studio {
                id
                name
            }
        }
        tags {
            id
            name
        }
        performers {
            id
            name
            gender
            favorite
            rating100
            stash_ids{
                endpoint
                stash_id
            }
        }
        movies {
            movie {
                name
                date
            }
            scene_index
        }
    }
    """
    )
    variables = {"id": scene_id}
    result = callGraphQL(query, variables)
    return result.get("findScene")


# used for bulk
def graphql_findScene(FILE_QUERY, perPage, direc="DESC") -> dict:
    query = (
        """
query FindScenes($filter: FindFilterType) {
    findScenes(filter: $filter) {
        count
        scenes {
            ...SlimSceneData
        }
    }
}
fragment SlimSceneData on Scene {
    id
    title
    date
    rating100
    organized
    stash_ids {
        endpoint
        stash_id
    }
"""
        + FILE_QUERY
        + """
        studio {
            id
            name
            parent_studio {
                id
                name
            }
        }
        tags {
            id
            name
        }
        performers {
            id
            name
            gender
            favorite
            rating100
            stash_ids{
                endpoint
                stash_id
            }
        }
        movies {
            movie {
                name
                date
            }
            scene_index
        }
    }
    """
    )
    # ASC DESC
    variables = {
        "filter": {
            "direction": direc,
            "page": 1,
            "per_page": perPage,
            "sort": "updated_at",
        }
    }
    result = callGraphQL(query, variables)
    result = result.get("findScenes")
    return result


# used to find duplicate
def graphql_findScenebyPath(path, modifier) -> dict:
    query = """
    query FindScenes($filter: FindFilterType, $scene_filter: SceneFilterType) {
        findScenes(filter: $filter, scene_filter: $scene_filter) {
            count
            scenes {
                id
                title
            }
        }
    }
    """
    # ASC DESC
    variables = {
        "filter": {"direction": "ASC", "page": 1, "per_page": 40, "sort": "updated_at"},
        "scene_filter": {"path": {"modifier": modifier, "value": path}},
    }
    result = callGraphQL(query, variables)
    return result.get("findScenes")


def graphql_getConfiguration():
    query = """
        query Configuration {
            configuration {
                general {
                    databasePath
                }
            }
        }
    """
    result = callGraphQL(query)
    return result.get("configuration")


def graphql_getStudio(studio_id):
    query = """
        query FindStudio($id:ID!) {
            findStudio(id: $id) {
                id
                name
                parent_studio {
                    id
                    name
                }
            }
        }
    """
    variables = {"id": studio_id}
    result = callGraphQL(query, variables)
    return result.get("findStudio")


def graphql_removeScenesTag(id_scenes: list, id_tags: list):
    query = """
    mutation BulkSceneUpdate($input: BulkSceneUpdateInput!) {
        bulkSceneUpdate(input: $input) {
            id
        }
    }
    """
    variables = {
        "input": {"ids": id_scenes, "tag_ids": {"ids": id_tags, "mode": "REMOVE"}}
    }
    result = callGraphQL(query, variables)
    return result


def graphql_getBuild(FRAGMENT_SERVER):
    query = """
        {
            systemStatus {
                databaseSchema
            }
        }
    """
    result = callGraphQL(FRAGMENT_SERVER, query)
    return result["systemStatus"]["databaseSchema"]
