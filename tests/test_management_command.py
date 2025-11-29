import io
import pytest
from django.core.management import call_command
from django.core import mail

from mailings.models import Mailing, Attempt


@pytest.mark.django_db
def test_mailings_send_processes_only_in_window(user, recipient_factory, message_factory, mailing_factory):
    r = recipient_factory(owner=user, email_prefix="r", idx=1)
    msg = message_factory(owner=user)
    in_window = mailing_factory(owner=user, message=msg, recipients=[r], start_delta=-1, end_delta=1)
    future = mailing_factory(owner=user, message=msg, recipients=[r], start_delta=2, end_delta=3)

    out = io.StringIO()
    call_command('mailings_send', stdout=out)

    in_window.refresh_from_db()
    future.refresh_from_db()
    assert in_window.status == Mailing.Status.FINISHED
    assert future.status == Mailing.Status.CREATED
    assert Attempt.objects.filter(mailing=in_window).count() == 1
    assert Attempt.objects.filter(mailing=future).count() == 0
    # одно письмо отправлено
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_mailings_send_skip_finished_with_id(user, recipient_factory, message_factory, mailing_factory):
    r = recipient_factory(owner=user, email_prefix="r", idx=1)
    msg = message_factory(owner=user)
    finished = mailing_factory(owner=user, message=msg, recipients=[r], start_delta=-1, end_delta=1,
                               status=Mailing.Status.FINISHED)

    out = io.StringIO()
    call_command('mailings_send', id=finished.id, stdout=out)

    # Никаких новых Attempt не создаётся
    assert Attempt.objects.filter(mailing=finished).count() == 0
    # В выводе присутствует уведомление о пропуске
    assert "already FINISHED" in out.getvalue()
