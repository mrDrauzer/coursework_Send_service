Сервис управления рассылками (курсовой проект на Django)
=======================================================

Кратко
— Веб‑приложение на Django для управления клиентами, сообщениями и рассылками: создание, редактирование, удаление, запуск рассылок и сбор статистики по попыткам отправки.

Статус
— Подготовлен каркас проекта: структура Django, приложения users и mailings, модели, базовые настройки, шаблоны base/index, .env.example.
— Далее план: миграции, CRUD и шаблоны, аутентификация/регистрация, права доступа, отправка рассылок, кеширование и отчёты.

Требования
- Python >= 3.8,<4.0
- Poetry

Быстрый старт
1) Установите Poetry (если не установлен):
   Windows (PowerShell): (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

2) Установите зависимости:
   poetry install

3) Создайте .env на основе примера:
   копируйте .env.example -> .env и при необходимости измените значения.

4) Примените миграции и запустите сервер разработки:
   poetry run python manage.py migrate
   poetry run python manage.py runserver

5) Зайдите в админку (опционально):
   poetry run python manage.py createsuperuser
   http://127.0.0.1:8000/admin/

Структура проекта
(на текущем этапе)

project-root/
├─ config/                  # Конфигурация Django‑проекта
│  ├─ __init__.py
│  ├─ settings.py           # Настройки (переменные читаются из .env)
│  ├─ urls.py               # Корневые URL
│  ├─ asgi.py
│  └─ wsgi.py
├─ users/                   # Приложение пользователей
│  ├─ __init__.py
│  ├─ admin.py              # Админ‑регистрация кастомной модели
│  ├─ apps.py
│  ├─ models.py             # Кастомная модель User (email как логин, avatar, phone, country)
│  └─ migrations/
│     └─ __init__.py
├─ mailings/                # Приложение рассылок
│  ├─ __init__.py
│  ├─ admin.py              # Админ‑регистрация моделей рассылок
│  ├─ apps.py
│  └─ models.py             # Recipient, Message, Mailing, Attempt (+ owner, Meta‑права)
├─ templates/
│  ├─ base.html             # Базовый шаблон, хедер, навигация и кнопки
│  └─ index.html            # Главная страница (пока заглушка)
├─ manage.py                # Точка входа Django
├─ .env.example             # Пример переменных окружения
├─ .gitignore
├─ pyproject.toml           # Конфигурация Poetry (зависимости)
├─ README.txt               # Этот файл
└─ main.py                  # Вспомогательный скрипт (не используется Django)

Переменные окружения (.env)
— Пример в .env.example. Ключевые:
- SECRET_KEY=...            # секретный ключ Django
- DEBUG=True|False
- ALLOWED_HOSTS=127.0.0.1,localhost
- SQLITE_NAME=db.sqlite3    # имя файла SQLite (по умолчанию)

Email (для разработки)
- EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
— Письма выводятся в консоль. Для реальной отправки переключите на SMTP и заполните EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS/SSL.

Дальнейший план (высокоуровнево)
1) Миграции для users и mailings, проверка админки.
2) CRUD для клиентов/сообщений/рассылок (CBV), фильтрация по владельцу, права «Менеджеров».
3) Аутентификация: регистрация, вход/выход, профиль, восстановление пароля; подтверждение email.
4) Отправка рассылок из интерфейса и management‑командой; фиксация Attempt.
5) Главная: статистика (всего рассылок, активных, уникальных получателей); страница отчётов.
6) Кеширование (server‑side) ключевых страниц/фрагментов.

Лицензия
— Учебный проект. Лицензия не указана (по умолчанию все права защищены). По необходимости добавьте LICENSE.
