#!/bin/bash

eco "installing requirements"
pip install -r requirements.txt
eco "requirements installed"

eco "making migrations"
py manage.py makemigrations 
py manage.py migrate 
eco "migrations maded"

eco "identifying port for running"
PORT="8000"
HOST_IP=$(hostname -I | awk '{print $1}')
HOST=${HOST_IP:-"127.0.0.1"}
echo "Server will be hosted at: $HOST:$PORT"

echo_message "Starting the Django development server..."
echo "Server is running at: http://$HOST:$PORT"
echo "Press CTRL+C to stop the server.

py manage.py runserver "$HOST:$PORT"

