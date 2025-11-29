from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache

from .models import Attempt, Mailing, Recipient


def _invalidate_cache():
    """Простая инвалидация: очищаем весь кеш.

    Для учебного проекта это надёжно и минимально по коду.
    При необходимости можно заменить на точечные ключи.
    """
    try:
        cache.clear()
    except Exception:  # noqa: BLE001
        # В dev-окружении кеш может быть не настроен — просто игнорируем
        pass


@receiver(post_save, sender=Attempt)
@receiver(post_delete, sender=Attempt)
def invalidate_on_attempt_change(sender, **kwargs):  # noqa: D401
    """Любое изменение Attempt влияет на отчёты — сбрасываем кеш."""
    _invalidate_cache()


@receiver(post_save, sender=Mailing)
@receiver(post_delete, sender=Mailing)
def invalidate_on_mailing_change(sender, **kwargs):  # noqa: D401
    """Изменения рассылок влияют на главную (активные/всего) и отчёты."""
    _invalidate_cache()


@receiver(post_save, sender=Recipient)
@receiver(post_delete, sender=Recipient)
def invalidate_on_recipient_change(sender, **kwargs):  # noqa: D401
    """Изменение получателей влияет на метрику уникальных email на главной."""
    _invalidate_cache()


# На случай изменения состава получателей у рассылки — тоже сбрасываем кеш
@receiver(m2m_changed, sender=Mailing.recipients.through)
def invalidate_on_m2m_recipients(sender, **kwargs):
    _invalidate_cache()
