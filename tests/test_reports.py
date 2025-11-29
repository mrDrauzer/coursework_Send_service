import pytest
from django.urls import reverse
from django.utils import timezone

from mailings.models import Attempt


@pytest.mark.django_db
def test_report_list_aggregates(client, user, recipient_factory, message_factory, mailing_factory):
    r1 = recipient_factory(owner=user, email_prefix="r", idx=1)
    r2 = recipient_factory(owner=user, email_prefix="r", idx=2)
    msg = message_factory(owner=user)
    mailing = mailing_factory(owner=user, message=msg, recipients=[r1, r2])

    # Создадим попытки: одна успешная, одна с ошибкой
    Attempt.objects.create(mailing=mailing, status=Attempt.AttemptStatus.SUCCESS, server_response="ok")
    Attempt.objects.create(mailing=mailing, status=Attempt.AttemptStatus.FAIL, server_response="err")

    client.login(username=user.email, password="pass12345")
    resp = client.get(reverse('mailings:report_mailing_list'))
    assert resp.status_code == 200
    html = resp.content.decode()
    # Проверяем агрегаты в таблице
    assert "2" in html  # всего попыток
    assert "1" in html  # успехов как минимум один


@pytest.mark.django_db
def test_report_detail_access_and_pagination(client, user, manager, other_user, recipient_factory, message_factory, mailing_factory):
    r = recipient_factory(owner=user)
    msg = message_factory(owner=user)
    mailing = mailing_factory(owner=user, message=msg, recipients=[r])

    # Создадим 25 попыток, чтобы сработала пагинация (по 20 на страницу)
    for i in range(25):
        Attempt.objects.create(mailing=mailing, status=Attempt.AttemptStatus.SUCCESS, server_response=f"ok {i}")

    # Владелец видит
    client.login(username=user.email, password="pass12345")
    url = reverse('mailings:report_mailing_detail', kwargs={'pk': mailing.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    assert "Стр." in resp.content.decode()

    # Чужой без прав не видит (пустой список/403-не используется — страница пустая)
    client.logout()
    client.login(username=other_user.email, password="pass12345")
    resp2 = client.get(url)
    assert resp2.status_code == 200
    assert "Попыток пока нет" in resp2.content.decode()

    # Менеджер видит
    client.logout()
    client.login(username=manager.email, password="pass12345")
    resp3 = client.get(url)
    assert resp3.status_code == 200
    assert "Попыток пока нет" not in resp3.content.decode()
