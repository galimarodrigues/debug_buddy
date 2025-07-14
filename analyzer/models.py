from django.db import models


class LogAnalysis(models.Model):
    log_input = models.TextField()
    ai_response = models.TextField()
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    session_id = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Log Analyses"