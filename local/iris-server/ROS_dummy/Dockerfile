FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive

# Install ROS demo nodes AND python3-flask for the health server
RUN apt-get update && apt-get install -y \
    ros-humble-demo-nodes-cpp \
    python3-flask \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

# Copy the startup script into the image
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose the port your backend checks
EXPOSE 80

CMD ["/start.sh"]