from colab_mcp.tools.inspect import _gen_list_vars_code, _gen_inspect_var_code


def test_list_vars_code_valid_and_filters_dunders():
    code = _gen_list_vars_code()
    compile(code, "<gen>", "exec")
    assert "globals()" in code
    assert "startswith('_')" in code


def test_inspect_var_code_quotes_name_and_reports_shape():
    code = _gen_inspect_var_code("model")
    compile(code, "<gen>", "exec")
    assert "'model'" in code
    assert "shape" in code
