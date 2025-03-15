#!/bin/bash

# Enter repository root directory
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"/..

# Generate JSON-LD context and keyword documentation
python tripper/datadoc/keywords.py \
    --context=tripper/context/0.3/context.json \
    --keywords=docs/datadoc/keywords.md \
    --prefixes=docs/datadoc/prefixes.md

# Don't crash pre-commit in case the above fails on GitHub
exit 0
