import pytest
from django.urls import reverse
from django.core import mail
from django.utils import timezone

from mailings.models import Attempt, Mailing


@pytest.mark.django_db
def test_run_view_success_in_window(client, user, recipient_factory, message_factory, mailing_factory):
    r1 = recipient_factory(owner=user, email_prefix="r", idx=1)
    r2 = recipient_factory(owner=user, email_prefix="r", idx=2)
    msg = message_factory(owner=user)
    mailing = mailing_factory(owner=user, message=msg, recipients=[r1, r2], start_delta=-1, end_delta=1)

    client.login(username=user.email, password="pass12345")
    url = reverse('mailings:mailing_run', kwargs={'pk': mailing.pk})
    resp = client.post(url)

    assert resp.status_code in (302, 301)
    mailing.refresh_from_db()
    assert mailing.status == Mailing.Status.FINISHED
    assert Attempt.objects.filter(mailing=mailing).count() == 1
    # Проверяем, что отправлено 2 письма
    assert len(mail.outbox) == 2


@pytest.mark.django_db
def test_run_view_outside_window_blocked(client, user, recipient_factory, message_factory, mailing_factory):
    r = recipient_factory(owner=user, email_prefix="r", idx=1)
    msg = message_factory(owner=user)
    # Окно в будущем
    mailing = mailing_factory(owner=user, message=msg, recipients=[r], start_delta=1, end_delta=2)

    client.login(username=user.email, password="pass12345")
    url = reverse('mailings:mailing_run', kwargs={'pk': mailing.pk})
    resp = client.post(url, follow=True)

    mailing.refresh_from_db()
    assert mailing.status == Mailing.Status.CREATED
    assert Attempt.objects.filter(mailing=mailing).count() == 0
    # Почта не отправлялась
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_run_view_finished_cannot_rerun(client, user, recipient_factory, message_factory, mailing_factory):
    r = recipient_factory(owner=user, email_prefix="r", idx=1)
    msg = message_factory(owner=user)
    mailing = mailing_factory(owner=user, message=msg, recipients=[r], start_delta=-2, end_delta=2,
                              status=Mailing.Status.FINISHED)

    client.login(username=user.email, password="pass12345")
    url = reverse('mailings:mailing_run', kwargs={'pk': mailing.pk})
    resp = client.post(url)
    assert resp.status_code in (302, 301)
    # Не создаётся новых попыток
    assert Attempt.objects.filter(mailing=mailing).count() == 0


@pytest.mark.django_db
def test_run_view_access_denied_for_non_owner_without_perm(client, other_user, user, recipient_factory, message_factory, mailing_factory):
    r = recipient_factory(owner=user, email_prefix="r", idx=1)
    msg = message_factory(owner=user)
    mailing = mailing_factory(owner=user, message=msg, recipients=[r], start_delta=-1, end_delta=1)

    client.login(username=other_user.email, password="pass12345")
    url = reverse('mailings:mailing_run', kwargs={'pk': mailing.pk})
    resp = client.post(url)
    # Должен произойти редирект без выполнения
    assert resp.status_code in (302, 301)
    mailing.refresh_from_db()
    assert mailing.status == Mailing.Status.CREATED
    assert Attempt.objects.filter(mailing=mailing).count() == 0
