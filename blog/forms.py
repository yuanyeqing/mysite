from django import forms
from .models import Article

class PostForm(forms.ModelForm):

    class Meta:
        model = Article
        fields = ('title', 'text', 'author', 'category')




