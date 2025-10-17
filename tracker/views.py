from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import JsonResponse
from django.db.models import Q
from .models import Cycle, Symptom, Profile, FlowDay, Craving, DiaryEntry, SelfCareEntry, GratitudeEntry, MoodCheckin, PromptAnswer, CommunityComment, CommunityPrompt
from .forms import ProfileForm, CycleForm, SymptomForm, FlowDayForm, CravingForm, DiaryForm, SelfCareForm, SignUpForm, GratitudeForm, PromptAnswerForm, CommunityCommentForm, CommunityPromptForm
from statistics import mean
import random
from datetime import datetime, timedelta, date
from collections import Counter
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse

# Public pages
def home(request):
    """Render the public home page."""
    return render(request, "tracker/pages/home.html")


def about(request):
    """Render the about page."""
    return render(request, "tracker/pages/about.html")


def contact(request):
    """Render the contact page."""
    return render(request, "tracker/pages/contact.html")

# Welcome page after login
@login_required
def welcome(request):
    """Render the welcome page after login."""
    return render(request, 'tracker/pages/welcome.html')

# Authentication / Sign up
def sign_up(request):
    """Handle user registration and initial profile creation."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('welcome')
    else:
        form = SignUpForm()
    return render(request, 'tracker/registration/sign_up.html', {'form': form})

# Dashboard - Main display
@login_required
def dashboard(request):
    """ Render the main dashboard for the logged-in user."""
    profile = Profile.objects.get(user=request.user)

    # Fetch user-specific data (explicitly filtered)
    cycles = Cycle.objects.filter(user=request.user).order_by('-start_date')
    symptoms = Symptom.objects.filter(profile=profile).order_by('-date')
    cravings = Craving.objects.filter(profile=profile).order_by('-date')
    flow_days = FlowDay.objects.filter(cycle__user=request.user).order_by('date')
    diary_entries = DiaryEntry.objects.filter(user=request.user).order_by('date')
    latest_selfcare = SelfCareEntry.objects.filter(user=request.user).order_by('-date').first()

    # Cycle calculations: collect durations and compute average cycle length
    cycle_lengths = [c.duration() for c in cycles if c.duration()]
    avg_cycle_length = int(mean(cycle_lengths)) if cycle_lengths else getattr(profile, 'cycle_length', None)

    # Flow types & irregular count
    flow_types = [c.flow_type for c in cycles if c.flow_type]
    most_common_flow = Counter(flow_types).most_common(1)[0][0] if flow_types else "Unknown"
    irregular_count = sum(1 for c in cycles if c.flow_type == "Irregular")

    # Simple trend detection (compare first half vs second half)
    trend = "Stable"
    if len(cycle_lengths) >= 4:
        mid = len(cycle_lengths) // 2
        first_half = cycle_lengths[:mid]
        second_half = cycle_lengths[mid:]
        if mean(second_half) > mean(first_half) + 1:
            trend = "Getting longer"
        elif mean(second_half) < mean(first_half) - 1:
            trend = "Getting shorter"

    # Cycle Predictions
    next_period_date = predicted_phase = care_tip = None

    # Only attempt predictions when we have at least 2 cycles and an avg length
    if len(cycles) >= 2 and avg_cycle_length:
        # Sort cycles by start_date descending (most recent first), guard against None
        cycles = sorted(cycles, key=lambda c: c.start_date or date.min, reverse=True)
        last_cycle = cycles[0]

        reference_date = last_cycle.end_date or last_cycle.start_date
        if reference_date and last_cycle.start_date:
            try:
                days_to_add = int(avg_cycle_length)
            except Exception:
                days_to_add = avg_cycle_length or 28

            next_period_date = reference_date + timedelta(days=days_to_add)
            today = date.today()
            days_since_last_start = (today - last_cycle.start_date).days

            if days_since_last_start < 0:
                predicted_phase = "Between cycles"
            elif days_since_last_start <= 5:
                predicted_phase = "Menstrual"
            elif 6 <= days_since_last_start <= 13:
                predicted_phase = "Follicular"
            elif 14 <= days_since_last_start <= 15:
                predicted_phase = "Ovulation"
            elif 16 <= days_since_last_start <= days_to_add:
                predicted_phase = "Luteal"
            else:
                predicted_phase = "Between cycles"

            # Care tips per phase
            phase_care_tips = {
                "Menstrual": "Rest, nourish your body, and prioritize gentle self-care.",
                "Follicular": "Plan, create, and enjoy rising energy.",
                "Ovulation": "Connect, collaborate, and embrace confidence.",
                "Luteal": "Slow down, reflect, and support your emotional needs.",
                "Between cycles": "Track your next cycle start to stay in sync."
            }
            care_tip = phase_care_tips.get(predicted_phase, "Listen to your body and rest as needed.")
        else:
            next_period_date = predicted_phase = care_tip = None

    # Flow chart data for client-side charting (user-scoped)
    intensity_map = {'Light': 1, 'Medium': 2, 'Heavy': 3}
    color_map = {'Light': '#F4E1D2', 'Medium': '#A18BD0', 'Heavy': '#ECA1A6'}

    flow_chart_data = {
        'labels': [fd.date.strftime('%Y-%m-%d') for fd in flow_days],
        'values': [intensity_map.get(fd.intensity, 0) for fd in flow_days],
        'colors': [color_map.get(fd.intensity, '#cccccc') for fd in flow_days]
    }

    # Combined Mood and Craving data
    mood_counts = Counter([s.mood for s in symptoms])
    craving_counts = Counter([c.craving_type for c in cravings])
    combined_labels = list(set(mood_counts.keys()) | set(craving_counts.keys()))
    combined_chart_data = {
        'labels': combined_labels,
        'moods': [mood_counts.get(label, 0) for label in combined_labels],
        'cravings': [craving_counts.get(label, 0) for label in combined_labels]
    }

    # Daily affirmation and reminders
    affirmations = [
        "You are strong, capable, and radiant.",
        "Your cycle is a part of your power.",
        "You deserve rest, love, and joy.",
        "Every phase of your flow is beautiful.",
        "You are blooming in your own time.",
        "Your wellness matters every single day.",
        "My menstrual cycle is a natural and sacred process",
        "Honor the flow of your energy and body",
        "Allow yourself to rest and recharge when needed",
        "You are connected to your feminine essence",
        "Trust your body's wisdom to guide you",
        "Your body is a source of power and wisdom",
        "You are strong and capable, in every phase of your cycle",
        "Embrace the natural rhythm of your body",
        "You are in tune with your body's needs",
        "You are connected to your inner strength",
        "Love and accept your body exactly as it is",
        "Your body is beautiful and worthy of care",
        "Nourish your body with kindness and compassion",
        "Release any judgment about your body",
        "You are a complete and whole being, in every season of life",
    ]
    daily_affirmation = random.choice(affirmations)

    today = date.today()
    now = datetime.now().time()
    show_period_reminder = False
    show_pill_reminder = False

    if getattr(profile, "last_period_start", None) and getattr(profile, "cycle_length", None):
        try:
            next_period = profile.last_period_start + timedelta(days=profile.cycle_length)
            reminder_day = next_period - timedelta(days=profile.period_reminder_days_before or 0)
            show_period_reminder = today == reminder_day
        except Exception:
            show_period_reminder = False

    if getattr(profile, "pill_reminder_time", None):
        if now.hour == profile.pill_reminder_time.hour and abs(now.minute - profile.pill_reminder_time.minute) <= 5:
            show_pill_reminder = True

    context = {
        'profile': profile,
        'cycles': cycles,
        'symptoms': symptoms,
        'cravings': cravings,
        'flow_days': flow_days,
        'diary_entries': diary_entries,
        'avg_cycle_length': avg_cycle_length,
        'next_period_date': next_period_date,
        'predicted_phase': predicted_phase,
        'care_tip': care_tip,
        'most_common_flow': most_common_flow,
        'irregular_count': irregular_count,
        'cycle_trend': trend,
        'flow_chart_data': flow_chart_data,
        'combined_chart_data': combined_chart_data,
        'daily_affirmation': daily_affirmation,
        'show_period_reminder': show_period_reminder,
        'show_pill_reminder': show_pill_reminder,
        'latest_selfcare': latest_selfcare,
    }

    return render(request, 'tracker/main/dashboard.html', context)

# Profile
@login_required
def profile(request):
    """View and edit the user's profile."""
    profile_obj, created = Profile.objects.get_or_create(user=request.user)

    # Auto-fill name if profile is newly created or empty
    if not getattr(profile_obj, "name", None):
        profile_obj.name = request.user.first_name or request.user.username
        profile_obj.save()

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=profile_obj)

    return render(request, "tracker/pages/profile.html", {
        "form": form,
        "profile": profile_obj
    })

