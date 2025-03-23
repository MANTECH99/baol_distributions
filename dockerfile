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

# Exécuter les migrations
RUN . /opt/venv/bin/activate && python manage.py migrate

# Créer le superutilisateur seulement s'il n'existe pas
RUN . /opt/venv/bin/activate && \
    echo "from django.contrib.auth import get_user_model; \
    User = get_user_model(); \
    User.objects.create_superuser('admin', 'dimariaagueye100@gmail.com', 'Mantech772607977') \
    if not User.objects.filter(username='admin').exists() else None" \
    | python manage.py shell

# Lancer Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "baol_distributions.wsgi:application"]
