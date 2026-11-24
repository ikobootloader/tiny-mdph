import re

lines = open(r"C:\Users\fredm\AppData\Local\Temp\eval_full.log", encoding="utf-8").readlines()
mauvaise = [l for l in lines if "[mauvaise fiche" in l]
absent = [l for l in lines if "[absent du top 3]" in l]


def is_template(l):
    return (
        "mais à quoi cela renvoie" in l
        or "Pour mon père, est-ce envisageable" in l
        or bool(re.search(r" et (peut-on|pendant combien|qui peut|comment)", l))
    )


m_tpl = sum(1 for l in mauvaise if is_template(l))
a_tpl = sum(1 for l in absent if is_template(l))
print(f"mauvaise fiche sûre : {len(mauvaise)} dont {m_tpl} issues de gabarits réutilisés -> {len(mauvaise) - m_tpl} hors gabarits")
print(f"absent du top 3     : {len(absent)} dont {a_tpl} issues de gabarits réutilisés -> {len(absent) - a_tpl} hors gabarits")

total = 645
abstention_hors_hc = 458
adj_mauvaise = len(mauvaise) - m_tpl
adj_top3_fail = len(absent) - a_tpl
adj_top3_total = abstention_hors_hc - a_tpl
print()
print(f"Taux ajusté 'mauvaise fiche sûre' (hors gabarits) : {adj_mauvaise}/{total} = {100 * adj_mauvaise / total:.2f}%  (seuil <=2%)")
print(f"Taux ajusté 'bonne fiche top3' (hors gabarits)    : {adj_top3_total - adj_top3_fail}/{adj_top3_total} = {100 * (adj_top3_total - adj_top3_fail) / adj_top3_total:.1f}%  (seuil >=90%)")
