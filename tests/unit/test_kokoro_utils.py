import re
import types
from pathlib import Path

# Load only the text-normalization helpers from kokoro.py to avoid heavy deps
lines = Path("questions/inference_server/kokoro.py").read_text().splitlines()
code = "\n".join([l for l in lines[1:73] if "phonemizer" not in l and "torch" not in l])
mod = types.ModuleType("kokoro_utils")
exec(code, mod.__dict__)


def test_split_num_year():
    match = re.match(r"\d+", "2023")
    assert mod.split_num(match) == "20 23"


def test_split_num_time():
    match = re.match(r"[0-9:]+", "12:05")
    assert mod.split_num(match) == "12 oh 5"


def test_flip_money_dollars():
    match = re.match(r"[$£]\d+(?:\.\d+)?", "$2.50")
    assert mod.flip_money(match) == "2 dollars and 50 cents"


def test_point_num_simple():
    match = re.match(r"\d*\.\d+", "3.14")
    assert mod.point_num(match) == "3 point 1 4"
