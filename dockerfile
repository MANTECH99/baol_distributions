FROM python:3.12

WORKDIR /app

# Installer les dépendances système nécessaires pour mysqlclient
apt-get update && apt-get install -y default-libmysqlclient-dev


# Configurer l'environnement virtuel et installer les dépendances Python
COPY requirements.txt .
RUN python -m venv /opt/venv && . /opt/venv/bin/activate && pip install -r requirements.txt

# Copier le reste de l'application
COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "baol_distributions.wsgi:application"]