# Site search
@login_required
def site_search(request):
    """Search across different models for the logged-in user."""
    query = request.GET.get('q')
    if not query:
        return render(request, 'tracker/search_results.html', {'query': '', 'results': {}})

    results = {
        'diary': DiaryEntry.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(short_term__icontains=query) |
            Q(medium_term__icontains=query) |
            Q(long_term__icontains=query)
        ).filter(user=request.user),
        'cycles': Cycle.objects.filter(
            Q(notes__icontains=query) |
            Q(flow_type__icontains=query)
        ).filter(user=request.user),
        'symptoms': Symptom.objects.filter(
            Q(symptom_type__icontains=query) | Q(notes__icontains=query)
        ).filter(profile__user=request.user),
        'cravings': Craving.objects.filter(
            Q(craving_type__icontains=query) | Q(notes__icontains=query)
        ).filter(profile__user=request.user),
        'flow_days': FlowDay.objects.filter(
            Q(intensity__icontains=query) | Q(notes__icontains=query)
        ).filter(cycle__user=request.user),
        'selfcare': SelfCareEntry.objects.filter(Q(notes__icontains=query)).filter(user=request.user),
        'gratitude': GratitudeEntry.objects.filter(Q(content__icontains=query)).filter(user=request.user),
        'prompts': PromptAnswer.objects.filter(Q(prompt__icontains=query) | Q(answer__icontains=query)).filter(user=request.user),
    }

    return render(request, 'tracker/search_results.html', {
        'query': query,
        'results': results,
    })

