"""
Nemdeterminisztikus Véges Automata (NFA) determinizálása (DFA-vá alakítása)
részhalmazos konstrukcióval (subset construction / powerset construction).

================================================================================
1. ELMÉLETI HÁTTÉR (NFA -> DFA konverzió)
================================================================================
A formális nyelvek és automaták elméletében egy nemdeterminisztikus véges automata:
    M_NFA = (Q, Σ, δ_NFA, q0, F)
ahol:
    - Q: az állapotok véges halmaza
    - Σ: a bemeneti ábécé véges halmaza
    - δ_NFA: Q × Σ → P(Q) (vagyis 2^Q, az állapotok hatványhalmaza: egy állapotból
             egy szimbólumra akár 0, 1 vagy több célállapotba is vezethet átmenet)
    - q0 ∈ Q: kezdőállapot
    - F ⊆ Q: elfogadó (vég-) állapotok halmaza

A Rabin-Scott tétellel igazolható, hogy minden NFA-hoz létezik egy vele ekvivalens
determinisztikus véges automata (DFA), amely pontosan ugyanazt a nyelvet fogadja el:
    M_DFA = (Q', Σ, δ_DFA, q0', F')

A részhalmazos konstrukció szabályai:
    1. Új állapotok halmaza (Q'): Az NFA állapotainak részhalmazai, Q' ⊆ P(Q) = 2^Q.
       A gyakorlatban kizárólag a kezdőállapotból elérhető részhalmazokat képezzük le.
    2. Új kezdőállapot (q0'): Az eredeti kezdőállapotot tartalmazó egyelemű halmaz:
       s0 = {q0}.
    3. Új átmenetfüggvény (δ_DFA): Egy S ⊆ Q részhalmazból az 'a' szimbólum hatására
       elérhető összes NFA állapot uniója:
           δ_DFA(S, a) = ⋃_{q ∈ S} δ_NFA(q, a)
       (Ha az unió üres halmaz, az a csapdaállapotnak felel meg; a feladat előírása
       szerint ilyenkor az él ki sem kerül kiírásra.)
    4. Új elfogadó állapotok (F'): Minden olyan S részhalmaz elfogadó állapot a DFA-ban,
       amely tartalmaz legalább egy eredeti elfogadó állapotot:
           F' = { S ∈ Q' | S ∩ F ≠ ∅ }
"""

import argparse
import sys
from collections import deque
from pathlib import Path

# ==============================================================================
# 2. DINAMIKUS ÚTVONALKEZELÉS (sys.path)
# ==============================================================================
# Ha a fájlt közvetlenül indítjuk el (pl. a VS Code jobb felső Run / Lejátszás gombjával),
# a Python alapértelmezetten a fájl saját mappáját (problems) helyezi a keresési útvonal elejére.
# Emiatt a "from project.problem import Problem" csomag-import meghiúsulna (ModuleNotFoundError).
# A python-starter gyökérmappa sys.path-hez adásával biztosítjuk, hogy a kód mindkét módon működjön:
# önálló fájlként futtatva és a hivatalos "python -m project" csomagként indítva is.
_starter_dir = Path(__file__).resolve().parent.parent.parent
if str(_starter_dir) not in sys.path:
    sys.path.insert(0, str(_starter_dir))

from project.problem import Problem


