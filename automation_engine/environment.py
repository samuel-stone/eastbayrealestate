import os
from dotenv import load_dotenv


load_dotenv()


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


if __name__ == "__main__":
    validate_environment()
