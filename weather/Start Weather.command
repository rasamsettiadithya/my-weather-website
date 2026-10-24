#!/bin/bash
cd "$(dirname "$0")"
python3 runtime/control.py || {
  echo ""
  echo "Could not open the control panel. Press Enter to close."
  read
}
