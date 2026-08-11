from django.db import models

# Create your models here.
class Report(models.Model):
    accused_id = models.CharField(max_length=100, unique=True)
    overall_result = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True) 
    video_prediction = models.CharField(max_length=50)
    audio_prediction = models.CharField(max_length=50)
    linguistic_analysis = models.CharField(max_length=50)
    detailed_report = models.JSONField() 
    # New fields for scenario and questions
    scenario = models.TextField(blank=True, null=True)
    questions = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"Report {self.id} - {self.accused_id} at {self.timestamp}"