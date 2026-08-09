#!/bin/bash
# Kill switch — halts the whole engine within ~60s.
# Run from a normal terminal:  ./stop.sh
#  1. STOP file appears -> daemon exits at its next block/sleep check
#  2. running processes are killed outright (daemon, batch child, hook)
#  3. launchd jobs are booted out (best-effort; works from a user terminal)
# No email can go out while STOP exists. Re-arm with ./start.sh.
cd "$(dirname "$0")" || exit 1
touch STOP
pkill -9 -f "pipeline.py daemon" 2>/dev/null
pkill -9 -f "send_batch.py" 2>/dev/null
pkill -9 -f "batch_hook.py" 2>/dev/null
launchctl bootout gui/$(id -u)/com.spielos.outbound.daemon 2>/dev/null
launchctl bootout gui/$(id -u)/com.spielos.outbound.hook 2>/dev/null
echo "STOPPED — engine halted. Remove STOP (or run start.sh) to re-arm."
