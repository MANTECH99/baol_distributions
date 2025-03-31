from django.contrib.auth.views import LoginView
from django.urls import path

from . import views
from .views import liste_livraisons, exporter_livraisons_excel, register, user_login, liste_rapports, \
    telecharger_rapport, ajouter_rapport, supprimer_rapport
from .views import ajouter_livraison
from .views import modifier_livraison, supprimer_livraison
from .views import dashboard
from .views import modifier_statut_camion  # Assure-toi que la vue est bien importée

urlpatterns = [
path('ajouter/', ajouter_livraison, name='ajouter_livraison'),
    path('livraisons/', liste_livraisons, name='liste_livraisons'),
    path('modifier/<int:livraison_id>/', modifier_livraison, name='modifier_livraison'),
    path('supprimer/<int:livraison_id>/', supprimer_livraison, name='supprimer_livraison'),
    path('dashboard/', dashboard, name='dashboard'),
    path('modifier-statut-camion/<int:camion_id>/', modifier_statut_camion, name='modifier_statut_camion'),
    # Autres URLs
    path('exporter-livraisons-excel/', exporter_livraisons_excel, name='exporter_livraisons_excel'),
    path('login/', user_login, name='login'),
    path('register/', register, name='register'),
        path('rapports/', liste_rapports, name='liste_rapports'),
    path('rapports/telecharger/<int:rapport_id>/', telecharger_rapport, name='telecharger_rapport'),
    path('rapports/ajouter/', ajouter_rapport, name='ajouter_rapport'),
    path('supprimer_rapport/<int:rapport_id>/', supprimer_rapport, name='supprimer_rapport'),


]
