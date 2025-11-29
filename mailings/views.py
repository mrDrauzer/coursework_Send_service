from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.views.generic.base import TemplateView
from django.utils import timezone
from django.db.models import Count, Q, Max

from .models import Recipient, Message, Mailing, Attempt
from .services import is_within_window, run_mailing
from .forms import RecipientForm, MessageForm, MailingForm


class HomeStatsView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        total_mailings = Mailing.objects.count()
        active_mailings = Mailing.objects.filter(start_at__lte=now, end_at__gte=now).exclude(status=Mailing.Status.FINISHED).count()
        unique_recipients = Recipient.objects.values('email').distinct().count()
        ctx.update({
            'total_mailings': total_mailings,
            'active_mailings': active_mailings,
            'unique_recipients': unique_recipients,
        })
        return ctx


class OwnerQuerysetMixin:
    """Ограничение выборки сущностями текущего пользователя.

    Позже здесь можно расширить логику для группы «Менеджеры», чтобы им разрешить просмотр всех записей.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()

        # Менеджерам (или у кого есть соответствующее право) показываем все записи
        model = getattr(self, 'model', None) or qs.model
        if model.__name__ == 'Recipient' and user.has_perm('mailings.view_all_recipients'):
            return qs
        if model.__name__ == 'Message' and user.has_perm('mailings.view_all_messages'):
            return qs
        if model.__name__ == 'Mailing' and user.has_perm('mailings.view_all_mailings'):
            return qs

        # Обычным пользователям — только свои
        return qs.filter(owner=user)

    def form_valid(self, form):
        # Проставляем владельца при создании
        if not form.instance.pk and hasattr(form.instance, 'owner'):
            form.instance.owner = self.request.user
        return super().form_valid(form)


# --------- Recipient ---------
class RecipientListView(LoginRequiredMixin, OwnerQuerysetMixin, ListView):
    model = Recipient
    template_name = 'mailings/recipient_list.html'
    context_object_name = 'items'
    paginate_by = 20


class RecipientDetailView(LoginRequiredMixin, OwnerQuerysetMixin, DetailView):
    model = Recipient
    template_name = 'mailings/recipient_detail.html'


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = 'mailings/recipient_form.html'
    success_url = reverse_lazy('mailings:recipient_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, OwnerQuerysetMixin, UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = 'mailings/recipient_form.html'
    success_url = reverse_lazy('mailings:recipient_list')


class RecipientDeleteView(LoginRequiredMixin, OwnerQuerysetMixin, DeleteView):
    model = Recipient
    template_name = 'mailings/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailings:recipient_list')


# --------- Message ---------
class MessageListView(LoginRequiredMixin, OwnerQuerysetMixin, ListView):
    model = Message
    template_name = 'mailings/message_list.html'
    context_object_name = 'items'
    paginate_by = 20


class MessageDetailView(LoginRequiredMixin, OwnerQuerysetMixin, DetailView):
    model = Message
    template_name = 'mailings/message_detail.html'


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerQuerysetMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')


class MessageDeleteView(LoginRequiredMixin, OwnerQuerysetMixin, DeleteView):
    model = Message
    template_name = 'mailings/message_confirm_delete.html'
    success_url = reverse_lazy('mailings:message_list')


# --------- Mailing ---------
class MailingListView(LoginRequiredMixin, OwnerQuerysetMixin, ListView):
    model = Mailing
    template_name = 'mailings/mailing_list.html'
    context_object_name = 'items'
    paginate_by = 20


class MailingDetailView(LoginRequiredMixin, OwnerQuerysetMixin, DetailView):
    model = Mailing
    template_name = 'mailings/mailing_detail.html'


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerQuerysetMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class MailingDeleteView(LoginRequiredMixin, OwnerQuerysetMixin, DeleteView):
    model = Mailing
    template_name = 'mailings/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')


class MailingRunView(LoginRequiredMixin, DetailView):
    model = Mailing

    def post(self, request, *args, **kwargs):
        mailing: Mailing = self.get_object()
        user = request.user
        # Проверка доступа: владелец либо менеджер с правом на просмотр всех рассылок
        if mailing.owner_id != user.id and not user.has_perm('mailings.view_all_mailings'):
            messages.error(request, 'Недостаточно прав для запуска этой рассылки.')
            return HttpResponseRedirect(mailing.get_absolute_url() if hasattr(mailing, 'get_absolute_url') else reverse_lazy('mailings:mailing_detail', kwargs={'pk': mailing.pk}))

        # Запрещаем повторный запуск завершённой рассылки
        if mailing.status == Mailing.Status.FINISHED:
            messages.info(request, 'Эта рассылка уже завершена и не может быть запущена повторно.')
            return HttpResponseRedirect(reverse_lazy('mailings:mailing_detail', kwargs={'pk': mailing.pk}))

        # Проверим окно отправки
        if not is_within_window(mailing):
            messages.error(request, 'Сейчас не входит в окно отправки рассылки (start/end).')
            return HttpResponseRedirect(reverse_lazy('mailings:mailing_detail', kwargs={'pk': mailing.pk}))

        # Помечаем как запущенную и выполняем отправку
        mailing.status = Mailing.Status.RUNNING
        mailing.save(update_fields=['status'])
        ok, err = run_mailing(mailing)
        if err == 0:
            messages.success(request, f'Рассылка отправлена: успешно {ok}, ошибок {err}.')
        else:
            messages.warning(request, f'Рассылка завершена с ошибками: успешно {ok}, ошибок {err}. Подробности в попытках.')

        return HttpResponseRedirect(reverse_lazy('mailings:mailing_detail', kwargs={'pk': mailing.pk}))


# --------- Reports (Attempts) ---------
class MailingReportListView(LoginRequiredMixin, OwnerQuerysetMixin, ListView):
    """Список рассылок с агрегированной статистикой попыток."""

    model = Mailing
    template_name = 'mailings/report_mailing_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        qs = super().get_queryset()
        return (
            qs
            .annotate(
                attempts_total=Count('attempts'),
                attempts_success=Count('attempts', filter=Q(attempts__status=Attempt.AttemptStatus.SUCCESS)),
                attempts_fail=Count('attempts', filter=Q(attempts__status=Attempt.AttemptStatus.FAIL)),
                last_attempt=Max('attempts__when'),
            )
            .select_related('message')
            .prefetch_related('recipients')
        )


class MailingReportDetailView(LoginRequiredMixin, ListView):
    """Детальная страница: попытки конкретной рассылки."""

    model = Attempt
    template_name = 'mailings/report_mailing_detail.html'
    context_object_name = 'attempts'
    paginate_by = 20

    def get_queryset(self):
        mailing_id = self.kwargs['pk']
        user = self.request.user
        qs = Attempt.objects.filter(mailing_id=mailing_id).order_by('-when')
        if user.has_perm('mailings.view_all_mailings'):
            return qs
        # Доступ только к своим рассылкам
        if not Mailing.objects.filter(pk=mailing_id, owner=user).exists():
            return Attempt.objects.none()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mailing = Mailing.objects.filter(pk=self.kwargs['pk']).select_related('message').first()
        ctx['mailing'] = mailing
        return ctx
