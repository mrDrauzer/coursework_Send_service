from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя: авторизация по email.

    Доп. поля: avatar, phone, country.
    """

    username = None  # отключаем username
    email = models.EmailField('Email', unique=True)

    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(
        'Телефон',
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^[0-9+()\-\s]+$', 'Введите корректный телефон')],
    )
    country = models.CharField('Страна', max_length=100, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email or super().__str__()
