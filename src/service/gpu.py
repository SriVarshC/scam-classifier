"""Optional on-demand GPU backend: the same Ollama model running in a Unity cluster GPU job.

Deployment only - same model (CALL_LLM_MODEL), prompts and scoring as the CPU path.

How it works (see deploy/unity/README.md):
  * A small controller job on Unity keeps an SSH connection to this VM (forced command scam-gpu-ctl).
    The service asks for the GPU by writing "start" to <control dir>/request; the controller picks it
    up within ~1 s and submits the GPU job. Every poll it also reports the cluster status to
    <control dir>/status. Azure never holds a key to the Unity account.
  * The GPU job starts Ollama and opens a reverse SSH tunnel, so the model appears at
    SCAM_GPU_OLLAMA_URL (e.g. http://127.0.0.1:11435). Tunnel up == model loaded. The job stops itself
    after a quiet period.
  * While the GPU is down the CPU model answers, as before.

Environment (all optional; without SCAM_GPU_OLLAMA_URL the GPU path is off):
  SCAM_GPU_OLLAMA_URL            tunnel address of the GPU Ollama
  SCAM_GPU_CONTROL_DIR           shared folder with the controller (default /var/lib/scam-gpu)
  SCAM_GPU_TIMEOUT_SECONDS       LLM deadline on the GPU (default 20); on failure the CPU model answers
  SCAM_GPU_AUTOSTART             1 (default) = request the GPU job when a request finds it down
  SCAM_GPU_START_EVERY_SECONDS   minimum gap between automatic start requests (default 120)
"""
import os
import threading
import time
import urllib.request
from pathlib import Path


class GpuBackend:
    def __init__(self, url, control_dir="/var/lib/scam-gpu", autostart=True, start_every_s=120, check_every_s=5):
        self.url = url.rstrip("/")
        self.control_dir = Path(control_dir) if control_dir else None
        self.autostart, self.start_every_s, self.check_every_s = autostart, start_every_s, check_every_s
        self._lock = threading.Lock()
        self._ready, self._checked_at = False, 0.0
        self._last_start_at, self.last_start = 0.0, None

    @classmethod
    def from_env(cls):
        url = os.environ.get("SCAM_GPU_OLLAMA_URL", "").strip()
        if not url:
            return None
        return cls(url, control_dir=os.environ.get("SCAM_GPU_CONTROL_DIR", "/var/lib/scam-gpu"),
                   autostart=os.environ.get("SCAM_GPU_AUTOSTART", "1") == "1",
                   start_every_s=float(os.environ.get("SCAM_GPU_START_EVERY_SECONDS", "120")))

    def _probe(self):
        try:
            with urllib.request.urlopen(f"{self.url}/api/version", timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    def ready(self, fresh=False):
        """Is the GPU model reachable through the tunnel? Cached for a few seconds."""
        now = time.monotonic()
        if fresh or now - self._checked_at > self.check_every_s:
            self._ready, self._checked_at = self._probe(), now
        return self._ready

    def mark_down(self):
        self._ready, self._checked_at = False, time.monotonic()

    def _request(self, action):
        """Hand an action (start|stop) to the Unity controller (atomic file write)."""
        if self.control_dir is None:
            return {"ok": False, "output": "no control dir"}
        try:
            tmp = self.control_dir / f".request.{os.getpid()}"
            tmp.write_text(action)
            os.replace(tmp, self.control_dir / "request")
            return {"ok": True, "output": f"{action} requested"}
        except OSError as e:
            return {"ok": False, "output": f"{type(e).__name__}: {e}"[:300]}

    def start(self, reason="request", force=False):
        """Ask for the GPU job. Returns False if skipped (autostart off, or asked recently)."""
        if not force and not self.autostart:
            return False
        with self._lock:
            now = time.monotonic()
            if not force and now - self._last_start_at < self.start_every_s:
                return False
            self._last_start_at = now
        result = self._request("start")
        self.last_start = {"reason": reason, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **result}
        return result["ok"]

    def stop(self):
        return self._request("stop")

    def _controller(self):
        if self.control_dir is None:
            return {"connected": False}
        try:
            seen = float((self.control_dir / "seen").read_text().strip() or 0)
        except (OSError, ValueError):
            seen = 0.0
        try:
            report = (self.control_dir / "status").read_text()[-1000:].strip()
        except OSError:
            report = ""
        age = time.time() - seen if seen else None
        return {"connected": age is not None and age < 30,
                "last_seen_s_ago": None if age is None else round(age),
                "pending_request": (self.control_dir / "request").exists(), "report": report}

    def status(self):
        return {"enabled": True, "ready": self.ready(fresh=True), "autostart": self.autostart,
                "last_start": self.last_start, "controller": self._controller()}
