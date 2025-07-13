from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest, HttpResponse
import openai
from typing import Optional
from .models import LogAnalysis


def build_prompt(log_text: str) -> str:
    """
    Build a prompt for the AI to analyze a Django/Python error log.

    Args:
        log_text: The error log text to analyze

    Returns:
        A formatted prompt string for the AI model
    """
    return f"""
Você é um engenheiro de software experiente. Abaixo está um log de erro Python/Django.

Sua tarefa é analisar o log e retornar um relatório com:
1. ERRO IDENTIFICADO: Um resumo em uma linha do erro principal.
2. EXPLICAÇÃO: O que significa este erro?
3. POSSÍVEIS CAUSAS: 2-3 razões pelas quais isso pode acontecer.
4. SUGESTÕES: Como corrigir ou investigar o problema.

Por favor, responda em português.

Log:
{log_text.strip()}
"""


def analyze_log(request: HttpRequest) -> HttpResponse:
    """
    View function to analyze Django/Python error logs using AI.

    This function handles both GET and POST requests:
    - GET: Displays the empty form
    - POST: Processes the submitted log, sends it to OpenAI for analysis,
            saves the analysis to the database with user's IP, and displays the result

    Args:
        request: The HTTP request object

    Returns:
        Rendered HTML response with analysis result if available
    """
    result: Optional[str] = None

    if request.method == "POST":
        log_text = request.POST.get("log_text")
        if log_text:
            openai.api_key = settings.OPENAI_API_KEY
            prompt = build_prompt(log_text)
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Você é um desenvolvedor backend sênior. Responda em português."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=1000
                )
                result = response['choices'][0]['message']['content']

                # Get client IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')

                LogAnalysis.objects.create(
                    log_input=log_text,
                    ai_response=result,
                    ip_address=ip_address
                )

            except Exception as e:
                result = f"Erro ao chamar a API do OpenAI: {str(e)}"

    return render(request, "analyzer/analyze_log.html", {"result": result})


def history(request: HttpRequest) -> HttpResponse:
    """
    View function to display the history of log analyses for the current user.

    Shows a list of previously analyzed logs submitted from the user's IP address,
    ordered by most recent first.

    Args:
        request: The HTTP request object

    Returns:
        Rendered HTML response with the log analysis history
    """
    # Get client IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    # Filter analyses by the user's IP address
    analyses = LogAnalysis.objects.filter(ip_address=ip_address).order_by('-created_at')

    return render(request, "analyzer/history.html", {"analyses": analyses})