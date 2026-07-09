from llm_gateway import strip_code_fence


def test_strip_code_fence_removes_json_fence():
    raw = "```json\n[1, 2, 3]\n```"
    assert strip_code_fence(raw) == "[1, 2, 3]"


def test_strip_code_fence_removes_plain_fence():
    raw = "```\n{\"a\": 1}\n```"
    assert strip_code_fence(raw) == '{"a": 1}'


def test_strip_code_fence_passthrough_without_fence():
    assert strip_code_fence("  [1, 2]  ") == "[1, 2]"
