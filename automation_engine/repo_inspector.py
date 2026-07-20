from pathlib import Path


ROOT = Path(".")


IGNORE = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "redfin_profile",
    ".DS_Store"
}


def inventory_repository():

    files = []

    for path in ROOT.rglob("*"):

        if any(part in IGNORE for part in path.parts):
            continue

        if path.is_file():

            files.append(
                str(path)
            )

    return sorted(files)



def summarize_repository():

    files = inventory_repository()

    summary = {
        "total_files": len(files),
        "python_files": [
            f for f in files
            if f.endswith(".py")
        ],
        "docs": [
            f for f in files
            if f.endswith(".md")
        ],
        "configs": [
            f for f in files
            if "config" in f
        ]
    }

    return summary



if __name__ == "__main__":

    import json

    print(
        json.dumps(
            summarize_repository(),
            indent=2
        )
    )
