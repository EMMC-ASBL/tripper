#!/bin/bash

# Enter repository root directory
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"/..

# Generate JSON-LD context and keyword documentation
python tripper/datadoc/keywords.py \
    --explanation \
    --special-keywords \
    --write-context=tripper/context/0.3/context.json \
    --write-kw-md=docs/datadoc/keywords.md \
    --write-prefixes=docs/datadoc/prefixes.md

python tripper/datadoc/keywords.py \
    --explanation \
    --write-context=tripper/context/process/0.1/context.json \
    --write-kw-md=docs/datadoc/keywords-process.md \
    --write-prefixes=docs/datadoc/prefixes-process.md


# Don't crash pre-commit in case the above fails on GitHub
exit 0
