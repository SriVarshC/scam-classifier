"""On-demand GPU routing: GPU when its tunnel is up, CPU otherwise (and the GPU job gets started)."""
from conftest import TOKEN, FakeLLM

SCAM = ("Caller: This is your bank fraud department. Your account is locked. "
        "Read me the code we just texted you so we can secure it.")


class FakeGpu:
    def __init__(self, ready):
        self.url, self._ready = "http://127.0.0.1:1", ready
        self.starts, self.marked_down, self.stopped = [], 0, 0

    def ready(self, fresh=False):
        return self._ready

    def mark_down(self):
        self.marked_down += 1
        self._ready = False

    def start(self, reason="request", force=False):
        self.starts.append((reason, force))
        return True

    def stop(self):
        self.stopped += 1
        return {"ok": True, "output": "cancelled"}

    def status(self):
        return {"enabled": True, "ready": self._ready}


def make(gpu_ready, gpu_fail=False):
    from service.pipeline import ScamService
    cpu, gpu_llm, gpu = FakeLLM(), FakeLLM(fail=gpu_fail), FakeGpu(gpu_ready)
    return ScamService(llm=cpu, gpu=gpu, gpu_llm=gpu_llm), cpu, gpu_llm, gpu


def test_uses_gpu_when_ready():
    svc, cpu, gpu_llm, gpu = make(True)
    out = svc.analyze(SCAM, "r1")
    assert out["llm_backend"] == "gpu" and gpu_llm.prompts and not cpu.prompts
    assert out["classes"][0] == "fraud" and gpu.starts == []


def test_gpu_down_uses_cpu_and_starts_gpu():
    svc, cpu, gpu_llm, gpu = make(False)
    out = svc.analyze(SCAM, "r2")
    assert out["llm_backend"] == "cpu" and cpu.prompts and not gpu_llm.prompts
    assert gpu.starts == [("request", False)]


def test_gpu_failure_falls_back_to_cpu_with_same_answer():
    svc, cpu, gpu_llm, gpu = make(True, gpu_fail=True)
    out = svc.analyze(SCAM, "r3")
    assert out["llm_backend"] == "cpu" and gpu.marked_down == 1
    ref, *_ = make(False)
    assert out["classes"] == ref.analyze(SCAM, "r3")["classes"]


def test_gpu_endpoints_need_token_and_work():
    from fastapi.testclient import TestClient
    from service.app import create_app
    svc, *_, gpu = make(False)
    client = TestClient(create_app(service=svc, token=TOKEN))
    assert client.post("/v1/gpu/start").status_code == 401
    h = {"Authorization": f"Bearer {TOKEN}"}
    r = client.post("/v1/gpu/start", headers=h).json()
    assert r["started"] is True and gpu.starts == [("manual", True)]
    assert client.get("/v1/gpu/status", headers=h).json()["enabled"] is True
    assert client.post("/v1/gpu/stop", headers=h).json()["ok"] is True and gpu.stopped == 1
    assert client.get("/v1/status", headers=h).json()["gpu_enabled"] is True


def test_gpu_endpoints_404_when_not_configured(service):
    from fastapi.testclient import TestClient
    from service.app import create_app
    client = TestClient(create_app(service=service, token=TOKEN))
    h = {"Authorization": f"Bearer {TOKEN}"}
    assert client.get("/v1/gpu/status", headers=h).status_code == 404
    assert client.get("/v1/status", headers=h).json()["gpu_enabled"] is False


def test_real_backend_writes_requests_and_debounces(tmp_path):
    import time
    from service.gpu import GpuBackend
    b = GpuBackend("http://127.0.0.1:1", control_dir=tmp_path, start_every_s=120)
    assert b.ready() is False                        # nothing listens on port 1
    assert b.start() is True and (tmp_path / "request").read_text() == "start"
    (tmp_path / "request").unlink()                  # the controller consumed it
    assert b.start() is False and not (tmp_path / "request").exists()   # asked < 120 s ago
    assert b.start("manual", force=True) is True     # warm-up endpoint always sends
    assert b.stop()["ok"] and (tmp_path / "request").read_text() == "stop"
    (tmp_path / "seen").write_text(str(time.time()))
    (tmp_path / "status").write_text("controller=1 | no job")
    c = b.status()["controller"]
    assert c["connected"] is True and "no job" in c["report"] and c["pending_request"] is True
