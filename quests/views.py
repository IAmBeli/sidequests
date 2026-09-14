from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import Quest, Assignment
from .ai import generate_quest

@login_required
def get_quest(request):
    if request.method == "POST":
        result = generate_quest()

        quest = Quest.objects.create(
            text=result.text,
            difficulty=result.difficulty,
            category=result.category,
        )

        Assignment.objects.create(
            user=request.user,
            quest=quest,
            deadline=timezone.now() + timedelta(hours=24),
        )

        return redirect("today")

    return render(request, "quests/get_quest.html")

@login_required
def today(request):
    assignments = Assignment.objects.filter(user=request.user, status="active").select_related("quest")
    return render(request, "quests/today.html", {"assignments": assignments})