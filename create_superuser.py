import os
import django

# Initialiser Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baol_distributions.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "password")
    print("Superutilisateur créé avec succès !")
else:
    print("Superutilisateur déjà existant.")
