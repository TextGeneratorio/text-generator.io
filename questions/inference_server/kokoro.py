import os
import re
import threading

import numpy as np
import phonemizer
import torch

# Enable TensorFloat32 and other CUDA optimizations for Ampere+ GPUs
if torch.cuda.is_available():
    torch.set_float32_matmul_precision('high')
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True
    if hasattr(torch.backends.cuda, 'enable_flash_sdp'):
        torch.backends.cuda.enable_flash_sdp(True)

# Cache for compiled models
_compiled_models = {}


def split_num(num):
    num = num.group()
    if "." in num:
        return num
    elif ":" in num:
        h, m = [int(n) for n in num.split(":")]
        if m == 0:
            return f"{h} o'clock"
        elif m < 10:
            return f"{h} oh {m}"
        return f"{h} {m}"
    year = int(num[:4])
    if year < 1100 or year % 1000 < 10:
        return num
    left, right = num[:2], int(num[2:4])
    s = "s" if num.endswith("s") else ""
    if 100 <= year % 1000 <= 999:
        if right == 0:
            return f"{left} hundred{s}"
        elif right < 10:
            return f"{left} oh {right}{s}"
    return f"{left} {right}{s}"


def flip_money(m):
    m = m.group()
    bill = "dollar" if m[0] == "$" else "pound"
    if m[-1].isalpha():
        return f"{m[1:]} {bill}s"
    elif "." not in m:
        s = "" if m[1:] == "1" else "s"
        return f"{m[1:]} {bill}{s}"
    b, c = m[1:].split(".")
    s = "" if b == "1" else "s"
    c = int(c.ljust(2, "0"))
    coins = f"cent{'' if c == 1 else 's'}" if m[0] == "$" else ("penny" if c == 1 else "pence")
    return f"{b} {bill}{s} and {c} {coins}"


def point_num(num):
    a, b = num.group().split(".")
    return " point ".join([a, " ".join(b)])


def normalize_text(text):
    # Strip special characters that TTS might pronounce literally (e.g., asterisk, underscore)
    # Common in AI-generated text for formatting like *bold* or _italic_
    text = re.sub(r"[*_~`#^|\\<>]", "", text)
    text = text.replace(chr(8216), "'").replace(chr(8217), "'")
    text = text.replace("«", chr(8220)).replace("»", chr(8221))
    text = text.replace(chr(8220), '"').replace(chr(8221), '"')
    text = text.replace("(", "«").replace(")", "»")
    for a, b in zip("、。！，：；？", ",.!,:;?"):
        text = text.replace(a, b + " ")
    text = re.sub(r"[^\S \n]", " ", text)
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"(?<=\n) +(?=\n)", "", text)
    text = re.sub(r"\bD[Rr]\.(?= [A-Z])", "Doctor", text)
    text = re.sub(r"\b(?:Mr\.|MR\.(?= [A-Z]))", "Mister", text)
    text = re.sub(r"\b(?:Ms\.|MS\.(?= [A-Z]))", "Miss", text)
    text = re.sub(r"\b(?:Mrs\.|MRS\.(?= [A-Z]))", "Mrs", text)
    text = re.sub(r"\betc\.(?! [A-Z])", "etc", text)
    text = re.sub(r"(?i)\b(y)eah?\b", r"\1e'a", text)
    text = re.sub(r"\d*\.\d+|\b\d{4}s?\b|(?<!:)\b(?:[1-9]|1[0-2]):[0-5]\d\b(?!:)", split_num, text)
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(
        r"(?i)[$£]\d+(?:\.\d+)?(?: hundred| thousand| (?:[bm]|tr)illion)*\b|[$£]\d+\.\d\d?\b", flip_money, text
    )
    text = re.sub(r"\d*\.\d+", point_num, text)
    text = re.sub(r"(?<=\d)-(?=\d)", " to ", text)
    text = re.sub(r"(?<=\d)S", " S", text)
    text = re.sub(r"(?<=[BCDFGHJ-NP-TV-Z])'?s\b", "'S", text)
    text = re.sub(r"(?<=X')S\b", "s", text)
    text = re.sub(r"(?:[A-Za-z]\.){2,} [a-z]", lambda m: m.group().replace(".", "-"), text)
    text = re.sub(r"(?i)(?<=[A-Z])\.(?=[A-Z])", "-", text)
    return text.strip()


