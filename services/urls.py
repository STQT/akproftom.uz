from django.urls import path

from . import views

app_name = "services"

urlpatterns = [
    path("", views.service_list, name="list"),
    path("<uslug:slug>/", views.service_detail, name="detail"),
]
