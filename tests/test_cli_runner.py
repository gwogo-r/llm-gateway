import pytest

from llm_gateway import CliAgentError
from llm_gateway.cli_runner import _find_binary


def test_find_binary_raises_for_unknown_command():
    with pytest.raises(CliAgentError, match="не найден в PATH"):
        _find_binary("definitely-not-a-real-cli-agent-xyz")
