# Run gateway from fork (dev mode)
# Stop any running gateway first: clawdbot gateway stop

$env:NODE_OPTIONS = "--enable-source-maps"
node dist/entry.js gateway --port 18789
