"""hamlet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import path, include
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('about/',
        TemplateView.as_view(template_name='about.html'), name='about'),
    # Note that URLs imported from theses all have top-level URL paths!
    # Because they're the meat of the application there's no reason to add
    # cruft to the URL.
    path(r'', include('hamlet.theses.urls')),
    path(r'citations/', include('hamlet.citations.urls')),
    path('captcha/', include('captcha.urls')),
    path('health/', include('health_check.urls')),
    path(
        'robots.txt',
        TemplateView.as_view(template_name='robots.txt', content_type='text/plain'),
    ),
]
