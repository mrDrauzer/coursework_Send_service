from django.core.mail import send_mail
from django.utils import timezone
from typing import Tuple

from .models import Mailing, Attempt


def is_within_window(mailing: Mailing) -> bool:
    now = timezone.now()
    return mailing.start_at <= now <= mailing.end_at


def run_mailing(mailing: Mailing) -> Tuple[int, int]:
    """Выполнить отправку писем по рассылке.

    Возвращает кортеж (успешно, ошибок).
    Создаёт запись Attempt с суммарным результатом.
    Обновляет статус рассылки: RUNNING -> FINISHED по завершении одной итерации.
    """
    success, errors = 0, 0
    subject = mailing.message.subject
    body = mailing.message.body

    # Отправляем по одному письму каждому получателю
    for recipient in mailing.recipients.all():
        try:
            sent = send_mail(
                subject=subject,
                message=body,
                from_email=None,  # возьмётся из DEFAULT_FROM_EMAIL
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            if sent:
                success += 1
            else:
                errors += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            last_error = str(e)
        else:
            last_error = ''

    status = Attempt.AttemptStatus.SUCCESS if errors == 0 else Attempt.AttemptStatus.FAIL
    response = f"OK: {success}; ERRORS: {errors}"
    if last_error:
        response += f"; last_error={last_error}"
    Attempt.objects.create(mailing=mailing, status=status, server_response=response)

    # Одноразовая отправка — помечаем как завершённую
    mailing.status = Mailing.Status.FINISHED
    mailing.save(update_fields=["status"])

    return success, errors
