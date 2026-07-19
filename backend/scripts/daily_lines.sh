#!/bin/zsh
# Daily line logging + grading for the Outscaled props paper-trade.
# Installed in crontab: log at 10:00 & 20:00, grade at 12:30.
cd /Users/matthewwiecking/Desktop/Outscaled2/backend || exit 1
case "$1" in
  log)   venv/bin/python scripts/log_lines.py ;;
  grade) venv/bin/python scripts/grade_lines.py ;;
  *)     echo "usage: daily_lines.sh {log|grade}"; exit 1 ;;
esac
