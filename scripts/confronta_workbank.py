"""Confronto fra la stima N preliminare e le valutazioni di capacità di WORKBank (Ae).

Uso: python scripts/confronta_workbank.py <expert_rated_technological_capability.csv>
Il confronto è di rango (Spearman): non richiede la conversione di Ae a 0-4,
che resta bloccata finché non si conoscono le ancore della scala.
"""
import csv, json, statistics, collections, sys

STAFF = "docs/ricerca/estratti/llm-prior-staff-finale.jsonl"
WB_EXP = sys.argv[1]

def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs); i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r

def spearman(x, y):
    rx, ry = rank(x), rank(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")

# Ae per task: media delle valutazioni esperte
ae = collections.defaultdict(list)
for r in csv.DictReader(open(WB_EXP, encoding="utf-8")):
    ae[str(int(r["Task ID"]))].append(int(r["Automation Capacity Rating"]))

# Nostri punteggi per task (chiave numerica O*NET)
staff = {}
for l in open(STAFF, encoding="utf-8"):
    x = json.loads(l)
    tid = x["task_id"].replace("ONET_TASK ", "").strip()
    staff[tid] = x

ov = sorted(set(ae) & set(staff), key=int)
print(f"task Ae: {len(ae)}  nostri: {len(staff)}  sovrapposti: {len(ov)}")
if not ov:
    sys.exit()

def media(x, voce):
    v = x["punteggi"].get(voce, [])
    return statistics.mean(v) if v else None

rows = []
for t in ov:
    x = staff[t]
    vals = {v: media(x, v) for v in ("k1", "k2", "k3", "r")}
    if any(vv is None for vv in vals.values()):
        continue
    vals["somma_k"] = vals["k1"] + vals["k2"] + vals["k3"]
    rows.append((t, statistics.mean(ae[t]), vals))

print(f"con tutti i punteggi: {len(rows)}")
y = [a for _, a, _ in rows]
for voce in ("k1", "k2", "k3", "r", "somma_k"):
    x = [v[voce] for _, _, v in rows]
    print(f"{voce:8s} rho vs Ae medio = {spearman(x, y):+.3f}")
