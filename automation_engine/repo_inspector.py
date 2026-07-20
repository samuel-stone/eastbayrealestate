import os
import json


ROOT = "."


def scan_repository():

    total_files = 0
    python_files = []
    docs = []
    configs = []


    for root, dirs, files in os.walk(ROOT):

        if ".git" in root:
            continue

        for file in files:

            total_files += 1

            path = os.path.join(root, file)

            if file.endswith(".py"):
                python_files.append(path)

            if file.endswith(".md"):
                docs.append(path)

            if "config" in path:
                configs.append(path)


    return {
        "total_files": total_files,
        "python_files": sorted(python_files),
        "docs": sorted(docs),
        "configs": sorted(configs)
    }



if __name__ == "__main__":

    result = scan_repository()

    print(
        json.dumps(
            result,
            indent=2
        )
    )
