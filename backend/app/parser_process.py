"""Resource-limited parser entry point. No provider credentials in its environment."""

import json
import os
import resource
import sys


def main():
    memory = int(os.environ["PARSER_MEMORY_MB"]) * 1024 * 1024
    seconds = int(os.environ["PARSER_TIMEOUT"])
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    from .parsing import extract

    try:
        pages = extract(
            sys.argv[1],
            sys.stdin.buffer.read(int(os.environ["MAX_UPLOAD_BYTES"]) + 1),
            int(os.environ["MAX_UPLOAD_BYTES"]),
            int(os.environ["MAX_TEXT_CHARS"]),
        )
        print(json.dumps(pages))
    except Exception:
        sys.exit(2)


if __name__ == "__main__":
    main()
