import logging

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from openpyxl.workbook import Workbook
from django.http import HttpResponse
from .models import Livraison, Camion, StatutCamion
from .forms import LivraisonForm
from django.db.models import Sum, Min
from django.utils.timezone import now
import json
from datetime import datetime, date
from django.views.decorators.clickjacking import xframe_options_exempt
@xframe_options_exempt
def ajouter_livraison(request):
    # Récupérer les paramètres depuis l'URL
    date_param = request.GET.get('date')
    camion_id = request.GET.get('camion')

    # Convertir la date en objet datetime
    try:
        selected_date = datetime.strptime(date_param, "%Y-%m-%d").date() if date_param else None
    except ValueError:
        selected_date = None

    # Récupérer le camion correspondant
    camion = None
    if camion_id:
        try:
            camion = get_object_or_404(Camion, id=camion_id)
        except Exception as e:
            return HttpResponse(f"Erreur : {str(e)}", status=400)

    if request.method == "POST":
        form = LivraisonForm(request.POST)
        if form.is_valid():
            livraison = form.save(commit=False)
            livraison.date = selected_date  # Pré-remplit la date
            livraison.camion = camion       # Pré-remplit le camion
            livraison.save()

            # Rediriger vers la liste des livraisons dans la fenêtre parente
            return HttpResponse(f"""
                <script>
                    window.top.location.href = "{reverse('liste_livraisons')}";
                </script>
            """)
        else:
            # Si le formulaire n'est pas valide, réafficher le formulaire avec les erreurs
            return render(request, 'gestion/ajouter_livraison.html', {
                'form': form,
                'camion': camion,
                'selected_date': selected_date
            })
    else:
        # Si la méthode est GET, afficher le formulaire vide
        form = LivraisonForm()
        return render(request, 'gestion/ajouter_livraison.html', {
            'form': form,
            'camion': camion,
            'selected_date': selected_date
        })


def liste_livraisons(request):
    # Récupérer le type de filtre (date ou mois)
    filter_type = request.GET.get('filter_type')
    # Définir des valeurs par défaut pour selected_date et selected_month
    selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))  # Date par défaut : aujourd'hui
    selected_month = request.GET.get('month', date.today().strftime('%Y-%m'))  # Mois par défaut : ce mois


    if filter_type == 'date':
        # Filtrer par date personnalisée
        selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        livraisons = Livraison.objects.filter(date=selected_date_obj).order_by('-date')
        selected_month = None
    elif filter_type == 'month':
        # Filtrer par mois spécifique
        selected_month = request.GET.get('month', date.today().strftime('%Y-%m'))
        year, month = map(int, selected_month.split('-'))
        livraisons = Livraison.objects.filter(date__year=year, date__month=month).order_by('-date')
        selected_date = None
        # Pour les camions sans livraison, on utilise le premier jour du mois sélectionné
        selected_date_obj = date(year, month, 1)
    else:
        # Par défaut, afficher les livraisons du jour
        selected_date = date.today().strftime('%Y-%m-%d')
        selected_date_obj = date.today()
        livraisons = Livraison.objects.filter(date=selected_date_obj).order_by('-date')
        selected_month = None

    # Récupérer tous les camions
    camions = Camion.objects.all()

    # Associer chaque camion à toutes ses livraisons du jour ou du mois
    livraisons_par_camion = {}
    for livraison in livraisons:
        if livraison.camion.id not in livraisons_par_camion:
            livraisons_par_camion[livraison.camion.id] = []
        livraisons_par_camion[livraison.camion.id].append(livraison)

    # Récupérer les statuts des camions sans livraison
    statuts_camions = {statut.camion.id: statut for statut in StatutCamion.objects.all()}

    context = {
        'livraisons': livraisons,
        'camions': camions,
        'livraisons_par_camion': livraisons_par_camion,
        'statuts_camions': statuts_camions,
        'selected_date': selected_date,
        'selected_month': selected_month,
        'selected_date_obj': selected_date_obj,  # Toujours inclure selected_date_obj
        'filter_type': filter_type,  # Passer le type de filtre au template
    }

    return render(request, 'gestion/livraisons.html', context)

def modifier_statut_camion(request, camion_id):
    camion = get_object_or_404(Camion, id=camion_id)

    if request.method == "POST":
        statut = request.POST.get("statut")
        statut_camion, created = StatutCamion.objects.get_or_create(camion=camion)
        statut_camion.statut = statut
        statut_camion.save()
        return redirect("liste_livraisons")

    return render(request, "gestion/modifier_statut_camion.html", {"camion": camion})




