from colab_mcp.tools.runtime import _gen_resource_usage_code


def test_gen_resource_usage_is_valid_python():
    code = _gen_resource_usage_code()
    compile(code, "<gen>", "exec")


def test_gen_resource_usage_queries_gpu_and_mem():
    code = _gen_resource_usage_code()
    assert "nvidia-smi" in code
    assert "utilization.gpu" in code
    assert "virtual_memory" in code
    assert "___COLAB_MCP_OUTPUT_START___" in code
