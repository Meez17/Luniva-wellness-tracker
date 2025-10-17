from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('goodbye/', views.goodbye, name='goodbye'),

    path('signup/', views.sign_up, name='sign_up'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='tracker/registration/login.html'), name='account_login'),    path('logout/', auth_views.LogoutView.as_view(next_page='goodbye'), name='logout'),
    path('welcome/', views.welcome, name='welcome'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('wellness-update/', views.wellness_update, name='wellness_update'),
    path('cycle-phases/', views.cycle_phases, name='cycle_phases'),

    path('profile/', views.profile, name='profile'),

    path('add_cycle/', views.add_cycle, name='add_cycle'),
    path('add_flow_day/', views.add_flow_day, name='add_flow_day'),

    path('flow_day_json/', views.flow_day_json, name='flow_day_json'),
    path('api/flow-days/', views.flow_day_json, name='api_flow_days'),
    path('cycles_json/', views.cycles_json, name='cycles_json'),
    path('api/cycles/', views.cycles_json, name='api_cycles'),
    path('api/mood-cravings/', views.mood_cravings_json, name='mood_cravings_json'),

    path('add_symptom/', views.add_symptom, name='add_symptom'),
    path('symptom_json/', views.symptom_json, name='symptom_json'),
    path('add_craving/', views.add_craving, name='add_craving'),
    path('craving_json/', views.craving_json, name='craving_json'),

    path('diary/', views.diary_page, name='diary_page'),
    path('diary/add/', views.add_diary, name='add_diary'),
    path('diary/edit/<int:entry_id>/', views.edit_diary, name='edit_diary'),
    path('diary/delete/<int:entry_id>/', views.delete_diary, name='delete_diary'),
    path('diary/history/', views.diary_history, name='diary_history'),
    path('diary_entries_json/', views.diary_entries_json, name='diary_entries_json'),

    path('diary/log-mood/', views.log_mood_checkin, name='log_mood_checkin'),
    path('diary/log-gratitude/', views.log_gratitude, name='log_gratitude'),

    path('prompt/add/', views.add_prompt, name='add_prompt'),
    path('prompt/<int:pk>/edit/', views.edit_prompt, name='edit_prompt'),
    path('prompt/<int:pk>/delete/', views.delete_prompt, name='delete_prompt'),

    path('gratitude/add/', views.add_gratitude, name='add_gratitude'),
    path('gratitude/<int:pk>/edit/', views.edit_gratitude, name='edit_gratitude'),
    path('gratitude/<int:pk>/delete/', views.delete_gratitude, name='delete_gratitude'),

    path('selfcare/', views.selfcare, name='selfcare'),
    path('selfcare/history/', views.selfcare_tracker, name='selfcare_tracker'),
    path('selfcare/edit/<int:entry_id>/', views.edit_selfcare, name='edit_selfcare'),
    path('selfcare/delete/<int:entry_id>/', views.delete_selfcare, name='delete_selfcare'),

    path('search/', views.site_search, name='site_search'),

    path('community/', views.community, name='community'),
    path('community/add_prompt/', views.add_community_prompt, name='add_community_prompt'),
    path('community/prompt/<int:prompt_id>/', views.prompt_detail, name='prompt_detail'),
    path('community/comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('community/comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
]

