from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contacts/", views.contacts, name="contacts"),
    path("certificates/", views.certificates, name="certificates"),
    path("colors/", views.colors, name="colors"),
    path("inquiry/", views.inquiry_create, name="inquiry"),
]
