from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView, RedirectView
from django.templatetags.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    # Заглушка главной страницы — позже заменим на представление со статистикой
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    # Явный маршрут для фавиконки, чтобы избежать 404 на /favicon.ico
    path('favicon.ico', RedirectView.as_view(url=static('favicon.svg'), permanent=False), name='favicon'),
]
