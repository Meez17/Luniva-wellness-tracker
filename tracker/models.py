from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

# Profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    cycle_length = models.IntegerField(blank=True, null=True)
    last_period_start = models.DateField(blank=True, null=True)
    last_period_end = models.DateField(null=True, blank=True)
    currently_on_period = models.BooleanField(default=False)

    regularity = models.CharField(
        max_length=20,
        choices=[('Regular', 'Regular'), ('Irregular', 'Irregular'), ('Uncertain', 'Uncertain')],
        blank=True
    )
    average_flow = models.CharField(
        max_length=10,
        choices=[('Light', 'Light'), ('Medium', 'Medium'), ('Heavy', 'Heavy')],
        blank=True
    )
    birth_control = models.CharField(
        max_length=20,
        choices=[('Yes', 'Yes'), ('No', 'No'), ('Prefer not to say', 'Prefer not to say')],
        blank=True
    )
    goals = models.CharField(
        max_length=50,
        choices=[
            ('Track symptoms', 'Track symptoms'),
            ('Track fertility', 'Track fertility'),
            ('Track mood', 'Track mood'),
            ('General wellness', 'General wellness')
        ],
        blank=True
    )
    notes = models.TextField(blank=True, null=True)
    pill_reminder_time = models.TimeField(blank=True, null=True)
    period_reminder_days_before = models.IntegerField(blank=True, null=True, default=2)
    last_reminder_sent = models.DateField(null=True, blank=True)
    email_reminders_enabled = models.BooleanField(default=True)
    last_reminder_sent = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username

# Cycle
class Cycle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    flow = models.CharField(max_length=20, choices=[
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('heavy', 'Heavy')
    ])
    flow_type = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True, null=True)

    def duration(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0

    def predicted_next_start(self):
        if self.end_date and self.duration():
            return self.end_date + timedelta(days=self.duration())
        return None

    def __str__(self):
        return f"{self.user.username} - {self.start_date} to {self.end_date}"
    
# FlowDay
class FlowDay(models.Model):
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name='flow_days')
    date = models.DateField()
    intensity = models.CharField(
        max_length=10,
        choices=[('Light', 'Light'), ('Medium', 'Medium'), ('Heavy', 'Heavy')])

    def __str__(self):
        return f"{self.date} - {self.intensity}"
    

class Symptom(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    mood = models.CharField(max_length=30, blank=True)  # <-- ADD THIS LINE
    cramps = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.mood}"

class Craving(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateField()
    craving_type = models.CharField(
        max_length=30,
        choices=[
            ('Sweet', 'Sweet'),
            ('Salty', 'Salty'),
            ('Spicy', 'Spicy'),
            ('Carbs', 'Carbs'),
            ('Chocolate', 'Chocolate'),
            ('Other', 'Other'),
        ]
    )
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.craving_type}"
    
# Diary
class DiaryEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default="Untitled Entry")
    date = models.DateField()
    mood = models.CharField(max_length=50, blank=True)
    custom_mood = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    short_term = models.TextField(blank=True, null=True)
    medium_term = models.TextField(blank=True, null=True)
    long_term = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Diary - {self.user.username} ({self.date})"

# Prompt and Answer
class PromptAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prompt = models.CharField(max_length=255)
    answer = models.TextField()
    date = models.DateField(auto_now_add=True)
    def __str__(self):
        return f"Prompt - {self.user.username} ({self.date})"

# Gratitude Entry
class GratitudeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    def __str__(self):
        return f"Gratitude - {self.user.username} ({self.date})"

# Mood Check-in
class MoodCheckin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    mood = models.CharField(max_length=50)
    custom_mood = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Mood Check-in - {self.user.username} ({self.date})"

# Self-Care Entry  
class SelfCareEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    sleep_hours = models.DecimalField(max_digits=4, decimal_places=1)
    energy_level = models.CharField(
        max_length=10,
        choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')],
        default='Moderate'
    )
    water_litres = models.DecimalField(max_digits=4, decimal_places=1)
    steps = models.PositiveIntegerField(blank=True, null=True)  # <-- FIXED
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Self-Care ({self.date}) - {self.user.username}"
    
# Community Models

User = get_user_model()

class CommunityPrompt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class CommunityComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    prompt = models.ForeignKey(CommunityPrompt, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    name = models.CharField(max_length=150, blank=True)
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_name(self):
        if self.is_anonymous:
            return "Anonymous"
        if self.name:
            return self.name
        if self.user:
            return self.user.get_full_name() or self.user.username
        return "Community member"

    def can_edit(self, user):
        if user.is_staff:
            return True
        if not self.user:
            return False
        if self.is_anonymous:
            return False
        return self.user == user

    def __str__(self):
        return f"Comment by {self.display_name} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
