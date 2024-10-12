from WithSecure.common.path_completion import complete as on_console,get_folder_and_search_path, get_suggestions

def on_agent(path, context):
    """
    Provides path completion, against files local to the Agent.
    """
    if path == "":
        path = "/"

    folder, search_path = get_folder_and_search_path(path, "/")
    folders = context.listFiles(folder)
    
    return [s.replace(" ", r"\ ") for s in get_suggestions(folder, search_path, map(lambda f: str(f), folders), "/", True)]
    
