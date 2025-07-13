# 🧠 Debug Buddy — IA para Análise de Logs Python/Django

## 🎯 Objetivo do Projeto

Criar um agente de IA que auxilie desenvolvedores fullstack a identificar e interpretar logs de erro em aplicações Python/Django, economizando tempo, melhorando a compreensão de exceções e sugerindo possíveis soluções.

## 🔍 Problema Identificado

Desenvolvedores frequentemente perdem tempo tentando entender logs de erro complexos, especialmente quando envolvem stacktraces extensos, erros de template ou problemas em queries.

O Debug Buddy resolve isso analisando o log com IA e retornando:
- Resumo do erro
- Explicação técnica
- Causas prováveis
- Sugestões de solução

## ⚙️ Como Funciona

1. O usuário cola um log no campo da interface.
2. O sistema envia o log para a API da OpenAI com um prompt cuidadosamente construído.
3. A resposta da IA é exibida diretamente ao usuário.
4. Cada análise é salva no banco de dados.

## 🤖 Prompt Utilizado

```
Você é um engenheiro de software experiente. Abaixo está um log de erro Python/Django.

Sua tarefa é analisar o log e retornar um relatório com:
1. ERRO IDENTIFICADO: Um resumo em uma linha do erro principal.
2. EXPLICAÇÃO: O que significa este erro?
3. POSSÍVEIS CAUSAS: 2-3 razões pelas quais isso pode acontecer.
4. SUGESTÕES: Como corrigir ou investigar o problema.

Por favor, responda em português.

Log:
[log_here]
```

O prompt foi projetado para ser claro, direto e focado em retorno útil e acionável.

## 🧱 Stack Utilizada

- **Backend**: Python + Django
- **Frontend**: Django Templates (HTML/CSS/JS)
- **IA**: OpenAI API (GPT-4)
- **Banco de Dados**: SQLite (padrão do Django)

## 🛠️ Como a IA Ajudou no Desenvolvimento

- Refinar prompts
- Corrigir exceções no Django
- Sugerir estrutura de pastas
- Criar layout clean para a UI

## 💡 Desafios Enfrentados

| Desafio | Solução |
|---------|---------|
| Excesso de retorno da API | Ajustei max_tokens e refinei o prompt |
| Layout inicial mal posicionado | Reescrevi o CSS para uma estrutura responsiva e centralizada |
| Entendimento dos requisitos do desafio | Estruturei a entrega com base no enunciado e critérios |

## 📎 Entregáveis

- Web App funcional com interface limpa
- Armazenamento de logs analisados
- Prompt bem estruturado
- Código organizado
- Documentação (este arquivo)

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passos para Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/debug-buddy.git
   cd debug-buddy
   ```

2. Crie e ative um ambiente virtual:
   ```
   python -m venv venv
   venv\Scripts\activate  # No Windows
   source venv/bin/activate  # No Linux/Mac
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Crie um arquivo `.env` na raiz do projeto com sua chave da API OpenAI:
   ```
   OPENAI_API_KEY=sua-chave-api-aqui
   ```

5. Execute as migrações do banco de dados:
   ```
   python manage.py migrate
   ```

6. Inicie o servidor de desenvolvimento:
   ```
   python manage.py runserver
   ```

7. Acesse a aplicação em seu navegador:
   ```
   http://127.0.0.1:8000/
   ```

## 📋 Uso da Aplicação

1. Na página inicial, cole o log de erro que deseja analisar no campo de texto.
2. Clique no botão "Analisar" para enviar o log para processamento.
3. Aguarde a resposta da IA, que será exibida na tela.
4. Para ver o histórico de análises anteriores, clique em "Histórico" na barra de navegação.

## 🔄 Exemplos de Uso

A aplicação inclui um botão "Exemplo" que insere automaticamente um log de erro de exemplo para demonstração.

## 🧪 Testes Unitários

O projeto inclui testes unitários abrangentes para garantir a qualidade e o funcionamento correto da aplicação. Os testes cobrem:

### Componentes Testados

- **Modelo LogAnalysis**: Testes para criação e representação de string do modelo
- **Função build_prompt**: Testes para garantir a formatação correta do prompt
- **View analyze_log**: Testes para requisições GET e POST, incluindo mock da API OpenAI e tratamento de erros
- **View history**: Testes para filtragem por endereço IP e suporte ao cabeçalho X-Forwarded-For

### Executando os Testes

Para executar todos os testes:

```
python manage.py test
```

Para executar testes específicos:

```
python manage.py test analyzer.tests.LogAnalysisModelTests
python manage.py test analyzer.tests.AnalyzeLogViewTests
```

### Cobertura de Testes

Os testes foram desenvolvidos para cobrir os principais fluxos da aplicação, incluindo:
- Criação e validação de modelos
- Formatação de prompts
- Processamento de requisições
- Integração com a API OpenAI (com mocks)
- Filtragem de dados por IP
- Tratamento de erros