#!/bin/bash
# Re-arm the engine after a stop. Run from a normal terminal:  ./start.sh
# Removes the STOP file and starts the supervisor, which brings the daemon
# back up within 30s.
cd "$(dirname "$0")" || exit 1
rm -f STOP
nohup bash supervise.sh >> experiments/auto/supervise.out 2>&1 &
echo "ENGINE RE-ARMED (supervisor pid $!)."
