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
from datetime import datetime, date, timedelta
from django.views.decorators.clickjacking import xframe_options_exempt
@xframe_options_exempt
def ajouter_livraison(request):
    # Récupérer les paramètres depuis l'URL
    date_param = request.GET.get('date')
    camion_id = request.GET.get('camion')

    try:
        selected_date = datetime.strptime(date_param, "%Y-%m-%d").date() if date_param else None
    except ValueError:
        selected_date = None

    camion = get_object_or_404(Camion, id=camion_id) if camion_id else None

    if request.method == "POST":
        form = LivraisonForm(request.POST)
        if form.is_valid():
            livraison = form.save(commit=False)
            livraison.date = selected_date
            livraison.camion = camion
            livraison.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Livraison enregistrée avec succès',
                    'livraison': {
                        'id': livraison.id,
                        'date': livraison.date.strftime('%Y-%m-%d'),
                        'date_display': livraison.date.strftime('%d %B %Y'),
                        'camion_id': camion.id,
                        'camion_numero': camion.numero,
                        'tonnage': str(livraison.tonnage),
                        'prix_unitaire': str(livraison.prix_unitaire),
                        'quantite': livraison.quantite,
                        'montant': str(livraison.montant),
                        'chiffonage': livraison.chiffonage,
                        'numero_bl': livraison.numero_bl,
                        'statut': livraison.get_statut_display(),
                    }
                })
            else:
                return HttpResponse(f"""
                    <script>
                        window.top.location.reload(true);
                    </script>
                """)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {f: [str(e) for e in form.errors[f]] for f in form.errors}
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
            else:
                return render(request, 'gestion/ajouter_livraison.html', {
                    'form': form,
                    'camion': camion,
                    'selected_date': selected_date
                })

    # GET request - afficher le formulaire
    form = LivraisonForm()
    return render(request, 'gestion/ajouter_livraison.html', {
        'form': form,
        'camion': camion,
        'selected_date': selected_date
    })

from django.shortcuts import render
from datetime import date, datetime
from .models import Livraison, Camion, StatutCamion

def liste_livraisons(request):
    # Récupérer les paramètres de filtre
    filter_type = request.GET.get('filter_type')
    selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    selected_month = request.GET.get('month', date.today().strftime('%Y-%m'))
    selected_camion_id = request.GET.get('camion')
    tonnage_filter = request.GET.get('tonnage_filter')  # Nouveau paramètre

    # Initialiser les variables
    selected_date_obj = None
    date_range = []
    livraisons = Livraison.objects.all()

    # Appliquer le filtre par date ou mois
    if filter_type == 'date':
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            livraisons = livraisons.filter(date=selected_date_obj)
            date_range = [selected_date_obj]
        except ValueError:
            selected_date_obj = date.today()
            livraisons = livraisons.filter(date=selected_date_obj)
            date_range = [selected_date_obj]
        selected_month = None
    elif filter_type == 'month':
        try:
            year, month = map(int, selected_month.split('-'))
            selected_date_obj = date(year, month, 1)
            last_day = (selected_date_obj.replace(month=month % 12 + 1, day=1) - timedelta(days=1)).day
            date_range = [date(year, month, day) for day in range(1, last_day + 1)]
            livraisons = livraisons.filter(date__year=year, date__month=month)
        except ValueError:
            selected_date_obj = date.today()
            livraisons = livraisons.filter(date=selected_date_obj)
            date_range = [selected_date_obj]
        selected_date = None
    else:
        selected_date = date.today().strftime('%Y-%m-%d')
        selected_date_obj = date.today()
        livraisons = livraisons.filter(date=selected_date_obj)
        date_range = [selected_date_obj]
        selected_month = None

    # Appliquer le filtre par camion si un camion est sélectionné
    if selected_camion_id and selected_camion_id != "None":
        livraisons = livraisons.filter(camion_id=selected_camion_id)

        # Appliquer le filtre par tonnage si sélectionné
    if tonnage_filter == 'lt5':
        livraisons = livraisons.filter(tonnage__lt=5)

    # Trier les livraisons par date
    livraisons = livraisons.order_by('-date')

    # Récupérer tous les camions
    camions = Camion.objects.all()

    # Organiser les livraisons par camion et par date
    livraisons_par_camion_et_date = {}
    for camion in camions:
        livraisons_par_camion_et_date[camion.id] = {}
        for day in date_range:
            livraisons_du_jour = livraisons.filter(camion=camion, date=day)
            if livraisons_du_jour.exists():
                livraisons_par_camion_et_date[camion.id][day] = list(livraisons_du_jour)
            else:
                livraisons_par_camion_et_date[camion.id][day] = None

    # Récupérer les statuts des camions
    statuts_camions = {statut.camion.id: statut for statut in StatutCamion.objects.all()}

    # Récupération des statuts par camion et date
    statuts_par_date = {}
    for camion in camions:
        statuts_par_date[camion.id] = {}
        for day in date_range:
            statut = StatutCamion.objects.filter(camion=camion, date=day).first()
            statuts_par_date[camion.id][day] = statut.get_statut_display() if statut else "En attente"

    # Préparer le contexte pour le template
    context = {
        'statuts_par_date': statuts_par_date,
        'livraisons': livraisons,
        'camions': camions,
        'livraisons_par_camion_et_date': livraisons_par_camion_et_date,
        'statuts_camions': statuts_camions,
        'selected_date': selected_date,
        'selected_month': selected_month,
        'selected_camion_id': selected_camion_id,
        'selected_date_obj': selected_date_obj,
        'filter_type': filter_type,
        'date_range': date_range,
        'tonnage_filter': tonnage_filter,  # Nouvelle variable
    }

    return render(request, 'gestion/livraisons.html', context)


