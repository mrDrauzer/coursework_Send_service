import datetime as dt

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from mailings.models import Recipient, Message, Mailing


User = get_user_model()


@pytest.fixture(autouse=True)
def _email_backend_locmem(settings):
    """Во всех тестах используем in-memory почтовый бэкенд для отслеживания отправок."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


@pytest.fixture
def user(db):
    return User.objects.create_user(email="user@example.com", password="pass12345")


@pytest.fixture
def manager(db):
    mgr = User.objects.create_user(email="manager@example.com", password="pass12345")
    # выдать права view_all_* на все три модели
    for model in (Recipient, Message, Mailing):
        ct = ContentType.objects.get_for_model(model)
        perm = Permission.objects.get(content_type=ct, codename={
            Recipient: 'view_all_recipients',
            Message: 'view_all_messages',
            Mailing: 'view_all_mailings',
        }[model])
        mgr.user_permissions.add(perm)
    return mgr


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="other@example.com", password="pass12345")


@pytest.fixture
def recipient_factory(db):
    def _make(owner, email_prefix="user", idx=1):
        return Recipient.objects.create(
            email=f"{email_prefix}{idx}@example.com",
            full_name=f"User {idx}",
            comment="",
            owner=owner,
        )
    return _make


@pytest.fixture
def message_factory(db):
    def _make(owner, subject="Hello", idx=1):
        return Message.objects.create(subject=f"{subject} {idx}", body="Body", owner=owner)
    return _make


@pytest.fixture
def mailing_factory(db):
    def _make(owner, message, recipients, start_delta=-1, end_delta=1, status=Mailing.Status.CREATED):
        now = timezone.now()
        mailing = Mailing.objects.create(
            start_at=now + dt.timedelta(hours=start_delta),
            end_at=now + dt.timedelta(hours=end_delta),
            status=status,
            message=message,
            owner=owner,
        )
        mailing.recipients.set(recipients)
        return mailing
    return _make
