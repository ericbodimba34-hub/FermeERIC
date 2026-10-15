# Guide Complet de Déploiement — Application DFM
### La Ferme de Diégonefla (Côte d'Ivoire)

Ce guide détaille les 3 options de déploiement adaptées aux réalités de l'exploitation de Diégonefla (accès local sans internet, cloud tout-en-un, ou serveur VPS professionnel).

---

## Sommaire
1. [Option 1 : Déploiement Cloud Rapide & Gratuit / Économique (Render / PythonAnywhere)](#option-1)
2. [Option 2 : Déploiement Professionnel sur VPS Linux (Ubuntu + Nginx + Gunicorn + HTTPS)](#option-2)
3. [Option 3 : Déploiement Local à la Ferme (Fonctionnement hors-ligne sur réseau Wi-Fi local)](#option-3)
4. [Politique de Sauvegarde Automatique des Données](#option-4)

---

<a name="option-1"></a>
## Option 1 : Déploiement Cloud Rapide (Render ou PythonAnywhere)
*Recommandé si vous souhaitez un accès immédiat pour l'équipe sur smartphone et ordinateur avec HTTPS automatique sans administrer de serveur Linux.*

### Déploiement sur Render.com (Gratuit / 7$/mois)
1. Créez un compte gratuit sur [Render.com](https://render.com).
2. Déposez le dossier de l'application sur un dépôt GitHub (privé ou public).
3. Sur Render, cliquez sur **New +** > **Web Service**.
4. Connectez votre dépôt GitHub.
5. Renseignez la configuration :
   - **Environment :** `Python 3`
   - **Build Command :** `pip install -r requirements.txt`
   - **Start Command :** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
6. Ajoutez un **Disque Persistant** (Persistent Disk) monté sur `/home/user/dfm-app/data` pour que la base SQLite `dfm_ferme.db` conserve vos données entre les redémarrages.
7. Cliquez sur **Create Web Service**. Votre application est en ligne avec une adresse sécurisée en `https://dfm-diegonefla.onrender.com`.

---

<a name="option-2"></a>
## Option 2 : Déploiement VPS Dédié (Production Robuste avec Nom de Domaine & HTTPS)
*Conforme aux exigences des sections 4.3 et 5.3 du Cahier des Charges (remplacement de dfm.test par https://app.ferme-diegonefla.ci).*

### 1. Prérequis
- Un serveur VPS Linux (Ubuntu 22.04 ou 24.04 LTS) chez un hébergeur (OVHcloud, Hetzner, DigitalOcean, Linode) : coût ~4 à 6 € / mois.
- Un nom de domaine (ex: `ferme-diegonefla.ci` ou `dfm-ferme.com`) pointant vers l'adresse IP du serveur.

### 2. Installation des paquets sur le VPS
Connectez-vous en SSH à votre serveur :
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx -y
```

### 3. Transfert des fichiers du projet
```bash
sudo mkdir -p /var/www/dfm-app
sudo chown -R $USER:$USER /var/www/dfm-app
# Copiez les fichiers du projet dans ce dossier :
cd /var/www/dfm-app
```

### 4. Environnement virtuel Python et dépendances
```bash
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn openpyxl
python3 database.py  # Initialise la base de données
```

### 5. Configuration du service d'arrière-plan (Systemd)
Pour que l'application démarre toute seule au démarrage du serveur et redémarre automatiquement en cas d'erreur :
Créez le fichier de service :
```bash
sudo nano /etc/systemd/system/dfm.service
```

Collez le contenu suivant :
```ini
[Unit]
Description=Application DFM La Ferme de Diegonefla
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/dfm-app
Environment="PATH=/var/www/dfm-app/venv/bin"
ExecStart=/var/www/dfm-app/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Donnez les bons droits au dossier de données :
```bash
sudo chown -R www-data:www-data /var/www/dfm-app
sudo chmod -R 775 /var/www/dfm-app/data
```

Activez et démarrez le service :
```bash
sudo systemctl daemon-reload
sudo systemctl start dfm
sudo systemctl enable dfm
sudo systemctl status dfm
```

### 6. Configuration du serveur Web Nginx (Reverse Proxy)
Créez la configuration Nginx :
```bash
sudo nano /etc/nginx/sites-available/dfm
```

Collez la configuration suivante (remplacez `app.ferme-diegonefla.ci` par votre domaine ou l'adresse IP du VPS) :
```nginx
server {
    listen 80;
    server_name app.ferme-diegonefla.ci;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/dfm-app/static/;
        expires 30d;
    }
}
```

Activez le site et testez Nginx :
```bash
sudo ln -s /etc/nginx/sites-available/dfm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Activation du cadenas vert HTTPS (Certificat SSL Gratuit)
```bash
sudo certbot --nginx -d app.ferme-diegonefla.ci
```
Certbot va configurer automatiquement le chiffrement SSL/TLS et son renouvellement automatique. Votre site est désormais accessible en `https://app.ferme-diegonefla.ci`.

---

<a name="option-3"></a>
## Option 3 : Déploiement Local à la Ferme (100% Hors-Ligne sur Réseau Wi-Fi Local)
*Recommandé si la ferme de Diégonefla subit des coupures d'électricité ou d'internet fréquentes.*

Vous pouvez installer l'application sur un **ordinateur portable classique (Windows ou Linux)** ou un **mini-ordinateur (Raspberry Pi ou Mini-PC)** situé dans le bureau de la ferme :

1. Installez Python 3 sur la machine.
2. Téléchargez le dossier `dfm-app`.
3. Lancez l'application :
   ```bash
   python app.py
   ```
4. Connectez cette machine au routeur Wi-Fi du bureau de la ferme.
5. Repérez son adresse IP locale (ex: `192.168.1.50`).
6. **Tous les collaborateurs connectés au Wi-Fi de la ferme peuvent ouvrir le logiciel sur leur smartphone, tablette ou ordinateur** en ouvrant simplement leur navigateur à l'adresse :
   ```text
   http://192.168.1.50:5000
   ```
   *Aucune connexion Internet n'est requise.*

---

<a name="option-4"></a>
## 4. Politique de Sauvegarde Quotidienne Automatique
Pour sécuriser les données de la ferme contre tout incident, activez une sauvegarde automatique quotidienne par script cron :

```bash
crontab -e
```
Ajoutez cette ligne pour créer une copie horodatée de la base SQLite tous les soirs à 23h00 :
```bash
0 23 * * * cp /var/www/dfm-app/data/dfm_ferme.db /var/backups/dfm_backup_$(date +\%Y\%m\%d).db
```

En parallèle, le gérant peut à tout moment se rendre dans le menu **Rapports & Paramètres** et cliquer sur **Exporter la Sauvegarde Complète (JSON)** pour garder une copie sur sa clé USB ou son ordinateur personnel.
