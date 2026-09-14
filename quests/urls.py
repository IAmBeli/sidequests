from django.urls import path
from . import views

urlpatterns = [
    path("get/", views.get_quest, name="get_quest"),
    path("today/", views.today, name="today"),
]