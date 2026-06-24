from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("catalog/", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("product/<uslug:slug>/", views.product, name="product"),
    path("catalog/<uslug:slug>/", views.category, name="category"),
]
