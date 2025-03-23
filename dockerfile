# Utiliser une image Python optimisée
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc \
    && rm -rf /var/lib/apt/lists/*  # Nettoyer pour réduire la taille de l'image

# Créer un utilisateur non-root
RUN useradd -m appuser
USER appuser

# Copier uniquement requirements.txt pour optimiser le cache
COPY --chown=appuser:appuser requirements.txt .  

# Créer un environnement virtuel et installer les dépendances
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY --chown=appuser:appuser . .

# Exposer le port
EXPOSE 8000

# Lancer Gunicorn
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "baol_distributions.wsgi:application"]
