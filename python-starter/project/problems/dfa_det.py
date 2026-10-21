"""
Nemdeterminisztikus Véges Automata (NFA) determinizálása (DFA-vá alakítása)
részhalmazos konstrukcióval (subset construction / powerset construction).

Elméleti háttér:
A formális nyelvek és automaták elméletében egy NFA determinisztikussá alakítható a részhalmazos
konstrukció módszerével. Az új DFA állapotai az eredeti NFA állapotainak részhalmazai (2^Q elemei).
    - Kezdőállapot: s0 = {q0} (az eredeti kezdőállapotot tartalmazó egyelemű halmaz)
    - Állapotátmenetek: δ_DFA(S, a) = ⋃_{q ∈ S} δ_NFA(q, a)
    - Elfogadó állapotok: minden olyan S részhalmaz, amely tartalmaz legalább egy eredeti elfogadó állapotot (S ∩ F ≠ ∅)
    - Az elérhetetlen állapotokat elhagyjuk, és a csapdaállapotba (üres halmazba) vezető átmeneteket nem írjuk ki.
"""

import argparse
import sys
from collections import deque
from pathlib import Path

# ==============================================================================
# 1. DINAMIKUS ÚTVONALKEZELÉS (sys.path)
# ==============================================================================
# Biztosítja, hogy a fájl önállóan (pl. VS Code Run gombbal) és csomagként (python -m project)
# futtatva is megtalálja a 'project' modult a python-starter gyökérmappában.
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
    # 2. PARSER ÉS A KERETRENDSZER KAPCSOLATA
    # ==========================================================================
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Regisztrálja a feladathoz szükséges parancssori kapcsolót (--det).
        """
        parser.add_argument(
            '--det',
            action='store_true',
            help='Transform NFA to DFA using subset construction',
        )

    def is_chosen_problem(self, args):
        """
        Ellenőrzi, hogy a --det kapcsoló megadásra került-e a parancssorban.
        """
        return bool(getattr(args, 'det', False))

    # ==========================================================================
    # 3. FELDOLGOZÁS ÉS DETERMINIZÁLÁS (run metódus)
    # ==========================================================================
    def run(self, args):
        input_file = args.input
        output_file = args.output

        # Bemeneti fájl beolvasása 'utf-8-sig' kódolással (BOM karakterek kiszűrése)
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            lines = f.read().splitlines()

        if len(lines) < 4:
            raise ValueError("A bemeneti fájlnak legalább 4 sort kell tartalmaznia.")

        # ----------------------------------------------------------------------
        # Bemenet értelmezése és szigorú érvényesség-ellenőrzés
        # ----------------------------------------------------------------------
        # 1. sor: Állapotok listája
        states_list = lines[0].split()
        states_set = set(states_list)
        if not states_set:
            raise ValueError("Az állapotok halmaza nem lehet üres.")

        # 2. sor: Bemeneti ábécé elemei
        alphabet_list = lines[1].split()
        alphabet_set = set(alphabet_list)
        if not alphabet_set:
            raise ValueError("Az ábécé nem lehet üres.")

        # 3. sor: Kezdőállapot
        start_state = lines[2].strip()
        if start_state not in states_set:
            raise ValueError(f"A kezdőállapot ('{start_state}') nem szerepel a megadott állapotok között.")

        # 4. sor: Végállapotok listája
        accept_states_list = lines[3].split()
        accept_states_set = set(accept_states_list)
        for acc in accept_states_set:
            if acc not in states_set:
                raise ValueError(f"A végállapot ('{acc}') nem szerepel a megadott állapotok között.")

        # 5. sortól: Átmenetek beolvasása és ellenőrzése
        # NFA esetén egy (állapot, szimbólum) párhoz több célállapot is tartozhat:
        # nfa_transitions[(src, sym)] = set(dst1, dst2, ...)
        nfa_transitions = {}
        for line_num, line in enumerate(lines[4:], start=5):
            line_str = line.strip()
            if not line_str:
                continue
            parts = line_str.split()
            if len(parts) != 3:
                raise ValueError(f"Hibás átmenet formátum a(z) {line_num}. sorban: '{line_str}'")
            src, sym, dst = parts

            # Szigorú ellenőrzés: szerepelnek-e a megadott érvényes elemek között
            if src not in states_set:
                raise ValueError(f"Ismeretlen forrásállapot '{src}' a(z) {line_num}. sorban.")
            if sym not in alphabet_set:
                raise ValueError(f"Ismeretlen szimbólum '{sym}' a(z) {line_num}. sorban.")
            if dst not in states_set:
                raise ValueError(f"Ismeretlen célállapot '{dst}' a(z) {line_num}. sorban.")

            if (src, sym) not in nfa_transitions:
                nfa_transitions[(src, sym)] = set()
            nfa_transitions[(src, sym)].add(dst)

        # ----------------------------------------------------------------------
        # 4. RÉSZHALMAZOS KONSTRUKCIÓ (Subset construction)
        # ----------------------------------------------------------------------
        # A kezdőállapot szigorúan az eredeti kezdőállapotot tartalmazó egyelemű halmaz: s0 = {start_state}
        initial_subset = frozenset([start_state])

        subset_to_name = {initial_subset: "s0"}
        name_to_subset = {"s0": initial_subset}
        dfa_states = ["s0"]

        queue = deque([initial_subset])
        dfa_transitions = []

        # Az ábécé elemei rendezve a bejáráshoz
        sorted_alphabet = sorted(alphabet_set)

        while queue:
            current_subset = queue.popleft()
            current_name = subset_to_name[current_subset]

            for sym in sorted_alphabet:
                # Az adott szimbólumra elérhető összes célállapot uniója: ⋃_{q ∈ S} δ(q, sym)
                target_subset = set()
                for q in current_subset:
                    if (q, sym) in nfa_transitions:
                        target_subset.update(nfa_transitions[(q, sym)])

                # Ahol nincs átmenet (üres halmaz), az él nem kerül kiírásra
                if not target_subset:
                    continue

                target_frozen = frozenset(target_subset)
                # Új részhalmaz felfedezése esetén új állapot létrehozása: s1, s2, ...
                if target_frozen not in subset_to_name:
                    new_name = f"s{len(dfa_states)}"
                    subset_to_name[target_frozen] = new_name
                    name_to_subset[new_name] = target_frozen
                    dfa_states.append(new_name)
                    queue.append(target_frozen)

                dfa_transitions.append((current_name, sym, subset_to_name[target_frozen]))

        # ----------------------------------------------------------------------
        # 5. RENDEZÉS ÉS KIMENET ÖSSZEÁLLÍTÁSA
        # ----------------------------------------------------------------------
        # Előírás: előbb a forráscsomópontok szerint (s0, s1...),
        # majd az él címkéje szerint (ábécé sorrendben), majd a célállomás szerint.
        dfa_transitions.sort(key=lambda t: (int(t[0][1:]), t[1], int(t[2][1:])))

        # Végállapotok: azok az s-állapotok, amelyek tartalmaznak legalább egy eredeti végállapotot
        dfa_accept_states = [
            s for s in dfa_states
            if any(q in accept_states_set for q in name_to_subset[s])
        ]

        # Kimeneti sorok összeállítása a specifikáció szerint
        output_lines = [
            ' '.join(dfa_states),        # 1. sor: Állapotok listája (s0 s1 s2...)
            ' '.join(alphabet_list),     # 2. sor: Bemeneti ábécé elemei
            's0',                        # 3. sor: Kezdőállapot (szigorúan s0)
            ' '.join(dfa_accept_states), # 4. sor: Végállapotok listája
        ]
        for src, sym, dst in dfa_transitions:
            output_lines.append(f"{src} {sym} {dst}")

        # Kiírás a megadott kimeneti fájlba 'utf-8' kódolással
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))


# ==============================================================================
# 6. KÖZVETLEN HELYI TESZTELÉS / FUTTATÁS BLOKK
# ==============================================================================
# Ez a blokk teszi lehetővé a közvetlen futtatást a VS Code Run gombjával vagy terminálból.
if __name__ == '__main__':
    from run_all import run_both_problems
    run_both_problems()

