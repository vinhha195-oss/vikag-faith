"""Two-tier checker: a cheap NLI verifier decides confident claims, the 7B judge decides the rest.

For each budget b (share of claims sent to the judge), the claims whose verifier score lies closest to the support
threshold go to the judge. A second rule abstains when the two checkers disagree, which gives a coverage/risk curve.
Writes outputs/analysis/cascade.json. results.json is not touched.
"""

import json

import numpy as np

from s11_ieee_extra import TH, catch, gold, hk, human, macro_f1, pred, score, test, usable
from s10_dot2 import decide
from common import OUT, SEED

OUTF = OUT / "analysis" / "cascade.json"
BUDGETS = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
J7 = pred["j7"]


def boot(y, p, n=1000):
    rng = np.random.default_rng(SEED); y, p = np.array(y), np.array(p)
    v = [macro_f1(y[i], p[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(n))]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def cascade(name, budget, ks):
    r = score(name); ts, tc = TH[name]
    ks = [k for k in ks if k in J7]
    margin = sorted(ks, key=lambda k: abs(r[k][name]["entail"] - ts))
    sent = set(margin[:int(round(budget * len(ks)))])
    return {k: (J7[k] if k in sent else decide(r[k][name]["entail"], r[k][name]["contra"], ts, tc)) for k in ks}


out = {"budgets": BUDGETS, "verifiers": {}}
for name in ("xft_v1", "ft_v1", "ft20full_v1"):
    rows = []
    for b in BUDGETS:
        row = {"budget": b}
        for tag, ks, ref in (("silver", test, gold), ("human", hk, human)):
            p = cascade(name, b, ks)
            kk = list(p)
            row[tag] = {"macro_f1": macro_f1([ref[k] for k in kk], [p[k] for k in kk]), **catch(p, kk, ref)}
            if b in (0.3, 0.5):
                row[tag]["ci95"] = boot([ref[k] for k in kk], [p[k] for k in kk])
        rows.append(row)
    out["verifiers"][name] = rows

# abstain when the verifier and the judge disagree on supported vs not supported
out["abstain"] = {}
for name in ("xft_v1", "ft_v1"):
    row = {}
    for tag, ks, ref in (("silver", test, gold), ("human", hk, human)):
        ks = [k for k in ks if k in J7 and k in pred[name]]
        agree = [k for k in ks if (J7[k] == "supported") == (pred[name][k] == "supported")]
        acc_bin = np.mean([(J7[k] == "supported") == (ref[k] == "supported") for k in agree])
        acc_all = np.mean([(J7[k] == "supported") == (ref[k] == "supported") for k in ks])
        row[tag] = {"coverage": len(agree) / len(ks), "n": len(ks), "binary_acc_kept": float(acc_bin), "binary_acc_judge_all": float(acc_all),
                    "macro_f1_kept": macro_f1([ref[k] for k in agree], [J7[k] for k in agree])}
    out["abstain"][name] = row
out["judge_alone"] = {t: macro_f1([ref[k] for k in ks if k in J7], [J7[k] for k in ks if k in J7]) for t, ks, ref in (("silver", test, gold), ("human", hk, human))}
json.dump(out, open(OUTF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for name, rows in out["verifiers"].items():
    print(name)
    for r in rows:
        print(f"  b={r['budget']:.1f} silver {r['silver']['macro_f1']:.3f} {r['silver']['caught']}/{r['silver']['wrong']} fa {r['silver']['false_alarm']}  "
              f"human {r['human']['macro_f1']:.3f} {r['human']['caught']}/{r['human']['wrong']} fa {r['human']['false_alarm']} {r['human'].get('ci95', '')}")
print("judge alone", out["judge_alone"])
print("abstain", json.dumps(out["abstain"], indent=0))
