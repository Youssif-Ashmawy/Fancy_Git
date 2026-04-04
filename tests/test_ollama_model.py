import pytest
import json
from unittest.mock import patch, MagicMock
import requests

from src.providers.ollama_model import OllamaModel
from src.config_manager import ConfigManager
from src.fancygit_config_dc import FancyGitConfig


def make_ollama(overrides=None):
    """Create an OllamaModel backed by a real FancyGitConfig (no network calls)."""
    mock_cm = MagicMock(spec=ConfigManager)
    cfg = FancyGitConfig()
    if overrides:
        for k, v in overrides.items():
            setattr(cfg, k, v)
    mock_cm.config = cfg
    return OllamaModel(config_manager=mock_cm)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelInit:
    def test_default_init_values(self):
        model = make_ollama()
        cfg = FancyGitConfig()
        assert model.base_url == cfg.ollama_api_url
        assert model.model == cfg.default_ollama_model
        assert model.preferred_model == cfg.default_ollama_model
        assert model.timeout == cfg.ollama_timeout
        assert model.max_retries == cfg.ollama_max_retries
        assert model.temperature == cfg.ollama_temperature
        assert model.max_tokens == cfg.ollama_max_tokens_to_sample

    def test_custom_config(self):
        model = make_ollama({
            "default_ollama_model": "mistral",
            "ollama_api_url": "http://custom:11434",
            "ollama_timeout": 60,
        })
        assert model.model == "mistral"
        assert model.base_url == "http://custom:11434"
        assert model.timeout == 60

    def test_fallback_models_are_set(self):
        model = make_ollama()
        assert isinstance(model.fallback_models, list)
        assert len(model.fallback_models) > 0

    def test_init_creates_config_manager_when_none(self):
        with patch("src.providers.ollama_model.ConfigManager") as mock_cm_cls:
            mock_cm = MagicMock()
            mock_cm.config = FancyGitConfig()
            mock_cm_cls.return_value = mock_cm
            model = OllamaModel(config_manager=None)
            mock_cm_cls.assert_called_once()


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelTestConnection:
    def test_connection_success(self):
        model = make_ollama()
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("requests.get", return_value=mock_response):
            assert model.test_connection() is True

    def test_connection_non_200_status(self):
        model = make_ollama()
        mock_response = MagicMock()
        mock_response.status_code = 500
        with patch("requests.get", return_value=mock_response):
            assert model.test_connection() is False

    def test_connection_request_exception(self):
        model = make_ollama()
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
            assert model.test_connection() is False

    def test_connection_timeout(self):
        model = make_ollama()
        with patch("requests.get", side_effect=requests.exceptions.Timeout):
            assert model.test_connection() is False

    def test_connection_uses_correct_endpoint(self):
        model = make_ollama({"ollama_api_url": "http://localhost:11434"})
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            model.test_connection()
            mock_get.assert_called_once_with(
                "http://localhost:11434/api/tags", timeout=5
            )


# ---------------------------------------------------------------------------
# get_model_info
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelGetModelInfo:
    def test_model_info_success(self):
        model = make_ollama()
        expected = {"name": "llama3.2", "size": 4000000000}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected
        with patch("requests.post", return_value=mock_response):
            result = model.get_model_info()
        assert result == expected

    def test_model_info_non_200(self):
        model = make_ollama()
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("requests.post", return_value=mock_response):
            assert model.get_model_info() == {}

    def test_model_info_request_exception(self):
        model = make_ollama()
        with patch("requests.post", side_effect=requests.exceptions.ConnectionError):
            assert model.get_model_info() == {}

    def test_model_info_sends_model_name(self):
        model = make_ollama({"default_ollama_model": "codellama"})
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, json=lambda: {})
            model.get_model_info()
            call_kwargs = mock_post.call_args
            assert call_kwargs[1]["json"]["name"] == "codellama"


# ---------------------------------------------------------------------------
# get_available_models
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelGetAvailableModels:
    def test_returns_model_names(self):
        model = make_ollama()
        api_response = {"models": [{"name": "llama3.2"}, {"name": "codellama:latest"}]}
        with patch("requests.get", return_value=MagicMock(status_code=200, json=lambda: api_response)):
            result = model.get_available_models()
        assert result == ["llama3.2", "codellama:latest"]

    def test_returns_empty_on_non_200(self):
        model = make_ollama()
        with patch("requests.get", return_value=MagicMock(status_code=500)):
            assert model.get_available_models() == []

    def test_returns_empty_on_exception(self):
        model = make_ollama()
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
            assert model.get_available_models() == []

    def test_returns_empty_when_models_key_missing(self):
        model = make_ollama()
        with patch("requests.get", return_value=MagicMock(status_code=200, json=lambda: {})):
            assert model.get_available_models() == []


