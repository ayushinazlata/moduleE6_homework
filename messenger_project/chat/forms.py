from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile, Chat


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'avatar']

    def save(self, commit=True):
        user = super().save(commit)
        profile = UserProfile.objects.get_or_create(user=user)
        avatar = self.cleaned_data.get('avatar')

        if avatar:
            profile.avatar = avatar
        profile.save()
        
        return user


class ProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150)

    class Meta:
        model = UserProfile
        fields = ['username', 'avatar'] 

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['username'].initial = user.username  


class ChatForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),  # Получаем всех пользователей
        widget=forms.CheckboxSelectMultiple, 
        required=False
    )

    class Meta:
        model = Chat
        fields = ['name', 'participants']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }