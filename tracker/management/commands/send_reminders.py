from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils.timezone import now
from tracker.models import Profile

class Command(BaseCommand):
    help = 'Send email reminders to users'

    def handle(self, *args, **kwargs):
        current_time = now().time().replace(second=0, microsecond=0)
        profiles = Profile.objects.filter(email_reminders_enabled=True, reminder_time=current_time)

        for profile in profiles:
            if profile.user.email:
                send_mail(
                    subject="🌸 Luniva Reminder",
                    message=f"Hi {profile.name or profile.user.username}, this is your gentle reminder to check in with Luniva today 💜",
                    from_email="noreply@luniva.com",
                    recipient_list=[profile.user.email],
                    fail_silently=True
                )
        self.stdout.write(self.style.SUCCESS('Reminders sent successfully.'))