# Cycle and FlowDay creation
@login_required
def add_cycle(request):
    if request.method == 'POST':
        form = CycleForm(request.POST)
        if form.is_valid():
            is_irregular = form.cleaned_data.get('is_irregular')
            irregular_days_raw = form.cleaned_data.get('irregular_days', '')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            flow_type = form.cleaned_data.get('flow_type')
            notes = form.cleaned_data.get('notes')

            if is_irregular and irregular_days_raw:
                try:
                    days = [datetime.fromisoformat(d).date() for d in irregular_days_raw.split(',') if d]
                    if days:
                        sd = min(days)
                        ed = max(days)
                        Cycle.objects.create(
                            user=request.user,
                            start_date=sd,
                            end_date=ed,
                            flow_type=flow_type or 'Irregular',
                            notes=f"Irregular days: {', '.join([d.isoformat() for d in days])}" + (f"\n\n{notes}" if notes else "")
                        )
                        messages.success(request, "Irregular cycle logged.")
                        return redirect('dashboard')
                    else:
                        messages.error(request, "No valid dates selected for irregular cycle.")
                except Exception as e:
                    messages.error(request, f"Error saving irregular cycle: {e}")
            else:
                if not start_date or not end_date:
                    messages.error(request, "Please provide both start and end dates.")
                elif start_date > end_date:
                    messages.error(request, "Start date cannot be after end date.")
                else:
                    Cycle.objects.create(
                        user=request.user,
                        start_date=start_date,
                        end_date=end_date,
                        flow_type=flow_type,
                        notes=notes
                    )
                    messages.success(request, "Cycle logged successfully.")
                    return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CycleForm()

    return render(request, 'tracker/pages/add_cycle.html', {'form': form})