def modifier_statut_camion(request, camion_id):
    camion = get_object_or_404(Camion, id=camion_id)
    date = request.GET.get('date')

    if request.method == "POST":
        statut = request.POST.get("statut")
        statut_camion, created = StatutCamion.objects.get_or_create(
            camion=camion,
            date=date,
            defaults={'statut': statut}
        )
        if not created:
            statut_camion.statut = statut
            statut_camion.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect("liste_livraisons")

    # Passez la date et les choix de statut au template
    STATUT_CHOICES = [
        ("En attente", "En attente"),
        ("En panne", "En panne"),
        ("Travaille pas", "Travaille pas"),
    ]

    context = {
        "camion": camion,
        "date": date,
        "STATUT_CHOICES": STATUT_CHOICES
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, "gestion/partials/statut_camion_form.html", context)
    return render(request, "gestion/modifier_statut_camion.html", context)

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
    # Récupérer tous les paramètres de filtre
    filter_type = request.GET.get('filter_type')
    selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    selected_month = request.GET.get('month', date.today().strftime('%Y-%m'))
    selected_year = request.GET.get('year', str(date.today().year))
    selected_camion_id = request.GET.get('camion')

    # Initialisation
    base_query = Livraison.objects.all()
    selected_date_obj = date.today()
    camions = Camion.objects.all()

    # Appliquer le filtre par camion en premier si sélectionné
    if selected_camion_id and selected_camion_id != "None":
        base_query = base_query.filter(camion_id=selected_camion_id)

    # Filtrage selon le type sélectionné
    if filter_type == 'date':
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            livraisons = base_query.filter(date=selected_date_obj)
        except ValueError:
            selected_date_obj = date.today()
            livraisons = base_query.filter(date=selected_date_obj)
        selected_month = None
        selected_year = None

    elif filter_type == 'month':
        try:
            year, month = map(int, selected_month.split('-'))
            selected_date_obj = date(year, month, 1)
            livraisons = base_query.filter(date__year=year, date__month=month)
        except ValueError:
            selected_date_obj = date.today()
            livraisons = base_query.filter(date=selected_date_obj)
        selected_date = None
        selected_year = None

    elif filter_type == 'year':
        try:
            year = int(selected_year)
            livraisons = base_query.filter(date__year=year)
        except ValueError:
            year = date.today().year
            livraisons = base_query.filter(date__year=year)
        selected_date = None
        selected_month = None

    else:
        # Par défaut: livraisons du jour
        livraisons = base_query.filter(date=selected_date_obj)
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

    # Préparation des données pour les graphiques
    mois_labels, tonnage_values, montant_values = [], [], []

    if filter_type == 'year':
        year = int(selected_year) if selected_year and filter_type == 'year' else date.today().year
        for mois in range(1, 13):
            query = base_query.filter(date__year=year, date__month=mois)
            stats_mois = query.aggregate(
                tonnage_mois=Sum('tonnage'),
                montant_mois=Sum('montant')
            )
            mois_labels.append(f"{mois}/{year}")
            tonnage_values.append(float(stats_mois['tonnage_mois'] or 0))
            montant_values.append(float(stats_mois['montant_mois'] or 0))

    elif filter_type == 'month':
        try:
            year, month = map(int, selected_month.split('-'))
            from calendar import monthrange
            nb_jours = monthrange(year, month)[1]
            for jour in range(1, nb_jours + 1):
                query = base_query.filter(date__year=year, date__month=month, date__day=jour)
                stats_jour = query.aggregate(
                    tonnage_jour=Sum('tonnage'),
                    montant_jour=Sum('montant')
                )
                mois_labels.append(f"{jour}/{month}")
                tonnage_values.append(float(stats_jour['tonnage_jour'] or 0))
                montant_values.append(float(stats_jour['montant_jour'] or 0))
        except ValueError:
            pass

    else:
        # Par défaut: 6 derniers mois
        mois_actuel = date.today().month
        annee_actuelle = date.today().year
        for i in range(6):
            mois = (mois_actuel - i) % 12 or 12
            annee = annee_actuelle if mois_actuel - i > 0 else annee_actuelle - 1
            query = base_query.filter(date__year=annee, date__month=mois)
            stats_mois = query.aggregate(
                tonnage_mois=Sum('tonnage'),
                montant_mois=Sum('montant')
            )
            mois_labels.append(f"{mois}/{annee}")
            tonnage_values.append(float(stats_mois['tonnage_mois'] or 0))
            montant_values.append(float(stats_mois['montant_mois'] or 0))

    # Récupérer les livraisons filtrées
    livraisons_mois = livraisons.order_by('-date')[:50].values(
        'date', 'camion__numero', 'camion_id', 'camion__telephone', 'tonnage',
        'prix_unitaire', 'quantite', 'montant', 'chiffonage', 'numero_bl', 'statut'
    )

    # Contexte
    context = {
        'selected_date': selected_date,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_camion_id': selected_camion_id,
        'selected_date_obj': selected_date_obj,
        'filter_type': filter_type,
        'total_tonnage': total_tonnage,
        'total_montant': total_montant,
        'total_livraisons': total_livraisons,
        'mois_labels': json.dumps(mois_labels[::-1]),
        'tonnage_values': json.dumps(tonnage_values[::-1]),
        'montant_values': json.dumps(montant_values[::-1]),
        'livraisons_mois': livraisons_mois,
        'last_five_years': [date.today().year - i for i in range(5)],
        'camions': camions,
    }

    return render(request, 'gestion/dashboard.html', context)




