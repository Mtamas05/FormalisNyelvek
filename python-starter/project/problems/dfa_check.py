"""
Determinisztikus Véges Automata (DFA - Deterministic Finite Automaton) szimulációja.

Elméleti háttér:
A formális nyelvek és automaták elméletében a determinisztikus véges automata egy 5-ösként definiálható:
    M = (Q, Σ, δ, q0, F)
ahol:
    - Q: az állapotok véges, nem üres halmaza (states)
    - Σ: a bemeneti ábécé véges halmaza (alphabet)
    - δ: az állapotátmenet-függvény, δ: Q × Σ → Q (transitions)
         (Determinisztikus: egy adott állapotból egy adott bemeneti szimbólumra legfeljebb egy átmenet létezhet)
    - q0: a kezdőállapot, q0 ∈ Q (start_state)
    - F: az elfogadó (vagy vég-) állapotok halmaza, F ⊆ Q (accept_states)
"""

import argparse
import sys
from pathlib import Path

# ==============================================================================
# 1. DINAMIKUS ÚTVONALKEZELÉS (sys.path)
# ==============================================================================
# Ha a fájlt közvetlenül indítjuk el (pl. a VS Code Run/Lejátszás gombjával vagy terminálból),
# a Python alapértelmezetten a fájl saját mappáját (problems) helyezi a keresési útvonal elejére.
# Emiatt a "from project.problem import Problem" csomag-import sikertelen lenne (ModuleNotFoundError).
# A python-starter gyökérmappa sys.path-hez adásával biztosítjuk, hogy a kód mindkét módon működjön:
# mind önálló fájlként futtatva, mind a hivatalos "python -m project" csomagként indítva.
_starter_dir = Path(__file__).resolve().parent.parent.parent
if str(_starter_dir) not in sys.path:
    sys.path.insert(0, str(_starter_dir))

from project.problem import Problem


