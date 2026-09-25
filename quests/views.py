from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

from .models import Quest, Assignment
from .ai import generate_quest

@login_required
def get_quest(request):
    if Assignment.objects.filter(user=request.user, status="active").exists():
        messages.info(request, "You already have an active quest.")
        return redirect("quests:today")
    
    if request.method == "POST":
        quest = generate_quest(request.user)

        new_quest = Quest.objects.create(
            text=quest.text,
            difficulty=quest.difficulty,
            category=quest.category,
        )

        Assignment.objects.create(
            user=request.user,
            quest=new_quest,
            deadline=timezone.now() + timedelta(hours=24),
        )

        return redirect("quests:today")

    return render(request, "quests/get_quest.html")

@login_required
def today(request):
    assignments = Assignment.objects.filter(user=request.user, status="active").select_related("quest")
    return render(request, "quests/today.html", {"assignments": assignments})

@login_required
def complete_quest(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)

    description = request.POST.get("description", "").strip()
    if not description:
        assignments = Assignment.objects.filter(user=request.user, status="active").select_related("quest")
        return render(request, "quests/today.html", {
            "assignments": assignments,
            "error": "Please describe what you did before completing the quest.",
            "error_assignment_id": assignment.id,
            "entered_description": request.POST.get("description", "")
        })

    assignment.status = "completed"
    assignment.description = description
    assignment.photo = request.FILES.get("photo")
    assignment.completed_at = timezone.now()
    assignment.save()
    messages.info(request, "Assignment marked as completed")
    return redirect("quests:today")

@login_required
def reroll(request):
    assignment = get_object_or_404(Assignment, user=request.user, status="active")

    if assignment.rerolls_used >= 3:
        messages.info(request, "Rerolls limit reached")
        return redirect("quests:today")
    
    quest = generate_quest(request.user)
    assignment.quest = quest
    assignment.rerolls_used += 1
    assignment.save()
    return redirect("quests:today")