logger = logging.getLogger(__name__)
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import datetime
from .models import Livraison
import logging

logger = logging.getLogger(__name__)

def exporter_livraisons_excel(request):
    # Récupérer les paramètres de filtre
    filter_type = request.GET.get('filter_type')
    selected_date = request.GET.get('date')
    selected_month = request.GET.get('month')
    selected_camion_id = request.GET.get('camion')  # Récupérer l'ID du camion
    tonnage_filter = request.GET.get('tonnage_filter')  # Nouveau paramètre

    logger.info(f"Filter type: {filter_type}, Date: {selected_date}, Month: {selected_month}, Camion: {selected_camion_id}")

    # Filtrer les livraisons en fonction des filtres sélectionnés
    livraisons = Livraison.objects.all()

    # Appliquer le filtre par camion si un camion est sélectionné
    if selected_camion_id:
        livraisons = livraisons.filter(camion_id=selected_camion_id)
        logger.info(f"Filtrage par camion ({selected_camion_id}): {livraisons.count()} livraisons")

    # Appliquer le filtre par date ou mois
    if filter_type == 'date' and selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            livraisons = livraisons.filter(date=selected_date_obj)
            logger.info(f"Filtrage par date ({selected_date_obj}): {livraisons.count()} livraisons")
        except ValueError:
            logger.error("Format de date invalide")
            livraisons = Livraison.objects.none()
    elif filter_type == 'month' and selected_month:
        try:
            year, month = map(int, selected_month.split('-'))
            livraisons = livraisons.filter(date__year=year, date__month=month)
            logger.info(f"Filtrage par mois ({year}-{month}): {livraisons.count()} livraisons")
        except ValueError:
            logger.error("Format de mois invalide")
            livraisons = Livraison.objects.none()

        # Appliquer le filtre par tonnage si sélectionné
    if tonnage_filter == 'lt5':
        livraisons = livraisons.filter(tonnage__lt=5)
        logger.info(f"Filtrage par tonnage <5: {livraisons.count()} livraisons")

    # Trier les livraisons par date
    livraisons = livraisons.order_by('-date')

    # Créer un nouveau classeur Excel
    wb = Workbook()
    ws = wb.active

    # Ajouter les en-têtes de colonnes
    headers = [
        "Date", "Camion", "Numéro Téléphone", "Tonnage", "Prix Unitaire",
        "Quantité", "Montant", "Chiffonage", "N° BL", "Statut"
    ]
    ws.append(headers)
    # Variables pour calculer les totaux
    total_tonnage = 0
    total_montant = 0

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
        # Ajouter au total tonnage et montant
        total_tonnage += livraison.tonnage
        total_montant += livraison.montant



    # Ajouter une ligne vide avant les totaux
    ws.append([])

    # Ajouter les totaux en bas du tableau
    ws.append(["Total", "", "", total_tonnage, "", "", total_montant, "", "", ""])

    # Créer le nom du fichier en fonction des filtres
    filename_parts = []
    if selected_camion_id:
        filename_parts.append(f"camion_{selected_camion_id}")
    if selected_date:
        filename_parts.append(f"date_{selected_date}")
    elif selected_month:
        filename_parts.append(f"mois_{selected_month}")
    if tonnage_filter == 'lt5':
        filename_parts.append("tonnage_lt5")
    filename = f"livraisons_{'_'.join(filename_parts) or 'all'}.xlsx"


    # Créer une réponse HTTP avec le fichier Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
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
