from django.contrib import admin
from .models import (
    Profile,
    Cycle,
    FlowDay,
    Symptom,
    Craving,
    DiaryEntry,
    PromptAnswer,
    GratitudeEntry,
    SelfCareEntry,
    CommunityPrompt,
    CommunityComment,
    MoodCheckin
)

admin.site.register(Profile)
admin.site.register(Cycle)
admin.site.register(FlowDay)
admin.site.register(Symptom)
admin.site.register(Craving)
admin.site.register(DiaryEntry)
admin.site.register(PromptAnswer)
admin.site.register(GratitudeEntry)
admin.site.register(SelfCareEntry)
admin.site.register(CommunityPrompt)
admin.site.register(CommunityComment)
admin.site.register(MoodCheckin)
