#!/bin/bash

# AWS EC2 Django Deployment Script
# Run this on your EC2 instance

set -e

PROJECT_NAME="radar_data"
PROJECT_PATH="/var/www/$PROJECT_NAME"
PYTHON_VERSION="3.11"
USER="ubuntu"

echo "Starting deployment of $PROJECT_NAME..."

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and essential packages
sudo apt-get install -y python$PYTHON_VERSION python$PYTHON_VERSION-pip python$PYTHON_VERSION-venv
sudo apt-get install -y nginx postgresql-client git curl

# Install Node.js (for potential frontend assets)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create project directory
sudo mkdir -p $PROJECT_PATH
sudo chown $USER:$USER $PROJECT_PATH

# Clone repository (replace with your repo URL)
cd /tmp
git clone YOUR_REPOSITORY_URL $PROJECT_NAME
sudo cp -r $PROJECT_NAME/* $PROJECT_PATH/
sudo chown -R $USER:$USER $PROJECT_PATH

# Create virtual environment
cd $PROJECT_PATH
python$PYTHON_VERSION -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p staticfiles
sudo mkdir -p /var/log/gunicorn
sudo chown $USER:$USER /var/log/gunicorn

# Copy environment file
cp .env.example .env
echo "Please edit .env file with your production values"

# Run Django commands
export DJANGO_SETTINGS_MODULE=core.settings.production
python manage.py collectstatic --noinput
python manage.py migrate

# Create systemd service for Gunicorn
sudo tee /etc/systemd/system/radar-data.service > /dev/null <<EOF
[Unit]
Description=Radar Data Django App
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$PROJECT_PATH/venv/bin"
ExecStart=$PROJECT_PATH/venv/bin/gunicorn --config gunicorn.conf.py core.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/radar-data > /dev/null <<EOF
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias $PROJECT_PATH/staticfiles/;
    }

    location /media/ {
        alias $PROJECT_PATH/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/radar-data /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo systemctl daemon-reload
sudo systemctl start radar-data
sudo systemctl enable radar-data
sudo systemctl restart nginx
sudo systemctl enable nginx

# Setup firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

echo "Deployment completed!"
echo "Please:"
echo "1. Edit .env file with your production settings"
echo "2. Update Nginx config with your domain"
echo "3. Restart services: sudo systemctl restart radar-data nginx"
echo "4. Check status: sudo systemctl status radar-data nginx"