@login_required
def add_flow_day(request):
    """Add a flow-day entry. Ensures the related cycle belongs to the current user and limits choices."""
    # Prepare initial values from GET (so ?cycle=4 persists in the form)
    initial = {}
    if 'cycle' in request.GET:
        try:
            initial['cycle'] = int(request.GET.get('cycle'))
        except Exception:
            pass
    if 'date' in request.GET:
        initial['date'] = request.GET.get('date')

    if request.method == 'POST':
        form = FlowDayForm(request.POST, user=request.user)
        if form.is_valid():
            flow_day = form.save(commit=False)
            # Server-side safety checks
            if not flow_day.cycle or flow_day.cycle.user != request.user:
                messages.error(request, "Invalid cycle selection.")
                return redirect('add_flow_day')
            if not flow_day.date:
                messages.error(request, "Please select a date.")
                return redirect('add_flow_day')
            if flow_day.date < flow_day.cycle.start_date or (flow_day.cycle.end_date and flow_day.date > flow_day.cycle.end_date):
                messages.error(request, "Selected date is outside the chosen cycle range.")
                return redirect('add_flow_day')
            flow_day.save()
            messages.success(request, "Flow day added successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FlowDayForm(user=request.user, initial=initial)

    return render(request, 'tracker/pages/add_flow_day.html', {'form': form})

@login_required
def flow_day_json(request):
    flow_days = FlowDay.objects.filter(cycle__user=request.user).order_by('date')
    intensity_map = {'Light': 1, 'Medium': 2, 'Heavy': 3}
    color_map = {'Light': '#F4E1D2', 'Medium': '#A18BD0', 'Heavy': '#ECA1A6'}
    labels = [fd.date.strftime('%Y-%m-%d') for fd in flow_days]
    values = [intensity_map.get(fd.intensity, 0) for fd in flow_days]
    colors = [color_map.get(fd.intensity, '#ccc') for fd in flow_days]
    return JsonResponse({'labels': labels, 'values': values, 'colors': colors})

@login_required
def cycles_json(request):
    """Return cycles data as JSON for charting/overview."""
    cycles = Cycle.objects.filter(user=request.user).order_by('start_date')
    labels = [c.start_date.strftime('%Y-%m-%d') for c in cycles]
    durations = [c.duration() or 0 for c in cycles]
    flows = [c.flow_type or '' for c in cycles]
    return JsonResponse({'labels': labels, 'durations': durations, 'flows': flows})

# Symptoms
@login_required
def add_symptom(request):
    """ Log a symptom and mood tied to the user's profile."""
    profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        form = SymptomForm(request.POST)
        if form.is_valid():
            mood = form.cleaned_data.get('mood')
            custom_mood = form.cleaned_data.get('custom_mood')
            symptom = form.save(commit=False)
            symptom.profile = profile
            symptom.mood = custom_mood if mood == 'Other' and custom_mood else mood
            symptom.save()
            messages.success(request, "Symptom logged.")
            return redirect('dashboard')
    else:
        form = SymptomForm()
    return render(request, 'tracker/pages/add_symptom.html', {'form': form})

@login_required
def symptom_json(request):
    """ Return mood counts as JSON for charting."""
    profile = Profile.objects.get(user=request.user)
    symptoms = Symptom.objects.filter(profile=profile).order_by('date')
    mood_counts = Counter(s.mood for s in symptoms)
    return JsonResponse({'labels': list(mood_counts.keys()), 'values': list(mood_counts.values())})

# Cravings
@login_required
def add_craving(request):
    """Log a craving tied to the user's profile."""
    profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        form = CravingForm(request.POST)
        if form.is_valid():
            craving = form.save(commit=False)
            craving.profile = profile
            craving.save()
            messages.success(request, "Craving logged.")
            return redirect('dashboard')
    else:
        form = CravingForm()
    return render(request, 'tracker/pages/add_craving.html', {'form': form})

@login_required
def craving_json(request):
    """Return craving counts as JSON for charting."""
    profile = Profile.objects.get(user=request.user)
    cravings = Craving.objects.filter(profile=profile).order_by('date')
    craving_counts = Counter(c.craving_type for c in cravings)
    return JsonResponse({'labels': list(craving_counts.keys()), 'values': list(craving_counts.values())})

@login_required
def mood_cravings_json(request):
    """ Return combined counts for moods and cravings for the current user.
    JSON: { labels: [...], moods: [...], cravings: [...] }"""
    profile = Profile.objects.get(user=request.user)
    symptoms = Symptom.objects.filter(profile=profile).order_by('date')
    cravings = Craving.objects.filter(profile=profile).order_by('date')

    mood_counts = Counter(s.mood for s in symptoms)
    craving_counts = Counter(c.craving_type for c in cravings)
    labels = list(sorted(set(mood_counts.keys()) | set(craving_counts.keys())))
    moods = [mood_counts.get(l, 0) for l in labels]
    cravings_values = [craving_counts.get(l, 0) for l in labels]

    return JsonResponse({'labels': labels, 'moods': moods, 'cravings': cravings_values})

# Prompt of the day
def get_prompt_of_the_day():
    """Return a stable prompt selection based on the day of month."""
    PROMPTS = [
        "What made you smile today?",
        "What are you proud of this week?",
        "What’s something you’re letting go of?",
        "What do you need more of right now?",
        "What’s a memory that brings you peace?",
        "What’s a challenge you overcame recently?",
        "What’s something new you learned about yourself?",
        "What’s a small act of kindness you experienced?",
        "What’s a goal you’re working towards?",
        "What’s a dream you have for the future?",
        "What’s a habit you want to build?",
        "What’s a book or movie that inspired you?",
        "What’s a place you want to visit and why?",
        "What’s a skill you want to learn?",
        "What’s a person who positively impacted your life?",
        "What’s a moment when you felt truly at peace?",
        "What’s a value that’s important to you?",
        "What’s a way you can practice self-care this week?",
        "What’s a recent accomplishment you’re proud of?",
        "What’s a lesson you learned from a mistake?",
        "What’s a way you can give back to your community?",
        "What’s a way you can step out of your comfort zone?",
        "What’s a way you can nurture your creativity?",
        "What’s a way you can connect with nature?",
        "What’s a way you can strengthen a relationship?",
        "What’s a way you can simplify your life?",
        "What’s a way you can practice mindfulness?",
    ]
    index = date.today().day % len(PROMPTS)
    return PROMPTS[index]

# Diary
@login_required
def add_diary(request):
    """ Add a diary entry; if prompt answer is provided it is saved as a PromptAnswer."""
    prompt_of_the_day = get_prompt_of_the_day()
    if request.method == "POST":
        form = DiaryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            if not entry.date:
                entry.date = date.today()
            entry.save()

            answer = request.POST.get("prompt_answer")
            if answer:
                PromptAnswer.objects.create(user=request.user, prompt=prompt_of_the_day, answer=answer)

            messages.success(request, "Diary entry saved.")
            return redirect("diary_page")
    else:
        form = DiaryForm()
    return render(request, "tracker/pages/add_diary.html", {"form": form, "prompt_of_the_day": prompt_of_the_day})

@login_required
def diary_page(request):
    """ Renders the diary page with paginated diary entries, prompts, and gratitude reflections.
    Supports search filtering and emoji mapping for moods."""
    query = request.GET.get('q')
    entries = DiaryEntry.objects.filter(user=request.user)

    if query:
        entries = entries.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(short_term__icontains=query) |
            Q(medium_term__icontains=query) |
            Q(long_term__icontains=query)
        )

    entries = entries.order_by('-date')
    paginator = Paginator(entries, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Add mood emoji to each entry
    MOOD_EMOJI = {
        "Happy": "😊", "Sad": "😢", "Angry": "😠", "Tired": "😴",
        "Confused": "😕", "Loved": "❤️", "Peaceful": "🌸", "Other": "📝"
    }
    for entry in page_obj:
        entry.mood_icon = MOOD_EMOJI.get(entry.mood, "📝")

    # Paginate prompt answers
    prompt_qs = PromptAnswer.objects.filter(user=request.user).order_by('-date')
    prompt_pag = Paginator(prompt_qs, 2)
    prompt_page = request.GET.get('prompt_page')
    prompt_answers = prompt_pag.get_page(prompt_page)

    # Paginate gratitude entries
    gratitude_qs = GratitudeEntry.objects.filter(user=request.user).order_by('-date')
    gratitude_pag = Paginator(gratitude_qs, 2)
    gratitude_page = request.GET.get('gratitude_page')
    gratitude_entries = gratitude_pag.get_page(gratitude_page)

    return render(request, 'tracker/main/diary_page.html', {
        'entries': page_obj,
        'prompt_answers': prompt_answers,
        'gratitude_entries': gratitude_entries,
        'prompt_of_the_day': get_prompt_of_the_day()
    })

@login_required
def edit_diary(request, entry_id):
    """Edit an existing diary entry."""
    entry = get_object_or_404(DiaryEntry, id=entry_id, user=request.user)
    if request.method == "POST":
        form = DiaryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Diary entry updated.")
            return redirect("diary_page")
    else:
        form = DiaryForm(instance=entry)
    return render(request, "tracker/actions/edit_diary.html", {"form": form, "entry": entry})


@login_required
def delete_diary(request, entry_id):
    """Delete a diary entry for the current user."""

    entry = get_object_or_404(DiaryEntry, id=entry_id, user=request.user)
    entry.delete()
    messages.success(request, "Diary entry deleted.")
    return redirect("diary_page")

def diary_history(request):
    """View paginated diary history with optional date filtering."""

    entries = DiaryEntry.objects.filter(user=request.user).order_by('-date')

    # Optional date filtering
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    if start:
        entries = entries.filter(date__gte=start)
    if end:
        entries = entries.filter(date__lte=end)

    paginator = Paginator(entries, 5)  # Show 5 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tracker/pages/diary_history.html', {'entries': page_obj})

@login_required
def log_mood_checkin(request):
    """Log a simple mood check-in and redirect to dashboard."""
    if request.method == 'POST':
        mood = request.POST.get('mood')
        if mood:
            MoodCheckin.objects.create(user=request.user, mood=mood)
    return redirect('dashboard')

@login_required
def log_gratitude(request):
    """Quickly log a gratitude entry from the dashboard."""
    if request.method == 'POST':
        gratitude = request.POST.get('gratitude')
        if gratitude:
            GratitudeEntry.objects.create(user=request.user, content=gratitude)
    return redirect('dashboard')

@login_required
def add_prompt(request):
    """Allow the user to respond to the prompt of the day."""
    prompt_of_the_day = get_prompt_of_the_day()

    if request.method == "POST":
        form = PromptAnswerForm(request.POST)
        if form.is_valid():
            PromptAnswer.objects.create(
                user=request.user,
                prompt=form.cleaned_data['prompt'],
                answer=form.cleaned_data['answer']
            )
            messages.success(request, "Prompt saved.")
            return redirect('diary_page')
    else:
        form = PromptAnswerForm()

    return render(request, 'tracker/actions/add_prompt.html', {
        'form': form,
        'prompt_of_the_day': prompt_of_the_day
    })

@login_required
def edit_prompt(request, pk):
    """Edit a previously submitted prompt answer."""
    prompt = get_object_or_404(PromptAnswer, pk=pk, user=request.user)
    prompt_of_the_day = get_prompt_of_the_day()

    if request.method == "POST":
        form = PromptAnswerForm(request.POST, instance=prompt)
        if form.is_valid():
            form.save()
            messages.success(request, "Prompt updated.")
            return redirect('diary_page')
    else:
        form = PromptAnswerForm(instance=prompt)

    return render(request, 'tracker/actions/edit_prompt.html', {
        'form': form,
        'prompt_of_the_day': prompt_of_the_day
    })


@login_required
def delete_prompt(request, pk):
    """Delete a prompt answer for the current user."""
    prompt = get_object_or_404(PromptAnswer, pk=pk, user=request.user)
    prompt.delete()
    messages.success(request, "Prompt deleted.")
    return redirect('diary_page')

@login_required
def add_gratitude(request):
    """Add a gratitude entry."""
    if request.method == "POST":
        form = GratitudeForm(request.POST)
        if form.is_valid():
            gratitude = form.save(commit=False)
            gratitude.user = request.user
            gratitude.save()
            messages.success(request, "Gratitude saved.")
            return redirect('diary_page')
    else:
        form = GratitudeForm()
    return render(request, 'tracker/actions/add_gratitude.html', {'form': form})

@login_required
def edit_gratitude(request, pk):
    """Edit an existing gratitude entry."""
    gratitude = get_object_or_404(GratitudeEntry, pk=pk, user=request.user)
    if request.method == "POST":
        form = GratitudeForm(request.POST, instance=gratitude)
        if form.is_valid():
            form.save()
            messages.success(request, "Gratitude updated.")
            return redirect('diary_page')
    else:
        form = GratitudeForm(instance=gratitude)
    return render(request, 'tracker/actions/edit_gratitude.html', {'form': form})

@login_required
def delete_gratitude(request, pk):
    """Delete a gratitude entry."""
    gratitude = get_object_or_404(GratitudeEntry, pk=pk, user=request.user)
    gratitude.delete()
    messages.success(request, "Gratitude deleted.")
    return redirect('diary_page')

# Calendar and JSON endpoints
@login_required
def diary_entries_json(request):
    """Return diary entries as JSON for calendar usage."""
    entries = DiaryEntry.objects.filter(user=request.user).order_by('date')
    data = [{
        'id': entry.id,
        'title': entry.title or 'Diary Entry',
        'date': entry.date.strftime('%Y-%m-%d'),
        'content': entry.content
    } for entry in entries]
    return JsonResponse(data, safe=False)

# Self-care
@login_required
def selfcare(request):
    """ Show the selfcare form. If today's selfcare exists, reuse it for editing."""

    existing = SelfCareEntry.objects.filter(user=request.user).order_by('-date').first()
    instance = existing if existing and existing.date == date.today() else None

    if request.method == "POST":
        form = SelfCareForm(request.POST, instance=instance)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            messages.success(request, "Self-care entry saved.")
            return redirect("dashboard")
    else:
        form = SelfCareForm(instance=instance)

    return render(request, "tracker/pages/selfcare.html", {"form": form})

@login_required
def selfcare_tracker(request):
    """List self-care entries."""
    entries = SelfCareEntry.objects.filter(user=request.user).order_by('-date')
    return render(request, "tracker/pages/selfcare_tracker.html", {"entries": entries})

@login_required
def edit_selfcare(request, entry_id):
    """Edit an existing self-care entry."""
    entry = get_object_or_404(SelfCareEntry, id=entry_id, user=request.user)
    if request.method == "POST":
        form = SelfCareForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Self-care entry updated.")
            return redirect("selfcare_tracker")
    else:
        form = SelfCareForm(instance=entry)
    return render(request, "tracker/pages/selfcare.html", {
        "form": form,
        "entry": entry,
        "title": "Edit Self-Care Entry",
        "delete_url": "delete_selfcare"
    })

@login_required
def delete_selfcare(request, entry_id):
    """Delete a self-care entry for the user."""
    entry = get_object_or_404(SelfCareEntry, id=entry_id, user=request.user)
    entry.delete()
    messages.success(request, "Self-care entry deleted.")
    return redirect("selfcare_tracker")

# Informational pages and summary
def cycle_phases(request):
    """Render the static cycle phases information page."""
    return render(request, 'tracker/pages/cycle_phases.html')


@login_required
def wellness_update(request):
    """
    Provide a short wellness summary: latest diary and selfcare entries,
    average cycle length, most common flow type, and irregular count/trend.
    """
    user = request.user
    profile = Profile.objects.get(user=user)

    daily_affirmation = "You are strong, capable, and beautifully in tune with your body."
    latest_diary = DiaryEntry.objects.filter(user=user).order_by('-date').first()
    latest_selfcare = SelfCareEntry.objects.filter(user=user).order_by('-date').first()
    cycles = Cycle.objects.filter(user=user).order_by('-start_date')

    avg_cycle_length = None
    most_common_flow = None
    irregular_count = 0
    cycle_trend = "Stable"

    if len(cycles) >= 2:
        # Calculate cycle lengths from start dates differences
        lengths = [(cycles[i].start_date - cycles[i+1].start_date).days for i in range(len(cycles)-1)]
        avg_cycle_length = sum(lengths) // len(lengths) if lengths else None
        irregular_count = sum(1 for l in lengths if abs(l - avg_cycle_length) > 3) if avg_cycle_length else 0
        cycle_trend = "Irregular" if irregular_count > 1 else "Stable"
        flow_types = [c.flow_type for c in cycles if c.flow_type]
        most_common_flow = Counter(flow_types).most_common(1)[0][0] if flow_types else "Unknown"
    else:
        avg_cycle_length = most_common_flow = None

    context = {
        'profile': profile,
        'daily_affirmation': daily_affirmation,
        'latest_diary': latest_diary,
        'latest_selfcare': latest_selfcare,
        'avg_cycle_length': avg_cycle_length,
        'most_common_flow': most_common_flow,
        'irregular_count': irregular_count,
        'cycle_trend': cycle_trend,
    }

    return render(request, 'tracker/main/wellness_update.html', context)

# Static prompt list reused from diary
def get_diary_prompts():
    return [
        "What made you smile today?",
        "What are you proud of this week?",
        "What’s something you’re letting go of?",
        "What do you need more of right now?",
        "What’s a memory that brings you peace?",
        "What’s a challenge you overcame recently?",
        "What’s something new you learned about yourself?",
        "What’s a small act of kindness you experienced?",
        "What’s a goal you’re working towards?",
        "What’s a dream you have for the future?",
        "What’s a habit you want to build?",
        "What’s a book or movie that inspired you?",
        "What’s a place you want to visit and why?",
        "What’s a skill you want to learn?",
        "What’s a person who positively impacted your life?",
        "What’s a moment when you felt truly at peace?",
        "What’s a value that’s important to you?",
        "What’s a way you can practice self-care this week?",
        "What’s a recent accomplishment you’re proud of?",
        "What’s a lesson you learned from a mistake?",
        "What’s a way you can give back to your community?",
        "What’s a way you can step out of your comfort zone?",
        "What’s a way you can nurture your creativity?",
        "What’s a way you can connect with nature?",
        "What’s a way you can strengthen a relationship?",
        "What’s a way you can simplify your life?",
        "What’s a way you can practice mindfulness?",
    ]

# Community Page
@login_required
def community(request):
    form = CommunityCommentForm()
    prompts = CommunityPrompt.objects.filter(is_public=True).order_by('-created_at')
    static_prompts = get_diary_prompts()

    # Handle general comment submission
    if request.method == 'POST' and 'static_prompt' not in request.POST and 'custom_prompt' not in request.POST:
        form = CommunityCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.prompt = None  # General comment
            if not form.cleaned_data.get('is_anonymous', False):
                comment.user = request.user
                if not comment.name:
                    comment.name = request.user.get_full_name() or request.user.username
            else:
                comment.user = None
            comment.save()
            messages.success(request, "Comment posted.")
            return redirect('community')

    # Paginate general comments
    all_comments = CommunityComment.objects.filter(prompt__isnull=True).order_by('-created_at')
    paginator = Paginator(all_comments, 3)
    page_number = request.GET.get('page')
    comments_page = paginator.get_page(page_number)

    for comment in comments_page:
        comment.can_edit_flag = (
            request.user.is_staff or
            (comment.user == request.user and not comment.is_anonymous)
        )

    return render(request, 'tracker/main/community.html', {
        'form': form,
        'prompts': prompts,
        'static_prompts': static_prompts,
        'comments': comments_page,
    })

# Prompt Detail Page
@login_required
def prompt_detail(request, prompt_id):
    prompt = get_object_or_404(CommunityPrompt, id=prompt_id, is_public=True)

    if request.method == 'POST':
        form = CommunityCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.prompt = prompt
            if not form.cleaned_data.get('is_anonymous', False):
                comment.user = request.user
                if not comment.name:
                    comment.name = request.user.get_full_name() or request.user.username
            else:
                comment.user = None
            comment.save()
            messages.success(request, "Comment posted.")
            return redirect('prompt_detail', prompt_id=prompt.id)
    else:
        form = CommunityCommentForm()

    all_comments = prompt.comments.order_by('-created_at')
    paginator = Paginator(all_comments, 10)
    page_number = request.GET.get('page')
    comments = paginator.get_page(page_number)

    for comment in comments:
        comment.can_edit_flag = (
            request.user.is_staff or
            (comment.user == request.user and not comment.is_anonymous)
        )

    return render(request, 'tracker/actions/prompt_detail.html', {
        'prompt': prompt,
        'form': form,
        'comments': comments,
    })


# Edit Comment
@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(CommunityComment, id=comment_id)
    if not comment.can_edit(request.user):
        messages.error(request, "You can only edit your own non-anonymous comments.")
        return redirect('community')

    if request.method == 'POST':
        form = CommunityCommentForm(request.POST, instance=comment)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.is_anonymous:
                updated.user = None
            else:
                if not updated.user:
                    updated.user = request.user
            updated.save()
            messages.success(request, "Comment updated.")
            return redirect('community')
    else:
        form = CommunityCommentForm(instance=comment)

    return render(request, 'tracker/actions/edit_comment.html', {'form': form, 'comment': comment})


# Delete Comment
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(CommunityComment, id=comment_id)
    if not comment.can_edit(request.user):
        messages.error(request, "You can only delete your own non-anonymous comments.")
        return redirect('community')

    if request.method == 'POST':
        comment.delete()
        messages.success(request, "Comment deleted.")
        return redirect('community')

    return render(request, 'tracker/actions/delete_comment.html', {'comment': comment})

@login_required
def add_community_prompt(request):
    form = CommunityPromptForm()
    all_prompts = CommunityPrompt.objects.filter(is_public=True).order_by('-created_at')
    diary_prompts = get_diary_prompts()

    if request.method == 'POST':
        selected_id = request.POST.get('selected_prompt')
        if selected_id:
            return redirect('prompt_detail', prompt_id=selected_id)

        form = CommunityPromptForm(request.POST)
        if form.is_valid():
            prompt = form.save(commit=False)
            prompt.user = request.user
            prompt.is_public = True
            prompt.save()
            messages.success(request, "Prompt shared with the community.")
            return redirect('prompt_detail', prompt_id=prompt.id)

    return render(request, 'tracker/actions/add_community_prompt.html', {
        'form': form,
        'all_prompts': all_prompts,
        'diary_prompts': diary_prompts,
    })

# Goodbye Page
def goodbye(request):
    affirmations = [
        "You are enough, just as you are.",
        "Rest is productive. You deserve it.",
        "Your wellness journey is always here for you.",
        "Thank you for showing up for yourself today.",
        "You are doing better than you think.",
        "See you soon, beautiful soul"
    ]
    farewell_affirmation = random.choice(affirmations)
    return render(request, "tracker/pages/goodbye.html", {"farewell_affirmation": farewell_affirmation})