def get_vocab():
    _pad = "$"
    _punctuation = ';:,.!?¡¿—…"«»“” '
    _letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    _letters_ipa = (
        "ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘'̩'ᵻ"
    )
    symbols = [_pad] + list(_punctuation) + list(_letters) + list(_letters_ipa)
    dicts = {}
    for i in range(len((symbols))):
        dicts[symbols[i]] = i
    return dicts


VOCAB = get_vocab()


def tokenize(ps):
    return [i for i in map(VOCAB.get, ps) if i is not None]


phonemizers = dict(
    a=phonemizer.backend.EspeakBackend(language="en-us", preserve_punctuation=True, with_stress=True),
    b=phonemizer.backend.EspeakBackend(language="en-gb", preserve_punctuation=True, with_stress=True),
)
_phonemizer_locks = {lang: threading.Lock() for lang in phonemizers}


def phonemize(text, lang, norm=True):
    if norm:
        text = normalize_text(text)
    with _phonemizer_locks[lang]:
        ps = phonemizers[lang].phonemize([text])
    ps = ps[0] if ps else ""
    # https://en.wiktionary.org/wiki/kokoro#English
    ps = ps.replace("kəkˈoːɹoʊ", "kˈoʊkəɹoʊ").replace("kəkˈɔːɹəʊ", "kˈəʊkəɹəʊ")
    ps = ps.replace("ʲ", "j").replace("r", "ɹ").replace("x", "k").replace("ɬ", "l")
    ps = re.sub(r"(?<=[a-zɹː])(?=hˈʌndɹɪd)", " ", ps)
    ps = re.sub(r' z(?=[;:,.!?¡¿—…"«»“” ]|$)', "z", ps)
    if lang == "a":
        ps = re.sub(r"(?<=nˈaɪn)ti(?!ː)", "di", ps)
    ps = "".join(filter(lambda p: p in VOCAB, ps))
    return ps.strip()


def length_to_mask(lengths):
    mask = torch.arange(lengths.max()).unsqueeze(0).expand(lengths.shape[0], -1).type_as(lengths)
    mask = torch.gt(mask + 1, lengths.unsqueeze(1))
    return mask


# Autocast policy. bf16/fp16: whole model under autocast (bf16 was the old default). fp32: none.
# dec-fp16/dec-bf16: text/duration/F0 stages in fp32, decoder under autocast. On a 3090, 122 chars:
# bf16 123 ms, fp32 84 ms, dec-fp16 71 ms. bf16 durations drift from fp32 (mel L1 0.77); dec-fp16 stays
# at 39 dB SNR / mel L1 0.011 vs fp32 with the same seed (seed-to-seed noise is mel L1 ~0.065).
KOKORO_PRECISION = os.environ.get("KOKORO_PRECISION", "dec-fp16").strip().lower()
# Optional fixed RNG seed per forward (the decoder's sine/noise source is random); for parity tests
KOKORO_SEED = os.environ.get("KOKORO_SEED")
# Sentence segmentation: segment 1 is short so the first audio is ready early
KOKORO_SEGMENT = os.environ.get("KOKORO_SEGMENT", "1").strip().lower() in {"1", "true", "yes", "on"}
SEG_FIRST_MIN_CHARS = int(os.environ.get("KOKORO_SEG_FIRST_MIN_CHARS", "30"))
SEG_FIRST_MAX_CHARS = int(os.environ.get("KOKORO_SEG_FIRST_MAX_CHARS", "120"))
SEG_MAX_CHARS = int(os.environ.get("KOKORO_SEG_MAX_CHARS", "400"))
MAX_TOKENS = 510