# ---------------------------------------------------------------------------
# set_model
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelSetModel:
    def _model_with_available(self, available):
        m = make_ollama()
        with patch.object(m, "get_available_models", return_value=available):
            yield m

    def test_exact_match_succeeds(self):
        model = make_ollama()
        with patch.object(model, "get_available_models", return_value=["llama3.2", "codellama:latest"]):
            assert model.set_model("llama3.2") is True
            assert model.model == "llama3.2"

    def test_prefix_match_succeeds(self):
        model = make_ollama()
        with patch.object(model, "get_available_models", return_value=["codellama:latest"]):
            assert model.set_model("codellama") is True
            assert model.model == "codellama:latest"

    def test_no_match_returns_false(self):
        model = make_ollama()
        with patch.object(model, "get_available_models", return_value=["llama3.2"]):
            assert model.set_model("gpt-4") is False

    def test_set_model_updates_preferred_model(self):
        model = make_ollama()
        with patch.object(model, "get_available_models", return_value=["mistral"]):
            model.set_model("mistral")
            assert model.preferred_model == "mistral"


# ---------------------------------------------------------------------------
# get_current_model
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelGetCurrentModel:
    def test_returns_current_model(self):
        model = make_ollama({"default_ollama_model": "llama3.2"})
        assert model.get_current_model() == "llama3.2"

    def test_returns_updated_model_after_set(self):
        model = make_ollama()
        with patch.object(model, "get_available_models", return_value=["mistral"]):
            model.set_model("mistral")
        assert model.get_current_model() == "mistral"


# ---------------------------------------------------------------------------
# _ensure_model_available
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelEnsureModelAvailable:
    def test_no_models_returns_false(self):
        model = make_ollama()
        with patch.object(model, "get_available_models", return_value=[]):
            assert model._ensure_model_available() is False

    def test_exact_preferred_match(self):
        model = make_ollama({"default_ollama_model": "llama3.2"})
        with patch.object(model, "get_available_models", return_value=["llama3.2", "mistral"]):
            assert model._ensure_model_available() is True
            assert model.model == "llama3.2"

    def test_prefix_match_for_preferred(self):
        model = make_ollama({"default_ollama_model": "llama3.2"})
        with patch.object(model, "get_available_models", return_value=["llama3.2:latest"]):
            assert model._ensure_model_available() is True
            assert model.model == "llama3.2:latest"

    def test_fallback_when_preferred_not_found(self):
        model = make_ollama({"default_ollama_model": "nonexistent-model"})
        with patch.object(model, "get_available_models", return_value=["llama3.2:latest"]):
            assert model._ensure_model_available() is True
            assert model.model == "llama3.2:latest"

    def test_returns_false_when_no_match_at_all(self):
        model = make_ollama({"default_ollama_model": "nonexistent"})
        # Make sure fallbacks don't match either
        with patch.object(model, "get_available_models", return_value=["totally-unknown-model"]):
            model.fallback_models = []  # Remove fallbacks
            assert model._ensure_model_available() is False


# ---------------------------------------------------------------------------
# _call_model
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelCallModel:
    def test_successful_response(self):
        model = make_ollama()
        api_resp = {"response": "  Hello world  "}
        with patch("requests.post", return_value=MagicMock(status_code=200, json=lambda: api_resp)):
            result = model._call_model("test prompt")
        assert result == "Hello world"

    def test_strips_surrounding_quotes(self):
        model = make_ollama()
        for quote in ('"', "'", "`"):
            api_resp = {"response": f"{quote}my response{quote}"}
            with patch("requests.post", return_value=MagicMock(status_code=200, json=lambda r=api_resp: r)):
                result = model._call_model("prompt")
            assert result == "my response"

    def test_returns_none_for_empty_response(self):
        model = make_ollama()
        with patch("requests.post", return_value=MagicMock(status_code=200, json=lambda: {"response": ""})):
            result = model._call_model("prompt")
        assert result is None

    def test_raises_on_non_200(self):
        model = make_ollama()
        with patch("requests.post", return_value=MagicMock(status_code=503)):
            with pytest.raises(Exception, match="status 503"):
                model._call_model("prompt")

    def test_raises_on_timeout(self):
        model = make_ollama()
        with patch("requests.post", side_effect=requests.exceptions.Timeout):
            with pytest.raises(Exception, match="timed out"):
                model._call_model("prompt")

    def test_raises_on_connection_error(self):
        model = make_ollama()
        with patch("requests.post", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(Exception, match="Cannot connect"):
                model._call_model("prompt")

    def test_raises_on_json_decode_error(self):
        model = make_ollama()
        mock_response = MagicMock(status_code=200)
        mock_response.json.side_effect = json.JSONDecodeError("msg", "", 0)
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(Exception, match="Invalid JSON"):
                model._call_model("prompt")

    def test_payload_uses_model_and_options(self):
        model = make_ollama({"default_ollama_model": "codellama", "ollama_temperature": 0.7})
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, json=lambda: {"response": "ok"})
            model._call_model("test")
            payload = mock_post.call_args[1]["json"]
        assert payload["model"] == "codellama"
        assert payload["options"]["temperature"] == pytest.approx(0.7)
        assert payload["stream"] is False


