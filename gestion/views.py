def liste_livraisons(request):
    # Récupérer les paramètres de filtre
    filter_type = request.GET.get('filter_type')
    selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    selected_month = request.GET.get('month', date.today().strftime('%Y-%m'))
    selected_camion_id = request.GET.get('camion')

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
    }

    return render(request, 'gestion/livraisons.html', context)


def modifier_statut_camion(request, camion_id):
    camion = get_object_or_404(Camion, id=camion_id)
    date_str = request.GET.get('date')

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        date = date.today()

    # Récupère le statut existant ou None
    statut_camion = StatutCamion.objects.filter(camion=camion, date=date).first()

    if request.method == "POST":
        statut = request.POST.get("statut")
        # Crée ou met à jour le statut
        if statut_camion:
            statut_camion.statut = statut
            statut_camion.save()
        else:
            StatutCamion.objects.create(
                camion=camion,
                date=date,
                statut=statut
            )
        return redirect("liste_livraisons")

    return render(request, "gestion/modifier_statut_camion.html", {
        "camion": camion,
        "date": date,
        "statut_camion": statut_camion  # Peut être None
    })
