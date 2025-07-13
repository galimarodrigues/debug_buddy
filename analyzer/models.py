from django.db import models


class LogAnalysis(models.Model):
    log_input = models.TextField(verbose_name="Log")
    ai_response = models.TextField(verbose_name="Resposta da IA")
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(verbose_name="Endereço IP", null=True, blank=True)

    def __str__(self):
        return f"Análise #{self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"