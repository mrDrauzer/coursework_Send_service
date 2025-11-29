from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView

from .forms import RegisterForm, ProfileForm


User = get_user_model()


class RegisterView(FormView):
    template_name = 'users/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save()
        # Отправляем письмо активации (в консоль при текущих настройках)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activate_url = self.request.build_absolute_uri(
            reverse('users:activate', kwargs={'uidb64': uid, 'token': token})
        )
        subject = 'Подтверждение регистрации'
        message = (
            f"Здравствуйте!\n\n"
            f"Для завершения регистрации перейдите по ссылке:\n{activate_url}\n\n"
            f"Если вы не регистрировались, проигнорируйте это письмо."
        )
        user.email_user(subject, message)

        messages.success(self.request, 'Мы отправили письмо с подтверждением на ваш email.')
        return super().form_valid(form)


class ActivateView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=['is_active'])
            login(request, user)
            messages.success(request, 'Email подтверждён, вы вошли в систему.')
            return redirect('users:profile')

        messages.error(request, 'Ссылка подтверждения недействительна или устарела.')
        return redirect('users:login')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'users/profile_form.html'
    form_class = ProfileForm
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user
