#!/bin/bash
source /opt/ros/humble/setup.bash

# Start a tiny background web server on port 80 for health checks
python3 -c "
from flask import Flask
app = Flask(__name__)
@app.route('/health')
def health(): return 'OK', 200
app.run(host='0.0.0.0', port=80)
" &

# Start your actual ROS node in the foreground
exec ros2 run demo_nodes_cpp talker