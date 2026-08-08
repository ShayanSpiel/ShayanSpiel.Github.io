#!/bin/bash
# SpielOS outbound supervisor — restarts the daemon within 30s if it dies.
# Runs as a nohup'd background process. Uses ps (pgrep is broken in this sandbox).
cd /Users/shayan/ShayanSpiel.Github.io/.agents/Outbound/scripts || exit 1
LOG=experiments/auto/daemon.out
while true; do
  if ! ps aux | grep -q "[p]ipeline.py daemon"; then
    rm -f experiments/auto/pipeline.pid
    nohup python3 pipeline.py daemon >> "$LOG" 2>&1 &
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) WATCHDOG: daemon dead — restarted" >> "$LOG"
  fi
  sleep 30
done