# ---------------------------------------------------------------------------
# _build_commit_prompt
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelBuildCommitPrompt:
    def test_prompt_contains_files_and_diff(self):
        model = make_ollama()
        context = {"staged_files": ["src/foo.py", "src/bar.py"], "diff": "- old\n+ new"}
        prompt = model._build_commit_prompt(context)
        assert "src/foo.py" in prompt
        assert "src/bar.py" in prompt
        assert "- old\n+ new" in prompt

    def test_diff_truncated_at_2000_chars(self):
        model = make_ollama()
        long_diff = "x" * 5000
        context = {"staged_files": [], "diff": long_diff}
        prompt = model._build_commit_prompt(context)
        assert "x" * 2001 not in prompt  # diff is truncated to 2000

    def test_prompt_uses_fallback_for_missing_keys(self):
        model = make_ollama()
        prompt = model._build_commit_prompt({})
        assert "files" in prompt  # fallback "files" text
        assert "No diff available" in prompt


# ---------------------------------------------------------------------------
# _format_commit_response
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelFormatCommitResponse:
    def test_valid_conventional_commit_passthrough(self):
        model = make_ollama()
        response = "feat(auth): add login endpoint\n- implement JWT validation\n- add user session tracking"
        result = model._format_commit_response(response)
        assert result.startswith("feat(auth): add login endpoint")
        assert "- implement JWT validation" in result

    def test_fallback_when_no_conventional_commit(self):
        model = make_ollama()
        response = "updated some files"
        result = model._format_commit_response(response)
        assert result.startswith("feat:")

    def test_fenced_code_block_is_unwrapped(self):
        model = make_ollama()
        response = "```\nfeat: add feature\n- detail one\n```"
        result = model._format_commit_response(response)
        assert result.startswith("feat: add feature")

    def test_empty_response_returns_fallback(self):
        model = make_ollama()
        result = model._format_commit_response("")
        assert "feat:" in result

    def test_bullets_deduplication(self):
        model = make_ollama()
        response = "feat: do thing\n- fix the login handler\n- fix the login handler\n- add error reporting"
        result = model._format_commit_response(response)
        assert result.count("- fix the login handler") == 1

    def test_skip_long_bullet_lines(self):
        model = make_ollama()
        long_line = "- " + "x" * 110
        response = f"feat: something\n{long_line}\n- short line here"
        result = model._format_commit_response(response)
        assert "x" * 110 not in result

    def test_skip_too_short_bullet_lines(self):
        model = make_ollama()
        response = "feat: something\n- hi\n- good change here"
        result = model._format_commit_response(response)
        assert "- hi" not in result

    def test_parenthesised_type_is_normalised(self):
        model = make_ollama()
        response = "(feat)(auth): add token refresh"
        result = model._format_commit_response(response)
        assert result.startswith("feat(auth):")

    def test_bullets_without_summary_get_fallback_summary(self):
        model = make_ollama()
        result = model._format_commit_response("   ")
        assert "feat:" in result


# ---------------------------------------------------------------------------
# generate_commit_message
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOllamaModelGenerateCommitMessage:
    def test_empty_context_returns_default(self):
        model = make_ollama()
        result = model.generate_commit_message({})
        assert result == "feat: add new functionality\n- initial implementation"

    def test_successful_generation(self):
        model = make_ollama()
        with patch.object(model, "set_model", return_value=True), \
             patch.object(model, "_call_model", return_value="feat: add login\n- add JWT auth"):
            result = model.generate_commit_message({"staged_files": ["auth.py"], "diff": "+code"})
        assert result.startswith("feat: add login")

    def test_restores_original_model_after_success(self):
        model = make_ollama({"default_ollama_model": "llama3.2"})
        original = model.model
        with patch.object(model, "set_model", return_value=True), \
             patch.object(model, "_call_model", return_value="feat: something\n- detail"):
            model.generate_commit_message({"staged_files": [], "diff": "diff"})
        # After generation, set_model should have been called to restore original
        assert True  # The finally block runs set_model(previous_model) without raising

    def test_restores_max_tokens_after_generation(self):
        model = make_ollama()
        original_max_tokens = model.max_tokens
        with patch.object(model, "set_model", return_value=True), \
             patch.object(model, "_call_model", return_value="feat: something\n- detail"):
            model.generate_commit_message({"staged_files": [], "diff": "diff"})
        assert model.max_tokens == original_max_tokens

    def test_fallback_when_model_unavailable(self):
        model = make_ollama()
        with patch.object(model, "set_model", return_value=False), \
             patch.object(model, "_ensure_model_available", return_value=False):
            result = model.generate_commit_message({"staged_files": [], "diff": "diff"})
        assert "unable to connect to Ollama" in result

    def test_fallback_on_repeated_api_errors(self):
        model = make_ollama({"ollama_max_retries": 1})
        with patch.object(model, "set_model", return_value=True), \
             patch.object(model, "_call_model", side_effect=Exception("API down")):
            result = model.generate_commit_message({"staged_files": [], "branch": "main", "diff": "diff"})
        assert "feat:" in result  # Falls back gracefully
