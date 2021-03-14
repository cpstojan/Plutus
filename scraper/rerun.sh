#!/bin/bash
  
while true;
do
    python rl_scraper.py || echo "App crashed... restarting..." >&2
    echo "Press Ctrl-C to quit." && sleep 1
done
