from colab_mcp.tools.files import (
    _gen_list_vm_code, _gen_read_vm_code, _gen_write_vm_code, _gen_delete_vm_code,
)


def test_list_vm_code_valid_and_quotes():
    code = _gen_list_vm_code("/content/My Dir")
    compile(code, "<gen>", "exec")
    assert "'/content/My Dir'" in code


def test_read_vm_code_truncates_to_max_bytes():
    code = _gen_read_vm_code("/content/x.txt", 1234)
    compile(code, "<gen>", "exec")
    assert "1234" in code
    assert "'/content/x.txt'" in code


def test_write_vm_code_embeds_content_via_json():
    code = _gen_write_vm_code("/content/x.txt", 'hi "there"\nline2')
    compile(code, "<gen>", "exec")
    assert "json.loads(" in code


def test_delete_vm_code_valid():
    code = _gen_delete_vm_code("/content/x.txt")
    compile(code, "<gen>", "exec")
    assert "'/content/x.txt'" in code
