from django.conf import settings
from django.db import models
from pgvector.django import VectorField

class Quest(models.Model):
    DIFFICULTY_CHOICES = [
        (1, "Very easy"),
        (2, "Easy"),
        (3, "Medium"),
        (4, "Hard"),
        (5, "Very hard"),
    ]
    CATEGORY_CHOICES = [
        ("physical", "Physical"),
        ("social", "Social"),
        ("creative", "Creative"),
        ("exploration", "Exploration")
    ]

    text = models.TextField()
    difficulty = models.PositiveSmallIntegerField(choices=DIFFICULTY_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    embedding = VectorField(dimensions=768, null=True, blank=True)

    def __str__(self):
        return self.text[:50]

class Assignment(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    quest = models.ForeignKey(
        Quest,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    taken_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    completed_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="proofs/", null=True, blank=True)
    rerolls_used = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.quest.text[:30]}"