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


import hashlib
import uuid


def get_or_create_user_id(request: HttpRequest) -> str:
    """
    Generate or retrieve a persistent user identifier using cookies.

    Args:
        request: The HTTP request object

    Returns:
        A unique user identifier string
    """
    user_id = request.COOKIES.get('user_id')

    # Return existing ID if found
    if user_id:
        return user_id

    # No cookie found, this will be set in the response
    return str(uuid.uuid4())


def analyze_log(request: HttpRequest) -> HttpResponse:
    result: Optional[str] = None
    user_id = get_or_create_user_id(request)

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
                    LogAnalysis.objects.create(
                        log_input=log_text,
                        ai_response=result,
                        ip_address=user_id  # Store the user_id in the ip_address field
                    )
                except Exception as db_error:
                    print(f"Database error: {str(db_error)}")

            except Exception as e:
                result = f"Erro ao chamar a API do OpenAI: {str(e)}"

    response = render(request, "analyzer/analyze_log.html", {"result": result})

    # Set cookie if it doesn't exist
    if not request.COOKIES.get('user_id'):
        response.set_cookie('user_id', user_id, max_age=31536000)  # 1 year

    return response


def history(request: HttpRequest) -> HttpResponse:
    try:
        # First try to get user_id from cookie
        user_id = request.COOKIES.get('user_id')

        if user_id:
            # Filter analyses by the user_id stored in ip_address field
            analyses = LogAnalysis.objects.filter(ip_address=user_id).order_by('-created_at')
        else:
            # Fallback to IP address if no cookie is found
            ip = get_client_ip(request)
            if ip:
                analyses = LogAnalysis.objects.filter(ip_address=ip).order_by('-created_at')
            else:
                # If neither cookie nor IP is available, return empty list
                analyses = LogAnalysis.objects.none()

        return render(request, "analyzer/history.html", {"analyses": analyses})
    except Exception as e:
        print(f"Error in history view: {str(e)}")
        return render(request, "analyzer/history.html",
                      {"analyses": [], "error": "Não foi possível carregar o histórico."})