#!/bin/bash
# Reads the sql engine from .lynk/config.json
python3 -c "import json,sys; print(json.load(open('.lynk/config.json')).get('engine','unknown'))" 2>/dev/null \
  || echo "unknown"
