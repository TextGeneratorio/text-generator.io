import re

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


def phonemize(text, lang, norm=True):
    if norm:
        text = normalize_text(text)
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


@torch.inference_mode()
def forward(model, tokens, ref_s, speed):
    device = ref_s.device
    tokens = torch.tensor([[0, *tokens, 0]], dtype=torch.long, device=device)
    input_lengths = torch.tensor([tokens.shape[-1]], dtype=torch.long, device=device)
    text_mask = length_to_mask(input_lengths)

    with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=device.type == "cuda"):
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
    ps = ps or phonemize(text, lang)
    tokens = tokenize(ps)
    if not tokens:
        return None
    outs = []
    loop_count = len(tokens) // 510 + (1 if len(tokens) % 510 != 0 else 0)
    for i in range(loop_count):
        ref_s = voicepack[len(tokens[i * 510 : (i + 1) * 510])]
        out = forward(model, tokens[i * 510 : (i + 1) * 510], ref_s, speed)
        outs.append(out)
    outs = np.concatenate(outs)
    ps = "".join(next(k for k, v in VOCAB.items() if i == v) for i in tokens)
    return outs, ps
