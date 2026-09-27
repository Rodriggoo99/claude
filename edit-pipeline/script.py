# Caption script -> captions.json (word-level times aligned to Whisper words)
import json, re, difflib, unicodedata

# Each chunk: list of lines; *word* = serif italic accent. "#0€" = hero line.
# Optional explicit start time override per chunk via tuple (lines, start).
CHUNKS = [
    ["oferecemos", "mais de *um* *mês*"],
    ["de estratégia de", "marca pessoal"],
    ["a um cliente"],
    ["e ganhamos", "#0€", "com isso"],
    ["um cliente chegou", "à nossa agência"],
    ["à procura de", "uma *direção*"],
    ["e de um novo *rumo*"],
    ["para as suas", "redes sociais"],
    ["visto que estavam", "*estagnados*"],
    ["e queriam dar", "o próximo passo"],
    ["em termos de", "marca pessoal"],
    ["foi mais de *um* *mês*"],
    ["reunião atrás", "de reunião"],
    ["à procura de vermos"],
    ["como é que seria", "*possível*"],
    ["concretizarmos", "este projeto"],
    ["durante estas", "reuniões"],
    ["fomos dando algumas", "*ideias* de conteúdo"],
    ["alguns truques", "de redes sociais"],
    ["e algumas formas de", "como é que iríamos"],
    ["*alavancar* o conteúdo", "deste cliente"],
    ["daqui em diante"],
    ["mas o *problema*", "foi que demos"],
    ["*demasiado* antes", "do contrato assinado"],
    ["este negócio", "acabou por"],
    ["não se concretizar"],
    ["e no mesmo dia"],
    ["que disseram que *não*"],
    ["estavam a lançar"],
    ["uma das *ideias*"],
    ["que nós demos", "durante as reuniões"],
    ["mas é a tal coisa"],
    ["a visão nem", "sempre *chega*"],
    ["é preciso saber", "como *executar*"],
    ["desde esta", "má experiência"],
    ["a nossa agência", "tem uma *regra*"],
    "G3",  # graphic carries the words (45.28-48.8)
    ["e se a tua empresa", "ou a tua marca pessoal"],
    ["está sem *rumo*", "ou direção"],
    ["comenta", "#reunião"],
    ["marcamos uma reunião", "de *diagnóstico*"],
    ["completamente", "*gratuita*"],
    ["e sais de lá", "a saber"],
    ["o que é que está mal", "com a tua empresa"],
]

def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9€]", "", s)

W = [w for seg in json.load(open("words.json")) for w in seg["w"]]
# Whisper misheard the ending; replace its tail with what was actually said.
tail_i = next(i for i, w in enumerate(W) if w[0] >= 55.93)
tail_words = "e sais de lá a saber o que é que está mal com a tua empresa".split()
tail_times = [55.94, 56.06, 56.34, 56.46, 56.52, 56.60, 56.84, 57.02, 57.08, 57.18, 57.26, 57.44, 57.52, 57.70, 57.76, 57.86]
W = W[:tail_i] + [[t, t + 0.1, s] for t, s in zip(tail_times, tail_words)]
# "Mas há tal coisa" -> "mas é a tal coisa"
for i, w in enumerate(W):
    if norm(w[2]) == "ha" and 38.6 < w[0] < 38.8:
        W[i] = [w[0], w[1], "é"]
        W.insert(i + 1, [w[0] + 0.07, w[1], "a"])
        break

src = [norm(w[2]) for w in W]
toks = []  # (chunk_idx, line_idx, text, accent, hero)
for ci, ch in enumerate(CHUNKS):
    if ch == "G3":
        continue
    for li, line in enumerate(ch):
        hero = line.startswith("#")
        for tok in (line[1:] if hero else line).split():
            acc = tok.startswith("*")
            toks.append((ci, li, tok.strip("*"), acc, hero))
dst = [norm(t[2]) for t in toks]
times = [None] * len(toks)
sm = difflib.SequenceMatcher(None, src, dst, autojunk=False)
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        times[b + k] = W[a + k][0]
miss = [toks[i][2] for i, t in enumerate(times) if t is None]
print("unmatched:", miss)
# interpolate missing
for i in range(len(times)):
    if times[i] is None:
        j = i
        while j < len(times) and times[j] is None:
            j += 1
        prev = times[i - 1] if i else 0
        nxt = times[j] if j < len(times) else prev + 0.3
        for k in range(i, j):
            times[k] = prev + (nxt - prev) * (k - i + 1) / (j - i + 1)

out = []
for ci, ch in enumerate(CHUNKS):
    if ch == "G3":
        continue
    lines = [[] for _ in ch]
    for (c, li, text, acc, hero), t in zip(toks, times):
        if c == ci:
            lines[li].append({"w": text, "t": round(t, 3), "a": acc, "h": hero})
    out.append({"start": lines[0][0]["t"], "lines": lines})
DUR = 58.4
for i, c in enumerate(out):
    nxt = out[i + 1]["start"] if i + 1 < len(out) else DUR
    c["end"] = round(min(nxt, c["lines"][-1][-1]["t"] + 2.5), 3)
# graphic G3 window: no captions between 45.28 and 48.8
for c in out:
    if 45.0 < c["end"] < 48.9 and c["start"] < 45.28:
        c["end"] = 45.28
json.dump(out, open("render/captions.json", "w"), ensure_ascii=False, indent=1)
for c in out:
    print(f'{c["start"]:6.2f}-{c["end"]:6.2f}', " / ".join(" ".join(w["w"] for w in l) for l in c["lines"]))
