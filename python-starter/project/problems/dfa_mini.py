"""
Determinisztikus Véges Automata (DFA - Deterministic Finite Automaton) minimalizálása
partíció-finomítási / Moore-féle állapotekvivalencia algoritmussal.

================================================================================
1. ELMÉLETI HÁTTÉR (DFA Minimalizálás)
================================================================================
A Myhill-Nerode tétel és az automaták elmélete kimondja, hogy minden reguláris nyelvhez
létezik egy állapotszámát tekintve minimális determinisztikus véges automata (DFA),
amely izomorfia erejéig (az állapotok átnevezésétől eltekintve) egyértelmű.

Egy DFA minimális, ha:
    1. Nem tartalmaz a kezdőállapotból elérhetetlen (felesleges) állapotokat.
    2. Nem tartalmaz egymással ekvivalens (megkülönböztethetetlen) állapotpárokat.

Két állapot (p, q ∈ Q) ekvivalens (p ≡ q), ha bármely w ∈ Σ* bemeneti szóra:
    δ*(p, w) ∈ F  akkor és csak akkor, ha  δ*(q, w) ∈ F.

A minimalizálás lépései (Moore-algoritmus):
    1. lépés - Elérhetetlen állapotok törlése:
       Kezdőállapotból (q0) kiindulva egy gráfbejárással (BFS/DFS) meghatározzuk
       az elérhető állapotok halmazát (Q_reach). A nem elérhető állapotokat és
       az azokhoz kapcsolódó átmeneteket végleg eldobjuk.

    2. lépés - Kiinduló partíció létrehozása (0-ekvivalencia):
       A halmazt két diszjunkt osztályra bontjuk:
           P_0 = { F_reach, Q_reach \\ F_reach }
       (Végállapotok és nem-végállapotok, hiszen az üres szóval ε azonnal
       megkülönböztethetők egymástól).

    3. lépés - Partíciók iteratív finomítása (k-ekvivalencia):
       Két állapot (p, q) egy osztályban marad a következő lépésben, ha azonos
       osztályban voltak, ÉS minden 'a' ∈ Σ szimbólumra az átmeneteik:
           δ(p, a) és δ(q, a)
       az aktuális partíció azonos blokkjába mutatnak.
       Az iterációt addig ismételjük, amíg a partíciók száma nem nő (stabil állapot).

    4. lépés - Új állapotok és átmenetek képzése:
       Minden kapott ekvivalencia-osztály egyetlen állapotot alkot a minimalizált DFA-ban.
       - Állapot elnevezése: Az osztályba tartozó eredeti állapotok közül a legkisebb
         sorszámú kapja a reprezentáns szerepét (pl. {q1, q5} -> 's1').
       - Állapotok jelölése: Minden állapot neve 's' előtaggal rendelkezik.
       - Átmenetek: Szigorúan rendezve (forrásállapot, él címke, célállapot szerint).
"""

import argparse
import re
import sys
from collections import deque
from pathlib import Path

# ==============================================================================
# 2. DINAMIKUS ÚTVONALKEZELÉS (sys.path)
# ==============================================================================
# Ha a fájlt közvetlenül indítjuk el (pl. a VS Code jobb felső Run gombjával),
# a Python alapértelmezetten a fájl saját mappáját (problems) helyezi a keresési útvonal elejére.
# Emiatt a "from project.problem import Problem" csomag-import hibát dobna (ModuleNotFoundError).
# A python-starter gyökérmappa sys.path-hez adásával biztosítjuk, hogy a modul önállóan
# és a hivatalos "python -m project" csomagként indítva is hibátlanul megtalálja a keretrendszert.
_starter_dir = Path(__file__).resolve().parent.parent.parent
if str(_starter_dir) not in sys.path:
    sys.path.insert(0, str(_starter_dir))

from project.problem import Problem


