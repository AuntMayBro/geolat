from django.contrib import admin
from django.urls import path, include


app_name = 'geolat'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('attendance.urls')),
]
