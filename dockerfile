FROM python:3.12

WORKDIR /app

# Installer les dépendances système nécessaires pour mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers nécessaires
COPY requirements.txt . 

# Configurer l'environnement virtuel et installer les dépendances
RUN python -m venv /opt/venv && . /opt/venv/bin/activate && pip install -r requirements.txt

# Copier le reste de l'application
COPY . .

# Appliquer les migrations au démarrage
CMD ["/bin/sh", "-c", ". /opt/venv/bin/activate && python manage.py migrate && python create_superuser.py && gunicorn --bind 0.0.0.0:8000 baol_distributions.wsgi:application"]
