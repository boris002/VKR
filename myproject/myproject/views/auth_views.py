from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.views import LogoutView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import FormView
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
# Вход
class CustomLoginView(LoginView):
    template_name = 'login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('main')

# Регистрация
class RegisterView(FormView):
    template_name = 'register.html'
    form_class = CustomUserCreationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('main')

    def form_valid(self, form):
        user = form.save()  # Сохраняем пользователя
        group = Group.objects.get(name='auth+')  # Получаем группу "auth+"
        user.groups.add(group)  # Добавляем пользователя в группу "auth+"
        user.save()  # Сохраняем изменения пользователя
        
        if user is not None:
            login(self.request, user)
        return super(RegisterView, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('main')
        return super(RegisterView, self).get(*args, **kwargs)

# Выход
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('main')

    def get(self, request, *args, **kwargs):
        """Logout may be done via GET."""
        return self.post(request, *args, **kwargs)

def profile_view(request):
    if request.method == 'POST':
        # Здесь логика обновления информации пользователя
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        messages.success(request, 'Профиль успешно обновлен.')
        return redirect('profile')  # Укажите здесь имя URL-адреса вашего профиля

    return render(request, 'profile.html', {'user': request.user})