class DFACheckProblem(Problem):
    """
    A Problem alaposztályból származtatott osztály, amely a megadott DFA leírást
    beolvasva ellenőrzi, hogy a megadott szavak levezethetők-e és elfogadó állapotba jutnak-e.
    """

    # ==========================================================================
    # 2. PARSER ÉS A KERETRENDSZER KAPCSOLATA
    # ==========================================================================
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Regisztrálja a feladathoz szükséges parancssori kapcsolót (--check).
        A --check szöveges értékként kapja meg a vesszővel elválasztott szavakat (pl. "10101,111,001").
        """
        parser.add_argument(
            '--check',
            type=str,
            help='Check comma-separated words against the DFA',
        )

    def is_chosen_problem(self, args):
        """
        A keretrendszer (__main__.py) ezt a metódust hívja meg minden Problem példányon.
        Ha a parancssorban megadták a --check kapcsolót (értéke nem None), akkor ezt a
        problémát választja ki futtatásra.
        """
        return getattr(args, 'check', None) is not None

    # ==========================================================================
    # 3. SZIMULÁCIÓ ÉS FELDOLGOZÁS (run metódus)
    # ==========================================================================
    def run(self, args):
        input_file = args.input
        output_file = args.output
        # A megadott szavak feldolgozása a vesszők mentén
        words_to_check = args.check.split(',')

        # ----------------------------------------------------------------------
        # Fájl beolvasása és BOM (Byte Order Mark) kezelés
        # ----------------------------------------------------------------------
        # Az 'utf-8-sig' kódolás elengedhetetlen Windows rendszereken vagy bizonyos
        # szövegszerkesztők használatakor: automatikusan és észrevétlenül eltávolítja
        # a fájl legelején található láthatatlan BOM fejlécet (\ufeff).
        # Sima 'utf-8' esetén ez a karakter hozzáragadna a legelső állapot nevéhez (pl. '\ufeffq0'),
        # ami hibás működést okozna az állapotok és átmenetek egyeztetésénél.
        #
        # A splitlines() használata garantálja, hogy a sorok indexelése pontos marad:
        # Ha az elfogadó állapotok halmaza üres (F = ∅), a 4. sor egy üres sor.
        # Sima üresszűrés (pl. [l for l in f if l.strip()]) elnyelné ezt a sort,
        # és az 5. sor (az első átmenet) csúszna fel elfogadó állapotnak!
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            lines = f.read().splitlines()

        # A fájl szerkezetének leképezése a DFA formális elemeire:
        # 1. sor: Állapotok listája (Q)
        states = lines[0].split() if len(lines) > 0 else []
        # 2. sor: Ábécé elemei (Σ) - halmazként tároljuk a gyors kereséshez
        alphabet = set(lines[1].split()) if len(lines) > 1 else set()
        # 3. sor: Kezdőállapot (q0)
        start_state = lines[2].strip() if len(lines) > 2 else ''
        # 4. sor: Elfogadó állapotok halmaza (F ⊆ Q) - halmaz a gyors O(1) ellenőrzéshez
        accept_states = set(lines[3].split()) if len(lines) > 3 else set()

        # ----------------------------------------------------------------------
        # 4. ÁTMENETTÁBLA FELÉPÍTÉSE (δ függvény reprezentációja)
        # ----------------------------------------------------------------------
        # Az 5. sortól kezdődően találhatók az állapotátmenetek: "honnan szimbólum hova".
        # A leképezést egy Python szótárban (hash map) tároljuk:
        # Kulcs: (forrás_állapot, szimbólum) pár
        # Érték: cél_állapot
        # Ez a struktúra O(1) konstans idejű elérést biztosít az átmenet lekérdezésekor.
        transitions = {}
        for line in lines[4:]:
            parts = line.strip().split()
            if len(parts) == 3:
                src, sym, dst = parts
                transitions[(src, sym)] = dst

        # ----------------------------------------------------------------------
        # 5. DFA SZIMULÁCIÓS CIKLUS
        # ----------------------------------------------------------------------
        results = []
        for word in words_to_check:
            # Minden szót a kezdőállapotból (q0) indítunk
            current_state = start_state
            valid = True

            # Karakterenként lépkedünk a szón végig (δ iteratív kiterjesztése)
            for char in word:
                # Érvénytelen az átmenet, ha:
                # 1. A karakter nem szerepel a megadott ábécében (char ∉ Σ), VAGY
                # 2. Az aktuális állapotból az adott karakterre nincs átmenet definíció
                if char not in alphabet or (current_state, char) not in transitions:
                    valid = False
                    break
                # Sikeres átmenet: átlépünk a következő állapotba: q' = δ(q, char)
                current_state = transitions[(current_state, char)]

            # Elfogadási feltétel:
            # 1. A szó beolvasása során nem volt érvénytelen átmenet (valid == True)
            # 2. A szó végén elért állapot az elfogadó állapotok közé tartozik (current_state ∈ F)
            # Megjegyzés: Üres szó (ε) esetén a belső ciklus nem fut le, így valid=True marad,
            # és az automata akkor és csak akkor fogadja el, ha q0 ∈ F.
            if valid and current_state in accept_states:
                results.append("IGEN")
            else:
                results.append("NEM")

        # ----------------------------------------------------------------------
        # 6. KIMENET KIÍRÁSA
        # ----------------------------------------------------------------------
        # Az eredményeket soronként 'utf-8' kódolással írjuk ki az args.output fájlba
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))


# ==============================================================================
# 7. KÖZVETLEN HELYI TESZTELÉS / FUTTATÁS BLOKK
# ==============================================================================
# Ez a blokk csak akkor fut le, ha a dfa_check.py fájlt közvetlenül indítják el
# (pl. a VS Code jobb felső Run / Lejátszás gombjával), nem pedig modulként importálva.
# Ha nincsenek parancssori argumentumok, automatikusan beállítja az alapértelmezett
# fájlokat és tesztszavakat, lefuttatja a Main osztályt, majd kiírja az eredményt a terminálra.
# A hivatalos "python -m project" vagy az automatikus tesztelő ezt a blokkot nem érinti.
if __name__ == '__main__':
    from run_all import run_both_problems
    run_both_problems()
