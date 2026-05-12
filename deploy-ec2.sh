#!/bin/bash
set -e

echo "============================================"
echo "  BotHunter EC2 Setup — Phase 2"
echo "============================================"

# Step 1: Create swap file (2GB safety net)
echo "[1/8] Creating 2GB swap file..."
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
echo "✅ Swap enabled"

# Step 2: Install system dependencies
echo "[2/8] Installing system packages..."
sudo dnf update -y -q
sudo dnf install -y -q python3.11 python3.11-pip python3.11-devel git nginx gcc g++
echo "✅ System packages installed"

# Step 3: Install Certbot for SSL
echo "[3/8] Installing Certbot..."
sudo dnf install -y -q certbot python3-certbot-nginx || {
    sudo pip3.11 install certbot certbot-nginx
}
echo "✅ Certbot installed"

# Step 4: Clone the repository
echo "[4/8] Cloning Bot-Hunter repository..."
cd /home/ec2-user
if [ -d "Bot-Hunter-" ]; then
    cd Bot-Hunter-
    git pull origin main
else
    git clone https://github.com/ABDULAH-ab/Bot-Hunter-.git
    cd Bot-Hunter-
fi
echo "✅ Repository cloned"

# Step 5: Create Python venv and install dependencies
echo "[5/8] Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install CPU-only PyTorch first (saves 1.5GB vs CUDA version)
echo "  → Installing PyTorch CPU..."
pip install --no-cache-dir torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -1

echo "  → Installing torch-geometric..."
pip install --no-cache-dir torch-geometric 2>&1 | tail -1

echo "  → Installing transformers..."
pip install --no-cache-dir transformers 2>&1 | tail -1

echo "  → Installing remaining dependencies..."
pip install --no-cache-dir -r requirements.txt 2>&1 | tail -1

echo "✅ Python dependencies installed"

# Step 6: Create production .env
echo "[6/8] Production .env will be created separately..."
echo "✅ Skipped (manual step)"

# Step 7: Configure Nginx
echo "[7/8] Configuring Nginx..."

# Rate limiting zone
sudo tee /etc/nginx/conf.d/rate-limit.conf > /dev/null << 'RATE_EOF'
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
RATE_EOF

# API reverse proxy
sudo tee /etc/nginx/conf.d/bothunter-api.conf > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name api.bothunter.app;

    client_max_body_size 10M;

    location / {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
NGINX_EOF

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx
echo "✅ Nginx configured and running"

# Step 8: Create systemd service
echo "[8/8] Creating systemd service..."
sudo tee /etc/systemd/system/bothunter.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=BotHunter FastAPI Backend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/Bot-Hunter-/Web/backend
EnvironmentFile=/home/ec2-user/bothunter.env
ExecStart=/home/ec2-user/Bot-Hunter-/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable bothunter
echo "✅ Systemd service created"

echo ""
echo "============================================"
echo "  ✅ Setup complete!"
echo "  Next: create /home/ec2-user/bothunter.env"
echo "  Then: sudo systemctl start bothunter"
echo "============================================"
