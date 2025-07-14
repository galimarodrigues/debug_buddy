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


def analyze_log(request: HttpRequest) -> HttpResponse:
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

                # Get client IP address using the utility function
                ip_address = get_client_ip(request)

                try:
                    LogAnalysis.objects.create(
                        log_input=log_text,
                        ai_response=result,
                        ip_address=ip_address
                    )
                except Exception as db_error:
                    # Log the database error but don't fail the request
                    print(f"Database error: {str(db_error)}")
                    # Continue with the response even if saving to DB fails

            except Exception as e:
                result = f"Erro ao chamar a API do OpenAI: {str(e)}"

    return render(request, "analyzer/analyze_log.html", {"result": result})


def history(request: HttpRequest) -> HttpResponse:
    try:
        # Get client IP address using the utility function
        ip_address = get_client_ip(request)

        # If we have no IP address, return empty list
        if not ip_address:
            return render(request, "analyzer/history.html",
                          {"analyses": [], "error": "Não foi possível identificar seu endereço IP."})

        # Filter analyses by the user's IP address
        analyses = LogAnalysis.objects.filter(ip_address=ip_address).order_by('-created_at')

        return render(request, "analyzer/history.html", {"analyses": analyses})
    except Exception as e:
        # Log the error but return an empty analyses list
        print(f"Error in history view: {str(e)}")
        return render(request, "analyzer/history.html",
                      {"analyses": [], "error": "Não foi possível carregar o histórico."})