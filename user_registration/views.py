from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from user_profile.models import Profile

from .forms import RegisterForm


class AuthLoginView(LoginView):
    template_name = 'user_registration/auth.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mode'] = 'login'
        ctx['register_form'] = RegisterForm()
        return ctx


class AuthRegisterView(FormView):
    template_name = 'user_registration/auth.html'
    form_class = RegisterForm
    success_url = reverse_lazy('my_profile')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mode'] = 'register'
        return ctx

    def form_valid(self, form):
        user = form.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.name = form.cleaned_data.get('name', '') or user.username
        profile.save()

        login(self.request, user)
        messages.success(self.request, 'Аккаунт создан. Добро пожаловать!')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        ctx = self.get_context_data(form=form)
        return self.render_to_response(ctx)


class AuthLogoutView(LogoutView):
    next_page = reverse_lazy('login')
