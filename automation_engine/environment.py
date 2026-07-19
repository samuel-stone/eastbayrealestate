import os


def validate_environment():

    required = [
        "DATABASE_URL"
    ]

    missing = []

    for item in required:

        if not os.environ.get(item):
            missing.append(item)


    if missing:

        raise RuntimeError(
            f"Missing environment variables: {missing}"
        )


    print(
        "Environment validated"
    )
