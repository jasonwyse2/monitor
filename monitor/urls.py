"""monitor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from monitor import views
urlpatterns = [
    path(r'admin', admin.site.urls),
    path(r'index/', views.default_index),
    path('order_search/', views.order_search),
    path('order/', views.order),
    path('',views.default_index),
    path('test/', views.testAccount),
    path('testOrder/', views.testOrder)
]
# from django.conf import settings
# if settings.DEBUG is False:
#     urlpatterns += patterns('',
#         url(r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT,
#         }),
#     )
