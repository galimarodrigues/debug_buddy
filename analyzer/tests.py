from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.http import HttpResponse
from typing import List, Optional, Any
from unittest.mock import patch, MagicMock
from .models import LogAnalysis
from .views import build_prompt


class LogAnalysisModelTests(TestCase):
    """Test suite for the LogAnalysis model."""

    def test_log_analysis_creation(self) -> None:
        """
        Test creating a LogAnalysis instance with all fields.

        Ensures that a LogAnalysis object can be created with the expected
        field values and that the created_at timestamp is automatically set.
        """
        log_analysis = LogAnalysis.objects.create(
            log_input="Test log input",
            ai_response="Test AI response",
            ip_address="127.0.0.1"
        )

        self.assertEqual(log_analysis.log_input, "Test log input")
        self.assertEqual(log_analysis.ai_response, "Test AI response")
        self.assertEqual(log_analysis.ip_address, "127.0.0.1")
        self.assertIsNotNone(log_analysis.created_at)

    def test_str_method(self) -> None:
        """
        Test the string representation of LogAnalysis objects.

        Verifies that the __str__ method returns a string containing the
        analysis ID, ensuring proper object representation in admin and debug contexts.
        """
        log_analysis = LogAnalysis.objects.create(
            log_input="Test log",
            ai_response="Test response",
            ip_address="127.0.0.1"
        )

        self.assertIn(f"Análise #{log_analysis.id}", str(log_analysis))


class BuildPromptTests(TestCase):
    """Test suite for the build_prompt function."""

    def test_build_prompt(self) -> None:
        """
        Test the build_prompt function formats the log text correctly.

        Ensures that the function properly embeds the log text within
        the AI prompt template and includes all necessary instructions.
        """
        log_text = "ImportError: No module named 'django'"
        prompt = build_prompt(log_text)

        self.assertIn("Você é um engenheiro de software experiente", prompt)
        self.assertIn("Abaixo está um log de erro Python/Django", prompt)
        self.assertIn(log_text, prompt)


class AnalyzeLogViewTests(TestCase):
    """Test suite for the analyze_log view function."""

    def setUp(self) -> None:
        """
        Set up test environment before each test.

        Initializes a test client and request factory for simulating
        HTTP requests to the view.
        """
        self.client = Client()
        self.factory = RequestFactory()

    def test_analyze_log_get(self) -> None:
        """
        Test the analyze_log view returns the correct template on GET request.

        Verifies that:
        - The view returns a 200 OK status
        - The correct template is used
        - The result context variable is None for GET requests
        """
        response = self.client.get(reverse('analyze_log'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analyzer/analyze_log.html')
        self.assertIsNone(response.context['result'])

    @patch('openai.ChatCompletion.create')
    def test_analyze_log_post(self, mock_openai: MagicMock) -> None:
        """
        Test the analyze_log view processes logs and saves analysis.

        This test:
        - Mocks the OpenAI API response
        - Sends a POST request with a sample log text
        - Verifies the response contains the mocked AI result
        - Confirms the analysis is saved to the database with the correct fields
        - Checks that an IP address is captured

        Args:
            mock_openai: Mocked OpenAI API function
        """
        # Mock the OpenAI API response
        mock_response = {
            'choices': [
                {
                    'message': {
                        'content': 'Mocked AI response'
                    }
                }
            ]
        }
        mock_openai.return_value = mock_response

        # Send a POST request with log text
        response = self.client.post(
            reverse('analyze_log'),
            {'log_text': 'Test error log'}
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['result'], 'Mocked AI response')

        # Check that the analysis was saved in the database
        log_analysis = LogAnalysis.objects.last()
        self.assertEqual(log_analysis.log_input, 'Test error log')
        self.assertEqual(log_analysis.ai_response, 'Mocked AI response')
        self.assertIsNotNone(log_analysis.ip_address)

    @patch('openai.ChatCompletion.create')
    def test_analyze_log_error_handling(self, mock_openai: MagicMock) -> None:
        """
        Test error handling in analyze_log view when the API call fails.

        This test:
        - Makes the OpenAI API mock raise an exception
        - Verifies the view returns an error message
        - Confirms no record is saved to the database in case of API errors

        Args:
            mock_openai: Mocked OpenAI API function set to raise an exception
        """
        # Make the OpenAI API raise an exception
        mock_openai.side_effect = Exception("API Error")

        # Send a POST request with log text
        response = self.client.post(
            reverse('analyze_log'),
            {'log_text': 'Test error log'}
        )

        # Check the error message is returned
        self.assertEqual(response.status_code, 200)
        self.assertIn("Erro ao chamar a API do OpenAI", response.context['result'])

        # No analysis should be saved
        self.assertEqual(LogAnalysis.objects.count(), 0)


class HistoryViewTests(TestCase):
    """Test suite for the history view function."""

    def setUp(self) -> None:
        """
        Set up test environment before each test.

        Creates test data with different IP addresses to verify
        the filtering behavior of the history view.
        """
        self.client = Client()

        # Create test data with different IP addresses
        LogAnalysis.objects.create(
            log_input="Test log 1",
            ai_response="Test response 1",
            ip_address="127.0.0.1"
        )
        LogAnalysis.objects.create(
            log_input="Test log 2",
            ai_response="Test response 2",
            ip_address="127.0.0.1"
        )
        LogAnalysis.objects.create(
            log_input="Test log 3",
            ai_response="Test response 3",
            ip_address="192.168.1.1"  # Different IP
        )

    def test_history_view_filters_by_ip(self) -> None:
        """
        Test the history view only shows logs from the current user's IP.

        Verifies that:
        - The view returns the correct status code
        - Only logs with the specified IP address are included in the response
        - The correct number of logs is returned
        """
        response = self.client.get(
            reverse('history'),
            REMOTE_ADDR='127.0.0.1'
        )

        self.assertEqual(response.status_code, 200)
        analyses = response.context['analyses']
        self.assertEqual(len(analyses), 2)
        for analysis in analyses:
            self.assertEqual(analysis.ip_address, '127.0.0.1')

    def test_history_view_with_forwarded_ip(self) -> None:
        """
        Test the history view works with X-Forwarded-For header.

        Confirms that:
        - The view correctly processes the X-Forwarded-For header
        - Only logs from the IP in the header are included
        - The proper filtering is applied even with multiple IPs in the header
        """
        response = self.client.get(
            reverse('history'),
            HTTP_X_FORWARDED_FOR='192.168.1.1, 10.0.0.1'
        )

        # Check that only analyses from this IP are included
        self.assertEqual(response.status_code, 200)
        analyses = response.context['analyses']
        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].ip_address, '192.168.1.1')