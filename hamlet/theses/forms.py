from dal import autocomplete

from django import forms

from .models import Thesis, Person


class AuthorAutocompleteForm(forms.ModelForm):
    author = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='theses:autocomplete_author',
            attrs={'class': 'field field-text form-input'}),
        label='By author'
    )

    class Meta:
        model = Person
        fields = ()


class TitleAutocompleteForm(forms.ModelForm):
    title = forms.ModelChoiceField(
        queryset=Thesis.objects.filter(unextractable=False),
        widget=autocomplete.ModelSelect2(url='theses:autocomplete_thesis'),
        label='By title'
    )

    class Meta:
        model = Thesis
        fields = ('title',)
