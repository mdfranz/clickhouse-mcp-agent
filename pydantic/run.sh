#!/usr/bin/bash

DATE=`date +%Y%m%d%H%M%S`

for m in gpt-4.1-2025-04-14 gpt-5 gpt-5-mini gpt-5-nano gemini-2.5-flash gemini-2.5-pro claude-haiku-4-5 claude-sonnet-4-5; do
    echo "-> Starting $m"
    ./chdb-sync.py $m >> $DATE-output
    echo "-> $m is complete"
done
