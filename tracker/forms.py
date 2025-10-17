from django import forms
from .models import Profile, Cycle, Symptom, FlowDay, Craving, DiaryEntry, SelfCareEntry, PromptAnswer, GratitudeEntry, CommunityComment, CommunityPrompt
from django.forms.widgets import DateInput, TimeInput, Textarea
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from datetime import date

# Shared styling
DATE_WIDGET = DateInput(attrs={'type': 'date', 'class': 'form-control'})
TEXTAREA_WIDGET = Textarea(attrs={'rows': 3, 'class': 'form-control'})

# User Registration Form
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# Profile Form
class ProfileForm(forms.ModelForm):
    REGULARITY_CHOICES = [
        ('Regular', 'Regular'),
        ('Irregular', 'Irregular'),
        ('Uncertain', 'Uncertain'),
    ]

    FLOW_CHOICES = [
        ('Light', 'Light'),
        ('Medium', 'Medium'),
        ('Heavy', 'Heavy'),
    ]

    BIRTH_CONTROL_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Prefer not to say', 'Prefer not to say'),
    ]

    GOAL_CHOICES = [
        ('Track symptoms', 'Track symptoms'),
        ('Track fertility', 'Track fertility'),
        ('Track mood', 'Track mood'),
        ('General wellness', 'General wellness'),
    ]

    name = forms.CharField(required=True, label="Name")
    age = forms.IntegerField(required=False, label="Age")
    cycle_length = forms.IntegerField(required=False, label="Cycle Length")
    last_period_start = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label="Last Period Start")
    last_period_end = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label="Last Period End")
    currently_on_period = forms.BooleanField(required=False, label="Are you currently on your period?")
    regularity = forms.ChoiceField(required=False, choices=REGULARITY_CHOICES, label="Cycle Regularity")
    average_flow = forms.ChoiceField(required=False, choices=FLOW_CHOICES, label="Average Flow")
    birth_control = forms.ChoiceField(required=False, choices=BIRTH_CONTROL_CHOICES, label="Birth Control")
    goals = forms.ChoiceField(required=False, choices=GOAL_CHOICES, label="Wellness Goals")
    notes = forms.CharField(required=False, widget=Textarea(attrs={'rows': 3}), label="Notes")
    pill_reminder_time = forms.TimeField(required=False, widget=TimeInput(attrs={'type': 'time'}), label="Pill Reminder Time")
    period_reminder_days_before = forms.IntegerField(required=False, label="Days Before Period Reminder")
    email_reminders_enabled = forms.BooleanField(required=False, label="Receive email reminders")
    last_reminder_sent = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label="Last Reminder Sent")
    
    class Meta:
        model = Profile
        fields = [
            'name', 'age', 'cycle_length', 'last_period_start', 'last_period_end',
            'currently_on_period', 'regularity', 'average_flow', 'birth_control',
            'goals', 'notes', 'pill_reminder_time', 'period_reminder_days_before',
            'email_reminders_enabled', 'last_reminder_sent'
        ]

# Cycle Form
class CycleForm(forms.ModelForm):
    start_date = forms.DateField(required=False, widget=DATE_WIDGET)
    end_date = forms.DateField(required=False, widget=DATE_WIDGET)
    flow_type = forms.CharField(required=False)
    notes = forms.CharField(required=False, widget=TEXTAREA_WIDGET)
    irregular_days = forms.CharField(required=False, widget=forms.HiddenInput())
    is_irregular = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id': 'is_irregular'}))

    class Meta:
        model = Cycle
        fields = ['start_date', 'end_date', 'flow_type', 'notes', 'irregular_days', 'is_irregular']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today_iso = date.today().isoformat()
        # Prevent selecting future dates for start and end
        self.fields['start_date'].widget.attrs['max'] = today_iso
        self.fields['end_date'].widget.attrs['max'] = today_iso
        # If a start_date is present in form data, enforce it as min for end_date
        if 'start_date' in self.data and self.data.get('start_date'):
            try:
                self.fields['end_date'].widget.attrs['min'] = self.data.get('start_date')
            except Exception:
                pass

class FlowDayForm(forms.ModelForm):
    cycle = forms.ModelChoiceField(queryset=Cycle.objects.none(), required=False)
    date = forms.DateField(required=False, widget=DATE_WIDGET)
    INTENSITY_CHOICES = [
        ('Light', 'Light'),
        ('Medium', 'Medium'),
        ('Heavy', 'Heavy'),
    ]
    intensity = forms.ChoiceField(choices=INTENSITY_CHOICES, required=True, label="Flow Intensity")

    class Meta:
        model = FlowDay
        fields = ['cycle', 'date', 'intensity']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        today_iso = date.today().isoformat()
        # Default: prevent future dates
        self.fields['date'].widget.attrs['max'] = today_iso
        # Limit cycle choices to current user only
        if user:
            self.fields['cycle'].queryset = Cycle.objects.filter(user=user).order_by('-start_date')
        else:
            self.fields['cycle'].queryset = Cycle.objects.none()

        # If a cycle was selected (POST or GET), restrict date to cycle range
        cycle_val = None
        # prefer cleaned_data if available (bound form), else data (unbound/initial)
        if self.is_bound:
            cycle_val = self.data.get('cycle') or None
        else:
            cycle_val = self.initial.get('cycle') or None

        try:
            if cycle_val:
                cycle_id = int(cycle_val)
                cycle = Cycle.objects.get(id=cycle_id)
                # enforce min/max on the date widget
                self.fields['date'].widget.attrs['min'] = cycle.start_date.isoformat()
                if cycle.end_date:
                    self.fields['date'].widget.attrs['max'] = cycle.end_date.isoformat()
        except Exception:
            pass

