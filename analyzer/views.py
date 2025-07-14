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


def get_client_ip(request: HttpRequest) -> str:
    """
    Get the client's IP address from the request, handling both
    direct connections and requests through proxies/load balancers.

    Args:
        request: The HTTP request object

    Returns:
        The client's IP address as a string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # In production with a proxy, the client IP is the first in the list
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # Direct connection, use REMOTE_ADDR
        ip = request.META.get('REMOTE_ADDR', '')

    return ip


def get_or_create_session_id(request: HttpRequest) -> str:
    """
    Get existing session ID or create a new one if it doesn't exist.

    Args:
        request: The HTTP request object

    Returns:
        A session identifier string
    """
    if not request.session.session_key:
        request.session.create()

    return request.session.session_key


def analyze_log(request: HttpRequest) -> HttpResponse:
    result: Optional[str] = None

    # Get both IP address and session ID
    client_ip = get_client_ip(request)
    session_id = get_or_create_session_id(request)

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

                try:
                    # Store both IP address and session ID
                    LogAnalysis.objects.create(
                        log_input=log_text,
                        ai_response=result,
                        ip_address=client_ip,
                        session_id=session_id
                    )
                except Exception as db_error:
                    print(f"Database error: {str(db_error)}")

            except Exception as e:
                result = f"Erro ao chamar a API do OpenAI: {str(e)}"

    return render(request, "analyzer/analyze_log.html", {"result": result})


def history(request: HttpRequest) -> HttpResponse:
    try:
        # Get both identifiers
        client_ip = get_client_ip(request)
        session_id = request.session.session_key  # Don't create if it doesn't exist

        # First try using IP address
        if client_ip:
            analyses = LogAnalysis.objects.filter(ip_address=client_ip).order_by('-created_at')
            if analyses.exists():
                return render(request, "analyzer/history.html", {"analyses": analyses})

        # Fallback to session ID if available and IP didn't yield results
        if session_id:
            analyses = LogAnalysis.objects.filter(session_id=session_id).order_by('-created_at')
            if analyses.exists():
                return render(request, "analyzer/history.html", {"analyses": analyses})

        # If we reach here, no analyses were found by either method
        return render(request, "analyzer/history.html",
                      {"analyses": [], "message": "Nenhuma análise encontrada no histórico."})

    except Exception as e:
        print(f"Error in history view: {str(e)}")
        return render(request, "analyzer/history.html",
                      {"analyses": [], "error": "Não foi possível carregar o histórico."})