from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string

def modifier_livraison(request, livraison_id):
    livraison = get_object_or_404(Livraison, id=livraison_id)

    if request.method == 'POST':
        form = LivraisonForm(request.POST, instance=livraison)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})  # ✅ Succès, pas besoin de recharger le formulaire

        # Si le formulaire contient des erreurs, on renvoie le HTML mis à jour
        html = render_to_string('gestion/partials/form_modif_livraison.html', {'form': form, 'livraison': livraison},
                                request=request)
        return JsonResponse({'success': False, 'html': html})  # ❌ Erreur, recharge le formulaire

    # Si GET, on affiche le formulaire dans le modal
    form = LivraisonForm(instance=livraison)
    html = render_to_string('gestion/partials/form_modif_livraison.html', {'form': form, 'livraison': livraison},
                            request=request)
    return JsonResponse({'html': html})


from django.shortcuts import get_object_or_404

def supprimer_livraison(request, livraison_id):
    livraison = get_object_or_404(Livraison, id=livraison_id)
    livraison.delete()
    return redirect('liste_livraisons')







def dashboard(request):
    # Récupérer le type de filtre (date, mois ou année)
    filter_type = request.GET.get('filter_type')

    # Récupérer les valeurs des filtres avec une valeur par défaut
    selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    selected_month = request.GET.get('month', date.today().strftime('%Y-%m'))
    selected_year = request.GET.get('year', str(date.today().year))

    # Initialisation des variables
    livraisons = Livraison.objects.all()
    selected_date_obj = date.today()

    # Filtrage selon le type sélectionné
    if filter_type == 'date':
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            selected_date_obj = date.today()
        livraisons = livraisons.filter(date=selected_date_obj)
        selected_month = None
        selected_year = None

    elif filter_type == 'month':
        try:
            year, month = map(int, selected_month.split('-'))
            selected_date_obj = date(year, month, 1)
        except ValueError:
            selected_date_obj = date.today()
        livraisons = livraisons.filter(date__year=year, date__month=month)
        selected_date = None
        selected_year = None

    elif filter_type == 'year':
        try:
            year = int(selected_year)
        except ValueError:
            year = date.today().year
        livraisons = livraisons.filter(date__year=year)
        selected_date = None
        selected_month = None

    else:
        livraisons = livraisons.filter(date=selected_date_obj)
        selected_month = None
        selected_year = None

    # Calculer les statistiques globales
    stats = livraisons.aggregate(
        total_tonnage=Sum('tonnage'),
        total_montant=Sum('montant')
    )

    total_tonnage = stats['total_tonnage'] or 0
    total_montant = stats['total_montant'] or 0
    total_livraisons = livraisons.count()

    # 🔥 Mise à jour des données des graphiques en fonction du filtre
    mois_labels, tonnage_values, montant_values = [], [], []

    if filter_type == 'year':
        # Si filtré par année, récupérer les stats des 12 mois de cette année
        for mois in range(1, 13):
            livraisons_mois = Livraison.objects.filter(date__year=year, date__month=mois)
            stats_mois = livraisons_mois.aggregate(
                tonnage_mois=Sum('tonnage'),
                montant_mois=Sum('montant')
            )
            mois_labels.append(f"{mois}/{year}")
            tonnage_values.append(float(stats_mois['tonnage_mois'] or 0))
            montant_values.append(float(stats_mois['montant_mois'] or 0))

    elif filter_type == 'month':
        # Si filtré par mois, récupérer les stats des jours de ce mois
        from calendar import monthrange
        nb_jours = monthrange(year, month)[1]
        for jour in range(1, nb_jours + 1):
            livraisons_jour = Livraison.objects.filter(date__year=year, date__month=month, date__day=jour)
            stats_jour = livraisons_jour.aggregate(
                tonnage_jour=Sum('tonnage'),
                montant_jour=Sum('montant')
            )
            mois_labels.append(f"{jour}/{month}")
            tonnage_values.append(float(stats_jour['tonnage_jour'] or 0))
            montant_values.append(float(stats_jour['montant_jour'] or 0))

    else:
        # Par défaut (ou si filtré par date), récupérer les 6 derniers mois
        mois_actuel = now().month
        annee_actuelle = now().year

        for i in range(6):  # Derniers 6 mois
            mois = (mois_actuel - i) % 12 or 12
            annee = annee_actuelle if mois_actuel - i > 0 else annee_actuelle - 1
            mois_labels.append(f"{mois}/{annee}")

            livraisons_mois = Livraison.objects.filter(date__year=annee, date__month=mois)
            stats_mois = livraisons_mois.aggregate(
                tonnage_mois=Sum('tonnage'),
                montant_mois=Sum('montant')
            )
            tonnage_values.append(float(stats_mois['tonnage_mois'] or 0))
            montant_values.append(float(stats_mois['montant_mois'] or 0))

    # Récupérer les 50 dernières livraisons
    livraisons_mois = livraisons.order_by('-date')[:50].values(
        'date', 'camion__numero', 'camion_id', 'camion__telephone', 'tonnage',
        'prix_unitaire', 'quantite', 'montant', 'chiffonage', 'numero_bl', 'statut'
    )

    # Générer les 5 dernières années dynamiquement
    current_year = date.today().year
    last_five_years = [current_year - i for i in range(5)]

    # Passer les données au template
    context = {
        'selected_date': selected_date,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_date_obj': selected_date_obj,
        'filter_type': filter_type,
        'total_tonnage': total_tonnage,
        'total_montant': total_montant,
        'total_livraisons': total_livraisons,
        'mois_labels': json.dumps(mois_labels),  # Inverser pour avoir les plus récents à droite
        'tonnage_values': json.dumps(tonnage_values[::-1]),
        'montant_values': json.dumps(montant_values[::-1]),
        'livraisons_mois': livraisons_mois,
        'last_five_years': last_five_years,
    }

    return render(request, 'gestion/dashboard.html', context)