_AC_DTYPES = {"bf16": torch.bfloat16, "fp16": torch.float16}


def _autocast(device, stage, mode):
    if mode.startswith("dec-"):
        mode = mode[4:] if stage == "dec" else "fp32"
    dtype = _AC_DTYPES.get(mode)
    return torch.amp.autocast(device_type="cuda", dtype=dtype or torch.bfloat16, enabled=device.type == "cuda" and dtype is not None)


def fold_weight_norm(model):
    """Bake weight_norm (g * v/|v|) into plain weights once instead of recomputing it every forward; bit-identical."""
    from torch.nn.utils import remove_weight_norm

    n = 0
    for part in model.values():
        for mod in part.modules():
            if hasattr(mod, "weight_g") and hasattr(mod, "weight_v"):
                remove_weight_norm(mod)
                n += 1
    return n


@torch.inference_mode()
def forward(model, tokens, ref_s, speed, seed=None):
    out = _forward(model, tokens, ref_s, speed, seed, KOKORO_PRECISION)
    if KOKORO_PRECISION != "fp32" and not np.isfinite(out).all():
        # fp16 overflow guard: redo this segment in fp32
        out = _forward(model, tokens, ref_s, speed, seed, "fp32")
    return out


def _forward(model, tokens, ref_s, speed, seed, precision):
    device = ref_s.device
    seed = KOKORO_SEED if seed is None else seed
    if seed is not None:
        torch.manual_seed(int(seed))
    tokens = torch.tensor([[0, *tokens, 0]], dtype=torch.long, device=device)
    input_lengths = torch.tensor([tokens.shape[-1]], dtype=torch.long, device=device)
    text_mask = length_to_mask(input_lengths)

    with _autocast(device, "enc", precision):
        bert_dur = model.bert(tokens, attention_mask=(~text_mask).int())
        d_en = model.bert_encoder(bert_dur).transpose(-1, -2)
        s = ref_s[:, 128:]
        d = model.predictor.text_encoder(d_en, s, input_lengths, text_mask)
        x, _ = model.predictor.lstm(d)
        duration = model.predictor.duration_proj(x)
        duration = torch.sigmoid(duration).sum(axis=-1) / speed
        pred_dur = torch.round(duration).clamp(min=1).long()
        total_frames = pred_dur.sum().item()
        num_tokens = input_lengths.item()
        pred_aln_trg = torch.zeros(num_tokens, total_frames, device=device)
        # Vectorized duration expansion (avoids per-token CPU sync)
        dur_flat = pred_dur.squeeze(0)
        cumsum = dur_flat.cumsum(0)
        frame_indices = torch.arange(total_frames, device=device)
        token_indices = torch.searchsorted(cumsum, frame_indices, right=True)
        token_indices = token_indices.clamp(max=num_tokens - 1)
        pred_aln_trg[token_indices, frame_indices] = 1.0
        en = d.transpose(-1, -2) @ pred_aln_trg.unsqueeze(0)
        F0_pred, N_pred = model.predictor.F0Ntrain(en, s)
        t_en = model.text_encoder(tokens, input_lengths, text_mask)
        asr = t_en @ pred_aln_trg.unsqueeze(0)
    with _autocast(device, "dec", precision):
        out = model.decoder(asr, F0_pred, N_pred, ref_s[:, :128])
    return out.squeeze().cpu().numpy()


