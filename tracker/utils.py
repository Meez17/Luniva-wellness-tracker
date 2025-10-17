from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from tracker.models import Profile

def get_avg_cycle_length(user):
    return 28  # Replace with real logic

def get_most_common_flow(user):
    return "Medium"  # Replace with real logic

def get_irregular_count(user):
    return 2  # Replace with real logic

def get_cycle_trend(user):
    return "Stable"  # Replace with real logic

def get_affirmation():
    return "You are in tune with your body 💜"

from datetime import date

def predict_phase(target_date):
    """Return predicted cycle phase based on day of cycle."""
    day = target_date.day % 28  # Simplified 28-day cycle
    if 1 <= day <= 5:
        return "Menstrual Phase"
    elif 6 <= day <= 13:
        return "Follicular Phase"
    elif 14 <= day <= 16:
        return "Ovulation Phase"
    elif 17 <= day <= 28:
        return "Luteal Phase"
    else:
        return "Unknown"

def get_tip_for_phase(phase):
    """Return a wellness tip based on cycle phase."""
    tips = {
        "Menstrual Phase": "Rest, hydrate, and nourish your body gently.",
        "Follicular Phase": "Try new activities and set intentions — energy is rising.",
        "Ovulation Phase": "You're glowing! Socialize and move your body.",
        "Luteal Phase": "Slow down, reflect, and prioritize self-care.",
        "Unknown": "Track your cycle to unlock personalized tips."
    }
    return tips.get(phase, "Take care of yourself today.")

def send_period_reminders():
    today = timezone.now().date()
    profiles = Profile.objects.filter(email_reminders_enabled=True).exclude(period_reminder_days_before__isnull=True)

    for profile in profiles:
        if profile.last_period_start and profile.period_reminder_days_before:
            reminder_date = profile.last_period_start - timedelta(days=profile.period_reminder_days_before)
            if reminder_date == today:
                send_mail(
                    subject="🌸 Period Reminder",
                    message=f"Hi {profile.name}, just a gentle reminder that your period is expected soon.",
                    from_email=None,
                    recipient_list=[profile.user.email],
                    fail_silently=False,
                )
                profile.last_reminder_sent = today
                profile.save()
                print(f"Sent period reminder to {profile.user.email}")