class DFAMinimizeProblem(Problem):
    """
    A Problem alaposztályból származtatott osztály, amely egy bemeneti DFA-t
    minimalizál az elérhetetlen állapotok kiszűrésével és az ekvivalens állapotok
    partíció-finomításos (Moore) összevonásával.
    """

    # ==========================================================================
    # 3. PARSER ÉS A KERETRENDSZER KAPCSOLATA
    # ==========================================================================
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Regisztrálja a minimalizáláshoz szükséges parancssori kapcsolót (--mini).
        Az action='store_true' miatt logikai értékként (flag) működik.
        """
        parser.add_argument(
            '--mini',
            action='store_true',
            help='Minimize DFA by removing unreachable states and merging equivalent states',
        )

    def is_chosen_problem(self, args):
        """
        A keretrendszer (__main__.py) ezt a metódust hívja meg a feladat azonosítására.
        Ha a --mini kapcsoló szerepel a parancssorban, a program ezt a feladatot hajtja végre.
        """
        return bool(getattr(args, 'mini', False))

    # ==========================================================================
    # 4. FŐ FELDOLGOZÁSI FOLYAMAT (run metódus)
    # ==========================================================================
    def run(self, args):
        input_file = args.input
        output_file = args.output

        # ----------------------------------------------------------------------
        # Fájl beolvasása és BOM (Byte Order Mark) kezelése
        # ----------------------------------------------------------------------
        # Az 'utf-8-sig' kódolás automatikusan kiszűri a Windows szerkesztők által
        # esetlegesen beszúrt láthatatlan BOM fejlécet (\ufeff), így a legelső állapot
        # neve nem sérül (pl. nem lesz '\ufeffq0').
        #
        # A splitlines() használata kötelező: ha az elfogadó állapotok halmaza üres (F = ∅),
        # a 4. sor egy üres sor marad, amit nem szabad eldobni!
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

        # 2. sor: Bemeneti ábécé elemei (Σ) - az eredeti kiírási sorrendet megőrizzük
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
        # Átmenetek beolvasása és szigorú ellenőrzése
        # ----------------------------------------------------------------------
        # Az 5. sortól kezdődnek az átmenetek: "<honnan> <szimbólum> <hova>".
        transitions = {}
        for line_num, line in enumerate(lines[4:], start=5):
            line_str = line.strip()
            if not line_str:
                continue
            parts = line_str.split()
            if len(parts) != 3:
                raise ValueError(f"Hibás átmenet formátum a(z) {line_num}. sorban: '{line_str}' (3 elem várt).")
            src, sym, dst = parts

            # Szigorú validáció: csak a deklarált elemek szerepelhetnek
            if src not in states_set:
                raise ValueError(f"Ismeretlen forrásállapot '{src}' a(z) {line_num}. sorban.")
            if sym not in alphabet_set:
                raise ValueError(f"Ismeretlen szimbólum '{sym}' a(z) {line_num}. sorban.")
            if dst not in states_set:
                raise ValueError(f"Ismeretlen célállapot '{dst}' a(z) {line_num}. sorban.")

            transitions[(src, sym)] = dst

        # ======================================================================
        # 5. ALGORITMUS 1. LÉPÉS: ELÉRHTETLEN ÁLLAPOTOK ELTÁVOLÍTÁSA
        # ======================================================================
        # Szélességi bejárással (BFS) felderítjük a kezdőállapotból elérhető állapotokat.
        reachable = set([start_state])
        queue = deque([start_state])
        while queue:
            curr = queue.popleft()
            for sym in alphabet_list:
                if (curr, sym) in transitions:
                    nxt = transitions[(curr, sym)]
                    if nxt not in reachable:
                        reachable.add(nxt)
                        queue.append(nxt)

        # Csak az elérhető állapotokat és átmeneteket tartjuk meg
        reachable_states = [s for s in states_list if s in reachable]
        reachable_accept_states = set(s for s in accept_states_set if s in reachable)
        reachable_transitions = {k: v for k, v in transitions.items() if k[0] in reachable}

        # ======================================================================
        # 6. ALGORITMUS 2. LÉPÉS: PARTÍCIÓ-FINOMÍTÁS (MOORE-MÓDSZER)
        # ======================================================================
        # Kezdeti partíció: Elfogadó és nem-elfogadó állapotok szétválasztása
        non_accept = [s for s in reachable_states if s not in reachable_accept_states]
        accept = [s for s in reachable_states if s in reachable_accept_states]

        partition = []
        if non_accept:
            partition.append(set(non_accept))
        if accept:
            partition.append(set(accept))

        def get_block_index(state, current_partition):
            """Megadja, hogy egy adott állapot a partíció hányadik blokkjában található."""
            for idx, blk in enumerate(current_partition):
                if state in blk:
                    return idx
            return -1  # Nincs átmenet

        # Finomítási ciklus: addig bontjuk a blokkokat, amíg a partíció stabilizálódik
        while True:
            new_partition = []
            for block in partition:
                # Minden állapot átmenet-aláírását (signature) elkészítjük az aktuális partíció alapján
                signatures = {}
                for state in block:
                    sig = []
                    for sym in alphabet_list:
                        nxt = reachable_transitions.get((state, sym), None)
                        sig.append(get_block_index(nxt, partition) if nxt is not None else -1)
                    sig_tuple = tuple(sig)
                    signatures.setdefault(sig_tuple, set()).add(state)
                # Az azonos aláírással rendelkező állapotok maradnak egy blokkban
                new_partition.extend(signatures.values())

            # Ha a blokkok száma nem változott, elértük a minimális partíciót
            if len(new_partition) == len(partition):
                break
            partition = new_partition

        # ======================================================================
        # 7. ALGORITMUS 3. LÉPÉS: ÁLLAPOTOK ELNEVEZÉSE ÉS REPREZENTÁCIÓ
        # ======================================================================
        # Szabály: Az összevont csoportban szereplő eredeti állapotok közül a legkisebb
        # sorszámút választjuk reprezentánsnak, és 's' betűvel jelöljük (pl. q1 -> s1).
        def state_sort_key(s):
            m = re.search(r'\d+', s)
            return (int(m.group()) if m else 999999, s)

        def to_s_name(orig_state):
            m = re.search(r'\d+', orig_state)
            return f's{m.group()}' if m else f's{orig_state}'

        state_to_new_name = {}
        new_states_list = []

        for block in partition:
            # A csoport legkisebb sorszámú állapota
            rep = min(block, key=state_sort_key)
            new_name = to_s_name(rep)
            for s in block:
                state_to_new_name[s] = new_name
            new_states_list.append(new_name)

        # Az új állapotok növekvő sorszám szerint rendezve
        new_states_list.sort(key=state_sort_key)

        # Új kezdőállapot: az a csoportnév, amely tartalmazza az eredeti kezdőállapotot
        new_start_state = state_to_new_name[start_state]

        # Új végállapotok: azok a csoportok, amelyek eredetileg elfogadó állapotot tartalmaznak
        new_accept_states = sorted(
            list(set(state_to_new_name[s] for s in reachable_accept_states)),
            key=state_sort_key
        )

        # Új determinisztikus átmenetek képzése duplikáció nélkül
        new_transitions_set = set()
        for (src, sym), dst in reachable_transitions.items():
            new_transitions_set.add((state_to_new_name[src], sym, state_to_new_name[dst]))

        # Szigorú rendezés:
        # 1. Forrásállapot neve (sorszáma) szerint
        # 2. Él címkéje (szimbólum) szerint ábécérendben
        # 3. Célállapot neve (sorszáma) szerint
        sorted_transitions = sorted(
            list(new_transitions_set),
            key=lambda t: (state_sort_key(t[0]), t[1], state_sort_key(t[2]))
        )

        # ======================================================================
        # 8. KIMENET ÖSSZEÁLLÍTÁSA ÉS KIÍRÁSA
        # ======================================================================
        output_lines = [
            ' '.join(new_states_list),      # 1. sor: Új minimalizált s-állapotok
            ' '.join(alphabet_list),        # 2. sor: Bemeneti ábécé elemei eredeti sorrendben
            new_start_state,                # 3. sor: Új kezdőállapot
            ' '.join(new_accept_states),    # 4. sor: Új végállapotok (üres halmaz esetén üres sor)
        ]
        for src, sym, dst in sorted_transitions:
            output_lines.append(f"{src} {sym} {dst}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))


# ==============================================================================
# 9. KÖZVETLEN HELYI TESZTELÉS / FUTTATÁS BLOKK
# ==============================================================================
if __name__ == '__main__':
    from run_all import run_all_problems
    run_all_problems()

