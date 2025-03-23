# Utiliser une image Python comme base
FROM python:3.11

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers du projet dans le conteneur
COPY . /app/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port utilisé par Django (par défaut 8000)
EXPOSE 8000

# Commande pour démarrer le serveur Django
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "baol_distributions.wsgi:application"]
