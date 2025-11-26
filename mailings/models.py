from django.conf import settings
from django.db import models


class Recipient(models.Model):
    email = models.EmailField('Email', unique=True)
    full_name = models.CharField('Ф. И. О.', max_length=255)
    comment = models.TextField('Комментарий', blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Владелец',
        on_delete=models.CASCADE,
        related_name='recipients',
    )

    class Meta:
        verbose_name = 'Получатель'
        verbose_name_plural = 'Получатели'
        permissions = (
            ('view_all_recipients', 'Может просматривать всех получателей (Менеджер)'),
        )

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    subject = models.CharField('Тема письма', max_length=255)
    body = models.TextField('Тело письма')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Владелец',
        on_delete=models.CASCADE,
        related_name='messages',
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        permissions = (
            ('view_all_messages', 'Может просматривать все сообщения (Менеджер)'),
        )

    def __str__(self) -> str:
        return self.subject


class Mailing(models.Model):
    class Status(models.TextChoices):
        CREATED = 'Создана', 'Создана'
        RUNNING = 'Запущена', 'Запущена'
        FINISHED = 'Завершена', 'Завершена'

    start_at = models.DateTimeField('Дата и время первой отправки')
    end_at = models.DateTimeField('Дата и время окончания отправки')
    status = models.CharField('Статус', choices=Status.choices, max_length=20, default=Status.CREATED)
    message = models.ForeignKey(
        Message,
        verbose_name='Сообщение',
        on_delete=models.CASCADE,
        related_name='mailings',
    )
    recipients = models.ManyToManyField(Recipient, verbose_name='Получатели', related_name='mailings')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Владелец',
        on_delete=models.CASCADE,
        related_name='mailings',
    )

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        permissions = (
            ('view_all_mailings', 'Может просматривать все рассылки (Менеджер)'),
        )

    def __str__(self) -> str:
        return f"Рассылка #{self.pk} — {self.status}"


class Attempt(models.Model):
    class AttemptStatus(models.TextChoices):
        SUCCESS = 'Успешно', 'Успешно'
        FAIL = 'Не успешно', 'Не успешно'

    when = models.DateTimeField('Дата и время попытки', auto_now_add=True)
    status = models.CharField('Статус', choices=AttemptStatus.choices, max_length=20)
    server_response = models.TextField('Ответ почтового сервера', blank=True)
    mailing = models.ForeignKey(
        Mailing,
        verbose_name='Рассылка',
        on_delete=models.CASCADE,
        related_name='attempts',
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылки'

    def __str__(self) -> str:
        return f"{self.mailing_id}: {self.status} @ {self.when:%Y-%m-%d %H:%M}"
