#!/bin/bash

# Enter repository root directory
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"/..

# Run doctest on all markdown files in the docs/ directory
find docs -name '*.md' | xargs -n1 python -m doctest
