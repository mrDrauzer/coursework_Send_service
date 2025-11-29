import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_recipient_list_visibility_user(client, user, other_user, recipient_factory):
    # Один свой и один чужой получатель
    own = recipient_factory(owner=user, email_prefix="own", idx=1)
    foreign = recipient_factory(owner=other_user, email_prefix="foreign", idx=1)

    client.login(username=user.email, password="pass12345")
    resp = client.get(reverse('mailings:recipient_list'))

    # Свой виден, чужой не виден
    assert resp.status_code == 200
    content = resp.content.decode()
    assert own.email in content
    assert foreign.email not in content


@pytest.mark.django_db
def test_recipient_list_visibility_manager(client, manager, user, other_user, recipient_factory):
    r1 = recipient_factory(owner=user, email_prefix="u", idx=1)
    r2 = recipient_factory(owner=other_user, email_prefix="o", idx=2)

    client.login(username=manager.email, password="pass12345")
    resp = client.get(reverse('mailings:recipient_list'))
    assert resp.status_code == 200
    html = resp.content.decode()
    # Менеджер видит всех
    assert r1.email in html
    assert r2.email in html