logger = logging.getLogger(__name__)

def exporter_livraisons_excel(request):
    # Récupérer les paramètres de filtre
    filter_type = request.GET.get('filter_type')
    selected_date = request.GET.get('date')
    selected_month = request.GET.get('month')

    logger.info(f"Filter type: {filter_type}, Date: {selected_date}, Month: {selected_month}")

    # Filtrer les livraisons en fonction du filtre sélectionné
    if filter_type == 'date' and selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            livraisons = Livraison.objects.filter(date=selected_date_obj).order_by('-date')
            logger.info(f"Livraisons filtrées par date ({selected_date_obj}): {livraisons.count()}")
        except ValueError:
            logger.error("Format de date invalide")
            livraisons = Livraison.objects.none()
    elif filter_type == 'month' and selected_month:
        try:
            year, month = map(int, selected_month.split('-'))
            livraisons = Livraison.objects.filter(date__year=year, date__month=month).order_by('-date')
            logger.info(f"Livraisons filtrées par mois ({year}-{month}): {livraisons.count()}")
        except ValueError:
            logger.error("Format de mois invalide")
            livraisons = Livraison.objects.none()
    else:
        # Par défaut, exporter toutes les livraisons
        livraisons = Livraison.objects.all().order_by('-date')
        logger.info(f"Toutes les livraisons: {livraisons.count()}")

    # Créer un nouveau classeur Excel
    wb = Workbook()
    ws = wb.active

    # Ajouter les en-têtes de colonnes
    headers = [
        "Date", "Camion", "Numéro Téléphone", "Tonnage", "Prix Unitaire",
        "Quantité", "Montant", "Chiffonage", "N° BL", "Statut"
    ]
    ws.append(headers)

    # Ajouter les données des livraisons
    for livraison in livraisons:
        ws.append([
            livraison.date.strftime("%Y-%m-%d"),
            livraison.camion.numero,
            livraison.camion.telephone,
            livraison.tonnage,
            livraison.prix_unitaire,
            livraison.quantite,
            livraison.montant,
            livraison.chiffonage,
            livraison.numero_bl,
            livraison.get_statut_display(),
        ])

    # Créer une réponse HTTP avec le fichier Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=livraisons.xlsx'
    wb.save(response)

    return response

# Vue pour l'inscription
def register(request):
    error = None
    if request.method == "POST":
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            error = "Les mots de passe ne correspondent pas."
        elif User.objects.filter(username=username).exists():
            error = "Ce nom d'utilisateur existe déjà."
        else:
            user = User.objects.create_user(username=username, password=password1)
            login(request, user)
            return redirect("login")  # Redirige vers le tableau de bord

    return render(request, "registration/login_register.html", {"register_error": error})

# Vue pour la connexion
def user_login(request):
    error = None
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")  # Redirige vers le tableau de bord
        else:
            error = "Identifiant ou mot de passe incorrect."

    return render(request, "registration/login_register.html", {"login_error": error})