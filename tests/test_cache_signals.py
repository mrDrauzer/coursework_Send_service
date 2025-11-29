import pytest
from unittest import mock

from django.core.cache import cache

from mailings.models import Recipient, Message, Mailing, Attempt


@pytest.mark.django_db
def test_cache_cleared_on_attempt_save(user, recipient_factory, message_factory, mailing_factory):
    r = recipient_factory(owner=user)
    msg = message_factory(owner=user)
    mailing = mailing_factory(owner=user, message=msg, recipients=[r])

    with mock.patch.object(cache, 'clear') as clear_mock:
        Attempt.objects.create(mailing=mailing, status=Attempt.AttemptStatus.SUCCESS, server_response='ok')
        assert clear_mock.called


@pytest.mark.django_db
def test_cache_cleared_on_mailing_save(user, recipient_factory, message_factory):
    r = recipient_factory(owner=user)
    msg = message_factory(owner=user)
    with mock.patch.object(cache, 'clear') as clear_mock:
        m = Mailing.objects.create(start_at=msg.owner.date_joined, end_at=msg.owner.date_joined, status=Mailing.Status.CREATED, message=msg, owner=user)
        # Обновление вызовет повторную очистку
        m.status = Mailing.Status.RUNNING
        m.save()
        assert clear_mock.called


@pytest.mark.django_db
def test_cache_cleared_on_recipient_save(user):
    with mock.patch.object(cache, 'clear') as clear_mock:
        Recipient.objects.create(email='x@example.com', full_name='X', comment='', owner=user)
        assert clear_mock.called


@pytest.mark.django_db
def test_cache_cleared_on_m2m_change(user, recipient_factory, message_factory, mailing_factory):
    r1 = recipient_factory(owner=user, email_prefix='r', idx=1)
    r2 = recipient_factory(owner=user, email_prefix='r', idx=2)
    msg = message_factory(owner=user)
    mailing = mailing_factory(owner=user, message=msg, recipients=[r1])
    with mock.patch.object(cache, 'clear') as clear_mock:
        mailing.recipients.add(r2)
        assert clear_mock.called
