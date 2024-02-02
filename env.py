import os

def get(name: str, default: str | None = None) -> str:
    """
    getenv function is used to fetch the environment variable for the
    passed key and exits with a non zero status code if the variable is not set.
    """
    val = os.getenv(name)
    if val is None:
        if default is not None:
            return default
        print(f"Environment variable {name} required to be set")
        exit(2)
    return val
