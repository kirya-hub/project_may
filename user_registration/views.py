from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from user_profile.models import Profile

from .forms import RegisterForm
from .models import EmailConfirmationToken


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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mode'] = 'register'
        return ctx

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.name = form.cleaned_data.get('name', '') or user.username
        profile.save()

        token = EmailConfirmationToken.objects.create(user=user)
        confirm_url = self.request.build_absolute_uri(
            reverse('confirm_email', args=[token.token])
        )

        html_message = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#141418;font-family:sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#141418;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0" style="background:#1c1c26;border-radius:16px;padding:32px;border:1px solid rgba(255,255,255,0.06);">
          <tr>
            <td style="color:#fff;font-size:22px;font-weight:800;padding-bottom:12px;">
              CafeRewards
            </td>
          </tr>
          <tr>
            <td style="color:rgba(255,255,255,0.7);font-size:15px;padding-bottom:24px;line-height:1.6;">
              Вы почти у цели! Подтвердите ваш email, чтобы начать пользоваться CafeRewards.
            </td>
          </tr>
          <tr>
            <td style="padding-bottom:24px;">
              <a href="{confirm_url}" style="display:inline-block;padding:14px 28px;border-radius:12px;background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;font-weight:800;font-size:15px;text-decoration:none;">
                Подтвердить email
              </a>
            </td>
          </tr>
          <tr>
            <td style="color:rgba(255,255,255,0.4);font-size:13px;">
              Ссылка действительна 24 часа. Если вы не регистрировались — просто проигнорируйте это письмо.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        send_mail(
            subject='CafeRewards — Подтвердите email',
            message=f'Перейдите по ссылке для подтверждения аккаунта: {confirm_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )

        return redirect(reverse('email_sent'))

    def form_invalid(self, form):
        ctx = self.get_context_data(form=form)
        return self.render_to_response(ctx)


class ConfirmEmailView(View):
    def get(self, request, token):
        try:
            confirmation = EmailConfirmationToken.objects.get(token=token)
        except EmailConfirmationToken.DoesNotExist:
            return render(request, 'user_registration/confirm_email.html', {'error': True})

        if confirmation.is_expired():
            confirmation.delete()
            return render(request, 'user_registration/confirm_email.html', {'error': True})

        user = confirmation.user
        user.is_active = True
        user.save()
        confirmation.delete()

        login(request, user)
        messages.success(request, 'Email подтверждён. Добро пожаловать!')
        return redirect('my_profile')


class EmailSentView(TemplateView):
    template_name = 'user_registration/email_sent.html'


class AuthLogoutView(LogoutView):
    next_page = reverse_lazy('login')
