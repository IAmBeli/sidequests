from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Avg, Count, Q
import logging

from .models import Quest, Assignment
from .ai import generate_quest, QuestGenerationError

logger = logging.getLogger(__name__)

@login_required
def get_quest(request):
    if Assignment.objects.filter(user=request.user, status="active").exists():
        messages.info(request, "You already have an active quest.")
        return redirect("quests:today")
    
    if request.method == "POST":
        raw = request.POST.get("difficulty", "")
        valid = {str(value) for value, _ in Quest.DIFFICULTY_CHOICES}
        difficulty = int(raw) if raw in valid else None
        try:
            quest = generate_quest(request.user, difficulty)
        except QuestGenerationError:
            logger.exception("Quest generation failed")
            messages.error(request, "Quest generation is temporarily unavailable. Please try again later.")
            return redirect("quests:today")

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

    return render(request, "quests/get_quest.html", {"difficulty_choices": Quest.DIFFICULTY_CHOICES})

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
    
    try:
        assignment.quest = generate_quest(request.user)
    except:
        logger.exception("Quest generation failed")
        messages.error(request, "Quest generation is temporarily unavailable. Please try again later.")
        return redirect("quests:today")
    
    assignment.rerolls_used += 1
    assignment.save()
    return redirect("quests:today")

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("quests:today")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def stats(request):
    assignments = Assignment.objects.filter(user=request.user)

    totals = assignments.aggregate(
        completed = Count("id", filter=Q(status="completed")),
        failed = Count("id", filter=Q(status="failed")),
        avg_rerolls = Avg("rerolls_used"),
    )

    finished = totals["completed"] + totals["failed"]
    completion_rate = round(totals["completed"] / finished * 100) if finished else None

    by_category = (
        assignments.filter(status="completed")
        .values("quest__category")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return render(request, "quests/stats.html", {
        "totals": totals,
        "completion_rate": completion_rate,
        "by_category": by_category,
    })