class DFADetermizeProblem(Problem):
    """
    A Problem alaposztályból származtatott osztály, amely egy tetszőleges (akár nemdeterminisztikus)
    véges automatát determinisztikus DFA-vá alakít át részhalmazos konstrukció segítségével.
    """

    # ==========================================================================
    # 3. PARSER ÉS A KERETRENDSZER KAPCSOLATA
    # ==========================================================================
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Regisztrálja a feladathoz szükséges parancssori kapcsolót (--det).
        Az action='store_true' beállítás miatt ez egy logikai (flag) kapcsoló:
        ha megadják a parancssorban, értéke True lesz, egyébként False.
        """
        parser.add_argument(
            '--det',
            action='store_true',
            help='Transform NFA to DFA using subset construction',
        )

    def is_chosen_problem(self, args):
        """
        A keretrendszer (__main__.py) ezt a metódust hívja meg minden regisztrált Problem-en.
        Ha a felhasználó a --det kapcsolóval indította a programot, a keretrendszer
        ezt a feladatot választja ki futtatásra.
        """
        return bool(getattr(args, 'det', False))

    # ==========================================================================
    # 4. BEOLVASÁS, SZIGORÚ VALIDÁCIÓ ÉS DETERMINIZÁLÁS (run metódus)
    # ==========================================================================
    def run(self, args):
        input_file = args.input
        output_file = args.output

        # ----------------------------------------------------------------------
        # Fájl beolvasása és BOM (Byte Order Mark) kezelés
        # ----------------------------------------------------------------------
        # Az 'utf-8-sig' kódolás elengedhetetlen Windows környezetben:
        # automatikusan kiszűri a fájl elején esetlegesen megbúvó láthatatlan BOM fejlécet (\ufeff).
        # Sima 'utf-8' esetén ez a karakter hozzátapadna a legelső állapothoz (pl. '\ufeffq0'),
        # ami hibás azonosítást okozna.
        #
        # A splitlines() használata garantálja, hogy az üres sorok megmaradjanak:
        # Ha az elfogadó állapotok halmaza üres (F = ∅), a 4. sor egy üres sor.
        # Ha [l for l in f if l.strip()]-et használnánk, ez a sor elveszne,
        # és az 5. sor (az első átmenet) csúszna fel hibásan elfogadó állapotnak.
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            lines = f.read().splitlines()

        if len(lines) < 4:
            raise ValueError("A bemeneti fájlnak legalább 4 fejléc-sort kell tartalmaznia.")

        # ----------------------------------------------------------------------
        # Szigorú érvényesség-ellenőrzés (fejléc adatok)
        # ----------------------------------------------------------------------
        # 1. sor: Állapotok listája (Q)
        states_list = lines[0].split()
        states_set = set(states_list)
        if not states_set:
            raise ValueError("Az állapotok halmaza (1. sor) nem lehet üres.")

        # 2. sor: Bemeneti ábécé elemei (Σ)
        # Megtartjuk a listát az eredeti kiírási sorrendhez, és halmazt képzünk a gyors kereséshez.
        alphabet_list = lines[1].split()
        alphabet_set = set(alphabet_list)
        if not alphabet_set:
            raise ValueError("A bemeneti ábécé (2. sor) nem lehet üres.")

        # 3. sor: Kezdőállapot (q0)
        start_state = lines[2].strip()
        if start_state not in states_set:
            raise ValueError(f"A kezdőállapot ('{start_state}') nem szerepel a megadott állapotok között.")

        # 4. sor: Végállapotok listája (F ⊆ Q)
        accept_states_list = lines[3].split()
        accept_states_set = set(accept_states_list)
        for acc in accept_states_set:
            if acc not in states_set:
                raise ValueError(f"A megadott végállapot ('{acc}') nem szerepel az érvényes állapotok között.")

        # ----------------------------------------------------------------------
        # Átmenetek beolvasása és szigorú ellenőrzése (NFA átmenettábla)
        # ----------------------------------------------------------------------
        # Az 5. sortól kezdődnek az átmenetek: "honnan szimbólum hova".
        # Nemdeterminisztikus automatánál egy (forrás, szimbólum) párhoz több célállapot is tartozhat!
        # Emiatt célállapotok halmazát (set) tároljuk az értékeknél:
        # nfa_transitions[(src, sym)] = {dst1, dst2, ...}
        nfa_transitions = {}
        for line_num, line in enumerate(lines[4:], start=5):
            line_str = line.strip()
            if not line_str:
                continue  # Esetleges üres sorok kihagyása a fájl végén
            parts = line_str.split()
            if len(parts) != 3:
                raise ValueError(f"Hibás átmenet formátum a(z) {line_num}. sorban: '{line_str}' (3 elem várt).")
            src, sym, dst = parts

            # Szigorú érvényesség-ellenőrzés:
            # Csak a fejlécben deklarált állapotok és szimbólumok szerepelhetnek az átmenetekben!
            if src not in states_set:
                raise ValueError(f"Ismeretlen forrásállapot '{src}' a(z) {line_num}. sorban.")
            if sym not in alphabet_set:
                raise ValueError(f"Ismeretlen szimbólum '{sym}' a(z) {line_num}. sorban.")
            if dst not in states_set:
                raise ValueError(f"Ismeretlen célállapot '{dst}' a(z) {line_num}. sorban.")

            if (src, sym) not in nfa_transitions:
                nfa_transitions[(src, sym)] = set()
            nfa_transitions[(src, sym)].add(dst)

        # ======================================================================
        # 5. RÉSZHALMAZOS KONSTRUKCIÓ (BFS bejárással)
        # ======================================================================
        # Kezdőállapot: szigorúan az eredeti kezdőállapotot tartalmazó egyelemű halmaz: s0 = {start_state}.
        # A részhalmazokat immutábilis 'frozenset'-ként reprezentáljuk, így szótárkulcsként használhatók.
        initial_subset = frozenset([start_state])

        # Kétirányú leképezés a részhalmazok és az új állapotnevek között:
        # subset_to_name: {q0} -> 's0', {q1, q2} -> 's1', stb.
        # name_to_subset: 's0' -> {q0}, 's1' -> {q1, q2}, stb.
        subset_to_name = {initial_subset: "s0"}
        name_to_subset = {"s0": initial_subset}
        dfa_states = ["s0"]

        # Szélességi bejárás (BFS - Breadth-First Search) sora az elérhető állapotok felfedezésére:
        queue = deque([initial_subset])
        dfa_transitions = []

        # Az ábécé szimbólumait rendezett sorrendben járjuk be az átmeneteknél
        sorted_alphabet = sorted(alphabet_set)

        while queue:
            current_subset = queue.popleft()
            current_name = subset_to_name[current_subset]

            for sym in sorted_alphabet:
                # Az aktuális részhalmaz minden NFA-állapotából lekérjük a 'sym' szimbólumra
                # elérhető célállapotokat, és uniót képzünk: ⋃_{q ∈ S} δ_NFA(q, sym)
                target_subset = set()
                for q in current_subset:
                    if (q, sym) in nfa_transitions:
                        target_subset.update(nfa_transitions[(q, sym)])

                # Csapdaállapot kezelése:
                # Ha az unió üres (∅), nincs érvényes átmenet az adott szimbólumra.
                # A feladat előírása szerint ilyenkor az él KI SEM KERÜL KIÍRÁSRA.
                if not target_subset:
                    continue

                target_frozen = frozenset(target_subset)
                # Ha ez egy eddig még nem látott új részhalmaz, regisztráljuk a következő s-sorszámmal:
                if target_frozen not in subset_to_name:
                    new_name = f"s{len(dfa_states)}"  # s1, s2, s3...
                    subset_to_name[target_frozen] = new_name
                    name_to_subset[new_name] = target_frozen
                    dfa_states.append(new_name)
                    queue.append(target_frozen)

                # Determinisztikus átmenet rögzítése: (forrás, szimbólum, cél)
                dfa_transitions.append((current_name, sym, subset_to_name[target_frozen]))

        # ======================================================================
        # 6. RENDEZÉSI SZABÁLYOK ÉS KIMENET ÖSSZEÁLLÍTÁSA
        # ======================================================================
        # Szigorú előírás az átmenetek kiírási sorrendjére:
        #   1. Előbb a forráscsomópontok szerint (s0, s1, s2... számérték alapján!)
        #   2. Majd az él címkéje szerint (ábécérendben)
        #   3. Majd a célállomás sorszáma szerint
        # A lambda t: (int(t[0][1:]), t[1], int(t[2][1:])) garantálja a helyes numerikus rendezést
        # (így pl. s2 megelőzi s10-et, nem lexikografikusan s1, s10, s2 lesz).
        dfa_transitions.sort(key=lambda t: (int(t[0][1:]), t[1], int(t[2][1:])))

        # Új végállapotok meghatározása:
        # Azok az s-állapotok minősülnek elfogadónak a DFA-ban, amelyek részhalmaza
        # tartalmaz legalább egy eredeti NFA-végállapotot (S ∩ F ≠ ∅).
        dfa_accept_states = [
            s for s in dfa_states
            if any(q in accept_states_set for q in name_to_subset[s])
        ]

        # Kimeneti fájl sorainak összeállítása az elvárt formátum szerint:
        output_lines = [
            ' '.join(dfa_states),        # 1. sor: DFA állapotok listája (s0 s1 s2...)
            ' '.join(alphabet_list),     # 2. sor: Bemeneti ábécé elemei
            's0',                        # 3. sor: Kezdőállapot (szigorúan s0)
            ' '.join(dfa_accept_states), # 4. sor: Elfogadó állapotok (ha üres halmaz, üres sor)
        ]
        # 5. sortól: Rendezett determinisztikus állapotátmenetek
        for src, sym, dst in dfa_transitions:
            output_lines.append(f"{src} {sym} {dst}")

        # Eredmény kiírása 'utf-8' kódolással
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))


# ==============================================================================
# 7. KÖZVETLEN HELYI TESZTELÉS / FUTTATÁS BLOKK
# ==============================================================================
# Ez a blokk csak akkor fut le, ha a dfa_det.py fájlt közvetlenül indítják el
# (pl. a VS Code jobb felső Run / Lejátszás gombjával vagy a terminálból: py dfa_det.py),
# nem pedig csomagként importálva.
# Ilyenkor a run_all modulon keresztül mindkét házi feladatot sorban lefuttatja,
# és az eredményeket kiírja a terminálra, megkönnyítve az azonnali tesztelést.
# A hivatalos "python -m project" vagy az egyetemi automata tesztelő ezt a blokkot nem érinti.
if __name__ == '__main__':
    from run_all import run_all_problems
    run_all_problems()
