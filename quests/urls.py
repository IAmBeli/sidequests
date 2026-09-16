from django.urls import path
from . import views

app_name = "quests"

urlpatterns = [
    path("get/", views.get_quest, name="get_quest"),
    path("today/", views.today, name="today"),
    path("complete/<int:assignment_id>/", views.complete_quest, name="complete"),
    path("reroll/", views.reroll, name="reroll"),
]