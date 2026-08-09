#!/bin/bash
# SpielOS outbound supervisor — restarts the daemon AND the wake hook within
# 30s if either dies. Runs as a nohup'd background process (or under launchd).
# Day-3 config (owner rule 2026-08-09): cap 300/day, 50-email blocks,
# 150s throttle (warmup caution after the 0.41% spam flag), hook supervised
# so wake events survive session end.
cd /Users/shayan/ShayanSpiel.Github.io/.agents/Outbound/scripts || exit 1
LOG=experiments/auto/daemon.out
export BLOCK_SIZE=50
export THROTTLE_SECONDS=150
export WARMUP_DAILY_CAP=300
while true; do
  if [ -f STOP ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) WATCHDOG: STOP file present — supervisor exiting" >> "$LOG"
    exit 0
  fi
  if ! ps aux | grep -q "[p]ipeline.py daemon"; then
    rm -f experiments/auto/pipeline.pid
    nohup python3 pipeline.py daemon >> "$LOG" 2>&1 &
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) WATCHDOG: daemon dead — restarted" >> "$LOG"
  fi
  if ! ps aux | grep -q "[b]atch_hook.py"; then
    rm -f experiments/auto/hook_offset
    nohup python3 batch_hook.py >> "$LOG" 2>&1 &
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) WATCHDOG: hook dead — restarted" >> "$LOG"
  fi
  sleep 30
done
