"""Script pour créer le superutilisateur admin initial."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plagiat_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@plagiatdetect.local',
        password='admin123',
        first_name='Admin',
        last_name='Système',
        role='admin',
    )
    print("Superutilisateur 'admin' créé avec succès.")
else:
    print("Le superutilisateur 'admin' existe déjà.")
