#!/usr/bin/env bash
# start.sh

# Start Flask in background
 cd my-app/server/
source venv/bin/activate
python app.py &

# Give Flask a moment, then start React
sleep 1
cd ../client
npm start
