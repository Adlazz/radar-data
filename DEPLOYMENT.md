# Guía de Deployment a AWS Free Tier

Esta guía te ayudará a desplegar tu blog Django "Radar Data" en AWS usando el Free Tier.

## Prerrequisitos

1. Cuenta de AWS activa
2. Clave SSH para acceso a EC2
3. Repositorio Git con tu código
4. Conocimientos básicos de terminal/SSH

## 1. Configurar EC2 Instance (t2.micro - Free Tier)

### Crear Instancia EC2
1. Ve al panel de EC2 en AWS Console
2. Click "Launch Instance"
3. Selecciona "Ubuntu Server 22.04 LTS (HVM)"
4. Selecciona "t2.micro" (Free tier eligible)
5. Crear o seleccionar Key Pair para SSH
6. Configurar Security Group:
   - SSH (port 22) desde tu IP
   - HTTP (port 80) desde anywhere (0.0.0.0/0)
   - HTTPS (port 443) desde anywhere (0.0.0.0/0)
7. Launch Instance

### Conectar a tu instancia
```bash
ssh -i "tu-key.pem" ubuntu@tu-ec2-public-ip
```

## 2. Configurar RDS PostgreSQL (Free Tier)

### Crear RDS Instance
1. Ve al panel de RDS en AWS Console
2. Click "Create database"
3. Selecciona "PostgreSQL"
4. Selecciona "Free tier" template
5. Configuración:
   - DB instance identifier: radar-data-db
   - Master username: postgres
   - Master password: [tu-password-seguro]
   - DB instance class: db.t3.micro
6. En "Additional configuration":
   - Initial database name: radar_data
7. Asegúrate de que esté en la misma VPC que tu EC2
8. Create database

### Configurar Security Group de RDS
1. Ve a tu RDS instance
2. Click en el Security Group
3. Agregar regla inbound:
   - Type: PostgreSQL
   - Port: 5432
   - Source: Security Group de tu EC2

## 3. Configurar S3 Bucket para Static/Media Files

### Crear S3 Bucket
1. Ve al panel de S3
2. Click "Create bucket"
3. Nombre único: tu-proyecto-static-files
4. Region: us-east-1 (o tu región preferida)
5. Desactivar "Block all public access"
6. Create bucket

### Configurar IAM User para S3
1. Ve al panel de IAM
2. Crear nuevo usuario: radar-data-s3-user
3. Adjuntar política: AmazonS3FullAccess
4. Generar Access Key y Secret Key

## 4. Deploy en EC2

### Subir código a GitHub/GitLab
```bash
git add .
git commit -m "Production deployment setup"
git push origin main
```

### Ejecutar script de deployment
1. Copia el archivo `deploy/deploy.sh` a tu servidor
2. Edita la URL del repositorio en el script
3. Ejecuta el script:

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

### Configurar variables de entorno
Edita el archivo `.env` en el servidor:

```bash
cd /var/www/radar_data
sudo nano .env
```

Completa con tus valores:
```env
# Django Settings
SECRET_KEY=tu-secret-key-super-seguro
DEBUG=False
ALLOWED_HOST=tu-dominio.com
DOMAIN=tu-dominio.com

# Database (RDS)
DB_NAME=radar_data
DB_USER=postgres
DB_PASSWORD=tu-password-rds
DB_HOST=tu-rds-endpoint.amazonaws.com
DB_PORT=5432

# AWS S3
AWS_ACCESS_KEY_ID=tu-access-key
AWS_SECRET_ACCESS_KEY=tu-secret-key
AWS_STORAGE_BUCKET_NAME=tu-bucket-name
AWS_S3_REGION_NAME=us-east-1

# OpenAI (opcional)
OPENAI_API_KEY=tu-openai-key
```

### Actualizar configuración de Nginx
```bash
sudo nano /etc/nginx/sites-available/radar-data
```

Reemplaza `YOUR_DOMAIN_OR_IP` con tu dominio o IP pública.

### Reiniciar servicios
```bash
sudo systemctl restart radar-data
sudo systemctl restart nginx
```

## 5. Configuración SSL con Let's Encrypt (Opcional)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

## 6. Comandos útiles de mantenimiento

### Ver logs
```bash
# Logs de Django/Gunicorn
sudo journalctl -u radar-data -f

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Actualizar código
```bash
cd /var/www/radar_data
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart radar-data
```

### Estado de servicios
```bash
sudo systemctl status radar-data
sudo systemctl status nginx
sudo systemctl status postgresql
```

## 7. Costos estimados (Free Tier)

- **EC2 t2.micro**: Gratis por 12 meses (750 horas/mes)
- **RDS db.t3.micro**: Gratis por 12 meses (750 horas/mes, 20GB storage)
- **S3**: 5GB gratis permanente
- **Transfer**: 15GB gratis salida/mes

## Troubleshooting

### Error de conexión a base de datos
- Verifica Security Groups
- Confirma endpoint y credenciales de RDS

### Static files no cargan
- Verifica configuración S3
- Confirma permisos IAM
- Ejecuta `collectstatic` nuevamente

### 502 Bad Gateway
- Verifica que Gunicorn esté corriendo: `sudo systemctl status radar-data`
- Revisa logs: `sudo journalctl -u radar-data`

### Problemas de memoria
- El t2.micro tiene 1GB RAM limitado
- Considera optimizar configuración de Gunicorn
- Monitorea uso: `htop`