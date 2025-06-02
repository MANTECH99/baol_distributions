from django import forms
from .models import Livraison, Rapport

class LivraisonForm(forms.ModelForm):
    class Meta:
        model = Livraison
        fields = ['tonnage', 'quantite', 'chiffonage', 'numero_bl', 'statut', 'verification']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Désactiver le champ "camion" s'il est présent
        if 'camion' in self.fields:
            self.fields['camion'].widget.attrs['readonly'] = True


    def clean_tonnage(self):
        tonnage = self.cleaned_data.get('tonnage')
        if tonnage < 0:
            raise forms.ValidationError("Le tonnage ne peut pas être négatif.")
        return tonnage

class RapportForm(forms.ModelForm):
    class Meta:
        model = Rapport
        fields = ['mois', 'fichier']
        widgets = {
            'mois': forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
        }

