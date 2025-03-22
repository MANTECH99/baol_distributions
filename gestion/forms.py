from django import forms
from .models import Livraison

class LivraisonForm(forms.ModelForm):
    class Meta:
        model = Livraison
        fields = ['tonnage', 'quantite', 'chiffonage', 'numero_bl', 'statut']

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
