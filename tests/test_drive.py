from colab_mcp.tools.drive import (
    _gen_mount_code, _gen_unmount_code, _gen_list_drive_code,
)


def test_mount_code_valid_and_mounts():
    code = _gen_mount_code("/content/drive")
    compile(code, "<gen>", "exec")
    assert "drive.mount" in code
    assert "/content/drive" in code


def test_unmount_code_flushes():
    code = _gen_unmount_code()
    compile(code, "<gen>", "exec")
    assert "flush_and_unmount" in code


def test_list_drive_code_quotes_path():
    code = _gen_list_drive_code("/content/drive/My Drive")
    compile(code, "<gen>", "exec")
    assert "'/content/drive/My Drive'" in code or '"/content/drive/My Drive"' in code
