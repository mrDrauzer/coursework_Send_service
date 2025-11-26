from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    # Заглушка главной страницы — позже заменим на представление со статистикой
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]