def compile_model(model, mode="reduce-overhead", dynamic=True):
    """
    Compile model components for faster inference using torch.compile.
    dynamic=True avoids recompiles for varying input sizes.
    """
    model_id = id(model)
    if model_id in _compiled_models:
        return _compiled_models[model_id]

    compile_opts = {"mode": mode, "fullgraph": False, "dynamic": dynamic}
    compiled_components = []

    try:
        model.bert = torch.compile(model.bert, **compile_opts)
        compiled_components.append("bert")
    except Exception as e:
        print(f"bert compile failed: {e}")

    try:
        model.predictor.text_encoder = torch.compile(model.predictor.text_encoder, **compile_opts)
        compiled_components.append("predictor.text_encoder")
    except Exception as e:
        print(f"predictor.text_encoder compile failed: {e}")

    try:
        model.text_encoder = torch.compile(model.text_encoder, **compile_opts)
        compiled_components.append("text_encoder")
    except Exception as e:
        print(f"text_encoder compile failed: {e}")

    if compiled_components:
        _compiled_models[model_id] = model
        print(f"Compiled (dynamic={dynamic}, mode={mode}): {', '.join(compiled_components)}")

    return model


_SENT_END = re.compile(r'[.!?\u2026]+["\u00bb\u201d\')\]]*\s+|\s*\n+\s*')
_CLAUSE_END = re.compile(r"[,;:\u2014\u2013]\s+")


def split_sentences(text):
    out, start = [], 0
    for m in _SENT_END.finditer(text):
        out.append(text[start : m.end()].strip())
        start = m.end()
    out.append(text[start:].strip())
    return [s for s in out if s]


def split_segments(text):
    """Normalized text -> segments. Segment 1 is the first sentence (or clause), the rest are sentence groups."""
    sents = split_sentences(text)
    if not sents:
        return []
    first, i = sents[0], 1
    while len(first) < SEG_FIRST_MIN_CHARS and i < len(sents):
        first, i = first + " " + sents[i], i + 1
    rest = sents[i:]
    if len(first) > SEG_FIRST_MAX_CHARS:
        cut = next((m.end() for m in _CLAUSE_END.finditer(first) if SEG_FIRST_MIN_CHARS <= m.start() < len(first) - SEG_FIRST_MIN_CHARS), None)
        if cut is not None:
            rest = [first[cut:].strip()] + rest
            first = first[:cut].strip()
    segs, cur = [first], ""
    for s in rest:
        if cur and len(cur) + 1 + len(s) > SEG_MAX_CHARS:
            segs.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}" if cur else s
    if cur:
        segs.append(cur)
    return segs


def generate_stream(model, text, voicepack, lang="a", speed=1, seed=None):
    """Yield (audio, is_last) per forward pass. Non-streamed output is the concatenation of these chunks."""
    if KOKORO_SEGMENT:
        segs = split_segments(normalize_text(text))
    else:
        segs = [text]
    toks = (t for t in (tokenize(phonemize(seg, lang, norm=not KOKORO_SEGMENT)) for seg in segs) if t)
    cur = next(toks, None)
    while cur is not None:
        nxt = next(toks, None)  # one segment of lookahead so is_last is exact even if a trailing segment is empty
        n = (len(cur) + MAX_TOKENS - 1) // MAX_TOKENS
        for i in range(n):
            win = cur[i * MAX_TOKENS : (i + 1) * MAX_TOKENS]
            yield forward(model, win, voicepack[len(win)], speed, seed=seed), nxt is None and i == n - 1
        cur = nxt


def generate(model, text, voicepack, lang="a", speed=1, ps=None):
    ps = ps or phonemize(text, lang)
    tokens = tokenize(ps)
    if not tokens:
        return None
    elif len(tokens) > 510:
        tokens = tokens[:510]
        print("Truncated to 510 tokens")
    ref_s = voicepack[len(tokens)]
    out = forward(model, tokens, ref_s, speed)
    ps = "".join(next(k for k, v in VOCAB.items() if i == v) for i in tokens)
    return out, ps


def generate_full(model, text, voicepack, lang="a", speed=1, ps=None):
    outs = [a for a, _ in generate_stream(model, text, voicepack, lang=lang, speed=speed)]
    if not outs:
        return None
    return np.concatenate(outs), ps or ""