# Symptom Form
class SymptomForm(forms.ModelForm):
    date = forms.DateField(required=False, widget=DATE_WIDGET)
    mood = forms.ChoiceField(required=False, choices=[
        ('😊', 'Happy'), ('😢', 'Sad'), ('😠', 'Angry'),
        ('😴', 'Tired'), ('😕', 'Confused'), ('❤️', 'Loved'),
        ('🌸', 'Peaceful'), ('Other', 'Other')
    ])
    custom_mood = forms.CharField(required=False, label="If other, specify")

    CRAMPS_CHOICES = [
        (True, 'Yes'),
        (False, 'No'),
    ]
    cramps = forms.ChoiceField(required=False, choices=CRAMPS_CHOICES, label="Cramps")

    flow_intensity = forms.ChoiceField(required=False, choices=[
        ('Light', 'Light'), ('Medium', 'Medium'), ('Heavy', 'Heavy'), ('Other', 'Other')
    ])

    notes = forms.CharField(required=False, widget=TEXTAREA_WIDGET)

    class Meta:
        model = Symptom
        fields = ['date', 'mood', 'custom_mood', 'cramps', 'flow_intensity', 'notes']

# Craving Form
class CravingForm(forms.ModelForm):
    date = forms.DateField(required=False, widget=DATE_WIDGET)
    craving_type = forms.ChoiceField(required=False, choices=[
        ('Sweet', 'Sweet'), ('Salty', 'Salty'), ('Savory', 'Savory'),
        ('Carbs', 'Carbs'), ('Fruits', 'Fruits'), ('Vegetables', 'Vegetables'),
        ('Other', 'Other')
    ])
    custom_craving = forms.CharField(required=False, label="If other, specify")
    notes = forms.CharField(required=False, widget=TEXTAREA_WIDGET)

    class Meta:
        model = Craving
        fields = ['date', 'craving_type', 'custom_craving', 'notes']

# Diary Entry Form
class DiaryForm(forms.ModelForm):
    title = forms.CharField(required=False)
    date = forms.DateField(required=False, widget=DATE_WIDGET)
    mood = forms.ChoiceField(required=False, choices=[
        ('😊', 'Happy'), ('😢', 'Sad'), ('😠', 'Angry'),
        ('😴', 'Tired'), ('😕', 'Confused'), ('❤️', 'Loved'),
        ('🌸', 'Peaceful'), ('Other', 'Other')
    ])
    custom_mood = forms.CharField(required=False, label="If other, specify")
    content = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}))
    short_term = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Short-Term Goals")
    medium_term = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Medium-Term Goals")
    long_term = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Long-Term Goals")

    class Meta:
        model = DiaryEntry
        fields = ['title', 'date', 'mood', 'custom_mood', 'content', 'short_term', 'medium_term', 'long_term']

# Prompt Answer Form
class PromptAnswerForm(forms.ModelForm):
    class Meta:
        model = PromptAnswer
        fields = ['prompt', 'answer']
        widgets = {
            'prompt': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# Gratitude Entry Form        
class GratitudeForm(forms.ModelForm):
    class Meta:
        model = GratitudeEntry
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# Self-Care Entry Form
class SelfCareForm(forms.ModelForm):
    date = forms.DateField(required=False, widget=DATE_WIDGET)
    sleep_hours = forms.DecimalField(required=False)

    ENERGY_CHOICES = [
    ('Low', 'Low'),
    ('Moderate', 'Moderate'),
    ('High', 'High'),]
    energy_level = forms.ChoiceField(required=False,choices=ENERGY_CHOICES,label="Energy Level") # <-- Add this line
    
    water_litres = forms.DecimalField(required=False)
    steps = forms.IntegerField(required=False)
    notes = forms.CharField(required=False, widget=TEXTAREA_WIDGET)
 
    class Meta:
        model = SelfCareEntry
        fields = ['date', 'sleep_hours', 'water_litres', 'steps','energy_level', 'notes']

# Community Comment Form
class CommunityCommentForm(forms.ModelForm):
    class Meta:
        model = CommunityComment
        fields = ['name', 'content', 'is_anonymous']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name (optional)', 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'placeholder': 'Share your thoughts...', 'class': 'form-control', 'rows': 4}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Name',
            'content': 'Comment',
            'is_anonymous': 'Post anonymously',
        }

class CommunityPromptForm(forms.ModelForm):
    class Meta:
        model = CommunityPrompt
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prompt title (e.g. What helps you feel grounded?)'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control mt-2',
                'placeholder': 'Share your thoughts here',
                'rows': 4
            }),
        }
        labels = {
            'title': 'Prompt Title',
            'content': 'Optional Description',
        }



