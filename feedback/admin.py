from django.contrib import admin

from .models import Feedback, EpisodeFeedbackPrompt

admin.site.register(Feedback)
admin.site.register(EpisodeFeedbackPrompt)
