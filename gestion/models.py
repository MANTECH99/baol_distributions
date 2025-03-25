from django.db import models


class Camion(models.Model):
    numero = models.CharField(max_length=20, unique=True)  # Numéro de camion
    telephone = models.CharField(max_length=15, unique=True)  # Numéro du chauffeur

    def __str__(self):
        return f"Camion {self.numero} - {self.telephone}"


class StatutCamion(models.Model):
    camion = models.OneToOneField(Camion, on_delete=models.CASCADE, related_name="statut_camion")

    STATUT_CHOICES = [
        ('attente', 'Attente'),
        ('panne', 'Panne'),
        ('off', 'Off'),
    ]

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='attente')

    def __str__(self):
        return f" {self.get_statut_display()}"


class Livraison(models.Model):
    date = models.DateField()  # Date auto-générée
    camion = models.ForeignKey(Camion, on_delete=models.CASCADE)  # Relation avec Camion
    tonnage = models.DecimalField(max_digits=5, decimal_places=2)  # Tonnage
    prix_unitaire = models.IntegerField(default=0)  # Prix calculé automatiquement
    quantite = models.IntegerField(default=1)  # Quantité, modifiable
    montant = models.IntegerField(default=0)  # Montant = PU × Quantité
    chiffonage = models.CharField(max_length=255, blank=True, null=True)  # Chiffonage
    numero_bl = models.CharField(max_length=50, blank=True, null=True)  # N° BL

    # Ajout du statut
    STATUT_CHOICES = [
        ('enregistré', 'Enregistré'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='enregistré')

    def save(self, *args, **kwargs):
        # Définir le prix unitaire selon le tonnage
        if self.tonnage < 5:
            self.prix_unitaire = 0
        elif self.tonnage < 8:
            self.prix_unitaire = 2500
        elif self.tonnage < 10:
            self.prix_unitaire = 3500
        elif self.tonnage <= 14.5:
            self.prix_unitaire = 5000
        else:
            self.prix_unitaire = 7500

        # Calcul du montant
        self.montant = self.prix_unitaire * self.quantite

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Livraison {self.date} - {self.camion.numero}"
