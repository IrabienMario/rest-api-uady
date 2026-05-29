#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Script de instalación en EC2 (Amazon Linux 2023 / Ubuntu)
# Ejecutar con: bash setup_ec2.sh
# ═══════════════════════════════════════════════════════════════

set -e

echo "──────────────────────────────────────────"
echo " Instalando dependencias del sistema..."
echo "──────────────────────────────────────────"

# Detectar distro
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git
elif command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip git
fi

echo "──────────────────────────────────────────"
echo " Clonando / actualizando el repositorio..."
echo "──────────────────────────────────────────"

# Si ya existe el directorio, hacer pull; si no, clonar
APP_DIR="/home/ec2-user/rest-api-uady"
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull
else
    git clone https://github.com/IrabienMario/rest-api-uady.git "$APP_DIR"
    cd "$APP_DIR"
fi

echo "──────────────────────────────────────────"
echo " Creando entorno virtual..."
echo "──────────────────────────────────────────"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "──────────────────────────────────────────"
echo " Configura tu archivo .env antes de iniciar"
echo " cp .env.example .env && nano .env"
echo "──────────────────────────────────────────"

# Crear servicio systemd para que arranque automáticamente
sudo tee /etc/systemd/system/sicei-api.service > /dev/null <<EOF
[Unit]
Description=SICEI REST API - UADY
After=network.target

[Service]
User=ec2-user
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python app.py
Restart=always
RestartSec=5
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sicei-api
echo ""
echo "✅ Instalación completa."
echo ""
echo "Pasos finales:"
echo "  1. Edita el .env:        nano $APP_DIR/.env"
echo "  2. Inicia el servicio:   sudo systemctl start sicei-api"
echo "  3. Ver logs:             sudo journalctl -u sicei-api -f"
