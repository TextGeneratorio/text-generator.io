from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "questions/inference_server/trtllm_accel/serve_generic.sh"


def _run_launcher(tmp_path: Path, *extra: str, **env_overrides: str) -> list[str]:
    venv = tmp_path / "venv"
    bin_dir = venv / "bin"
    bin_dir.mkdir(parents=True)
    recorder = tmp_path / "argv"
    fake = bin_dir / "trtllm-serve"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s\\n' \"$@\" > {recorder}\n"
    )
    fake.chmod(0o755)

    env = os.environ.copy()
    env.update({"TRTLLM_VENV": str(venv), "MODEL": "/models/gemma4", **env_overrides})
    subprocess.run([str(LAUNCHER), *extra], env=env, check=True, capture_output=True, text=True)
    return recorder.read_text().splitlines()


def test_trtllm_launcher_uses_openai_serve_contract(tmp_path):
    argv = _run_launcher(tmp_path)

    assert argv[:8] == [
        "serve",
        "/models/gemma4",
        "--backend",
        "pytorch",
        "--host",
        "0.0.0.0",
        "--port",
        "8200",
    ]
    assert "--trust_remote_code" in argv


def test_trtllm_launcher_passes_capacity_and_extra_flags(tmp_path):
    argv = _run_launcher(
        tmp_path,
        "--log_level",
        "info",
        TP_SIZE="1",
        MAX_SEQ_LEN="4096",
        MAX_NUM_TOKENS="8192",
        KV_CACHE_FREE_GPU_MEMORY_FRACTION="0.15",
        TRUST_REMOTE_CODE="0",
    )

    assert argv[argv.index("--tp_size") + 1] == "1"
    assert argv[argv.index("--max_seq_len") + 1] == "4096"
    assert argv[argv.index("--max_num_tokens") + 1] == "8192"
    assert argv[argv.index("--kv_cache_free_gpu_memory_fraction") + 1] == "0.15"
    assert "--trust_remote_code" not in argv
    assert argv[-2:] == ["--log_level", "info"]
