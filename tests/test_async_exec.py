from colab_mcp.tools.execution import (
    _gen_run_async_code, _gen_poll_code, _gen_stop_code, _gen_list_jobs_code,
)


def test_run_async_code_valid_and_threads():
    code = _gen_run_async_code("print('hi')", "job_abc")
    compile(code, "<gen>", "exec")
    assert "__COLAB_MCP_JOBS__" in code
    assert "threading" in code
    assert "job_abc" in code


def test_run_async_embeds_user_code_via_json():
    code = _gen_run_async_code("x = 'tricky \"quotes\"'", "job_1")
    compile(code, "<gen>", "exec")
    assert "json.loads(" in code  # user code embedded safely


def test_poll_code_uses_cursor():
    code = _gen_poll_code("job_1", 500)
    compile(code, "<gen>", "exec")
    assert "job_1" in code
    assert "500" in code


def test_stop_code_sets_flag():
    code = _gen_stop_code("job_1")
    compile(code, "<gen>", "exec")
    assert "stop" in code.lower()


def test_list_jobs_code_valid():
    code = _gen_list_jobs_code()
    compile(code, "<gen>", "exec")
    assert "__COLAB_MCP_JOBS__" in code


import json as _json
import time as _time


def test_run_async_harness_executes_in_real_interpreter():
    # Execute the generated run_async code in a fresh namespace and confirm
    # the job registry is populated and the thread runs to completion.
    ns = {}
    code = _gen_run_async_code("print('hello from job')", "job_real")
    exec(compile(code, "<gen>", "exec"), ns, ns)
    assert "__COLAB_MCP_JOBS__" in ns
    rec = ns["__COLAB_MCP_JOBS__"]["job_real"]
    # wait for the daemon thread to finish
    rec["thread"].join(timeout=5)
    assert rec["status"] == "done"
    assert "hello from job" in rec["buf"].getvalue()


def test_poll_after_run_reads_output_in_real_interpreter():
    ns = {}
    exec(compile(_gen_run_async_code("print('line1')", "job_p"), "<g>", "exec"), ns, ns)
    ns["__COLAB_MCP_JOBS__"]["job_p"]["thread"].join(timeout=5)
    # run poll code in the SAME namespace
    poll = _gen_poll_code("job_p", 0)
    # capture stdout from the poll print
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(poll, "<g>", "exec"), ns, ns)
    out = buf.getvalue()
    assert "line1" in out
    assert "done" in out
