from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.views.decorators.cache import cache_page
from django.templatetags.static import static as static_tag
from django.conf import settings
from django.conf.urls.static import static
from mailings.views import HomeStatsView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('mailings/', include('mailings.urls', namespace='mailings')),
    # Главная страница со статистикой
    # ВАЖНО: не кешируем целиком страницу, т.к. она содержит пользовательский
    # header (navbar) с блоком авторизации. Иначе после входа/выхода
    # состояние будет отображаться некорректно до обновления кеша.
    path('', HomeStatsView.as_view(), name='home'),
    # Явный маршрут для фавиконки, чтобы избежать 404 на /favicon.ico
    path('favicon.ico', RedirectView.as_view(url=static_tag('favicon.svg'), permanent=False), name='favicon'),
]

# Медиа-файлы для разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
