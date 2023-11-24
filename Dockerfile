FROM ubuntu:latest

#   Environmental Variables
ENV USERNAME=app
ENV WORKDIR=/home/$USERNAME


#   Initialize the container
RUN apt update -y && apt upgrade -y                   # Update and Upgrade packages
RUN apt install -y sudo                               # Install necessary binaries
RUN passwd -l root                                    # Disable logging in as the root user
RUN echo "Pacific/Auckland" | tee /etc/timezone       # Set the timezone to Pacific/Auckland


#   Add a new user
RUN adduser --disabled-password --gecos '' $USERNAME
RUN usermod -aG sudo $USERNAME && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" | tee -a /etc/sudoers     # Disable the need for password when running superuser commands in the new user
WORKDIR $WORKDIR
COPY . .
RUN chown -R $USERNAME .


#   Run the application specific commands
RUN chmod +x scripts/initialize.sh && ./scripts/initialize.sh
RUN chmod +x scripts/startup.sh


#   Startup
USER $USERNAME
ENTRYPOINT nohup sudo apt-get update -y >> update.log && sudo apt-get upgrade -y >> update.log \
            & nohup scripts/startup.sh >> server.log \
            & tail -f server.log