"""
Reguláris kifejezések alkalmazása Android logfájlok elemzésére (Logcat feldolgozás).

================================================================================
1. ELMÉLETI HÁTTÉR (Reguláris kifejezések és automaták kapcsolata)
================================================================================
A Kleene-tétel értelmében a reguláris kifejezések (Regex) és a véges állapotú automaták
(DFA / NFA) leíróereje azonos: pontosan a 3-as típusú (reguláris) nyelvek osztályát
definiálják a Chomsky-féle hierarchiában.

A gyakorlatban a reguláris kifejezések a mintaillesztés és szövegfeldolgozás
legalapvetőbb eszközei. Ebben a feladatban egy valós Android 'logcat' naplóállományt
dolgozunk fel KIZÁRÓLAG reguláris kifejezésekkel (re modul), szigorúan elkerülve a
beépített string-manipulációs függvények (split, find, in, index stb.) használatát.

Egy Android logcat sor általános formátuma:
    <Dátum> <Idő> <PID> <TID> <Szint> <Tag>: <Üzenet>
Példa:
    10-15 10:18:47.782   221   221 I lowmemorykiller: Process polling is supported
ahol:
    - Dátum: MM-DD formátum (pl. 10-15)
    - Idő: HH:MM:SS.mmm (pl. 10:18:47.782)
    - PID: Process ID (folyamatazonosító, pl. 221)
    - TID: Thread ID (szálazonosító, pl. 221 - ha PID == TID, akkor a fő szálon fut)
    - Szint: Naplózási szint (V: Verbose, D: Debug, I: Info, W: Warning, E: Error, F: Fatal)
    - Tag: A naplózó komponens vagy osztály neve (pl. lowmemorykiller, PackageManager)
    - Üzenet: A kettőspont utáni tetszőleges leíró szöveg vagy hiba stack trace.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# ==============================================================================
# 2. DINAMIKUS ÚTVONALKEZELÉS (sys.path)
# ==============================================================================
# Ha a fájlt közvetlenül indítjuk el (pl. VS Code Run gombbal vagy terminálból),
# a Python a fájl saját mappáját (problems) tenné a keresési útvonal elejére.
# A python-starter gyökérmappa sys.path-hez adásával garantáljuk, hogy a modul
# önállóan és a hivatalos "python -m project" csomagként indítva is működjön.
_starter_dir = Path(__file__).resolve().parent.parent.parent
if str(_starter_dir) not in sys.path:
    sys.path.insert(0, str(_starter_dir))

from project.problem import Problem


class RegexProblem(Problem):
    """
    A Problem alaposztályból származtatott osztály, amely az Android logcat fájlokat
    kizárólag Python reguláris kifejezésekkel (re modul) elemzi ki az 1-5 alfeladat szerint.
    """

    # ==========================================================================
    # 3. PARSER ÉS A KERETRENDSZER KAPCSOLATA
    # ==========================================================================
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Regisztrálja a feladathoz szükséges parancssori kapcsolót (--rgx).
        A --rgx egy egész számot (1-5) vár paraméterként az elvégzendő alfeladathoz.
        """
        parser.add_argument(
            '--rgx',
            type=int,
            help='Regex problem number 1-5',
        )

    def is_chosen_problem(self, args):
        """
        A keretrendszer (__main__.py) ezt a metódust hívja meg minden Problem példányon.
        Ha az args.rgx meg van adva (nem None), akkor ezt a feladatot választja ki.
        """
        return getattr(args, 'rgx', None) is not None

    # ==========================================================================
    # 4. FŐ FELDOLGOZÁSI FOLYAMAT (run metódus)
    # ==========================================================================
    def run(self, args):
        input_file = args.input
        output_file = args.output
        task_id = args.rgx

        # Bemeneti logfájl beolvasása 'utf-8-sig' kódolással (BOM fejléc automatikus kiszűrése)
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            log_text = f.read()

        # ======================================================================
        # 1. ALFELADAT (--rgx 1): Logcat sorok szűrése és számolása 10 szempontból
        # ======================================================================
        # Minden mintára a re.findall() függvényt használjuk re.MULTILINE módban.
        # A re.MULTILINE hatására a ^ és $ horgonyok minden egyes sor elejére és végére
        # illeszkednek, nem csak a teljes szöveg elejére/végére.
        if task_id == 1:
            # 1.1: 10. hó 15-én keletkezett sorok száma
            # Minta: a sor kezdetén (^) a '10-15' dátum szerepel.
            p1 = r'^10-15.*'
            c1 = len(re.findall(p1, log_text, re.MULTILINE))

            # 1.2: 10. hó 15-én pontosan 10:18:51-kor keletkezett sorok száma
            # Minta: a sor '10-15 10:18:51.' időbélyeggel indul.
            p2 = r'^10-15 10:18:51\..*'
            c2 = len(re.findall(p2, log_text, re.MULTILINE))

            # 1.3: Az 51. másodpercben keletkezett sorok (függetlenül a perctől)
            # Minta: \d{2}:\d{2}:51\. formátumú időpont a sor elején.
            p3 = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:51\..*'
            c3 = len(re.findall(p3, log_text, re.MULTILINE))

            # 1.4: lowmemorykiller tag-et tartalmazó sorok száma
            # Minta: 'lowmemorykiller' literális szó keresése.
            p4 = r'lowmemorykiller'
            c4 = len(re.findall(p4, log_text))

            # 1.5: 10:18:51-kor keletkező, 221-es PID-ű sorok száma
            # Minta: 10:18:51 idő és az utána lévő 221 folyamatazonosító.
            p5 = r'^\d{2}-\d{2}\s+10:18:51\.\d+\s+221\s+.*'
            c5 = len(re.findall(p5, log_text, re.MULTILINE))

            # 1.6: Hibát (Error, 'E') tartalmazó logsorok száma
            # Minta: a naplózási szint oszlopában 'E' betű áll.
            p6 = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+E\s+.*'
            c6 = len(re.findall(p6, log_text, re.MULTILINE))

            # 1.7: Warningok ('W'), amelyeket a PackageManager küld
            # Minta: 'W' naplózási szint, amelyet közvetlenül a 'PackageManager' tag követ.
            p7 = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+W\s+PackageManager.*'
            c7 = len(re.findall(p7, log_text, re.MULTILINE))

            # 1.8: ExoPlayer-es Debug ('D') logsorok száma
            # Minta: 'D' szint és a sorban szerepel az 'ExoPlayer' komponens.
            p8 = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+D\s+.*ExoPlayer.*'
            c8 = len(re.findall(p8, log_text, re.MULTILINE))

            # 1.9: Java állománypozíciót tartalmazó hibák és warningok ([EW] .*\.java:\d+)
            # Minta: [EW] karakterosztály (Error vagy Warning), majd '.java:' fájlpozíció.
            p9 = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+[EW]\s+.*\.java:\d+'
            c9 = len(re.findall(p9, log_text, re.MULTILINE))

            # 1.10: 'Thread' szót az üzenet részben (tag: message) tartalmazó sorok száma
            # Minta: kettőspont (:) utáni részben szerepel a 'Thread' szó.
            p10 = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+[A-Z]\s+.*?:.*Thread.*'
            c10 = len(re.findall(p10, log_text, re.MULTILINE))

            counts = [c1, c2, c3, c4, c5, c6, c7, c8, c9, c10]
            output_content = '\n'.join(str(c) for c in counts)

        # ======================================================================
        # 2. ALFELADAT (--rgx 2): Hiba stack trace forrásfájlok kinyerése
        # ======================================================================
        # Kizárólag az Error (E) szintű sorokból kinyerjük a zárójelben található
        # Java forrásállomány nevét (pl. HashMap.java) az előfordulási sorrend megtartásával.
        # Illesztési minta magyarázata:
        #   - ^\d{2}-\d{2}...: sor eleji időbélyeg és PID/TID
        #   - \s+E\s+: pontosan 'E' (Error) szintű sor
        #   - .*?: nem-mohó (lazy) ugrás a stack trace sorig
        #   - \((\w+\.java):\d+\): zárójelben lévő fájlnév elfogása a (\w+\.java) csoporttal
        elif task_id == 2:
            pattern = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+E\s+.*?\((\w+\.java):\d+\)'
            java_files = re.findall(pattern, log_text, re.MULTILINE)
            output_content = '\n'.join(java_files)

        # ======================================================================
        # 3. ALFELADAT (--rgx 3): Különböző PID-k kinyerése előfordulási sorrendben
        # ======================================================================
        # Az összes logsorból regex csoporttal (\d+) kinyerjük a folyamatazonosítót (PID).
        # A PID az időbélyegző utáni legelső numerikus mező.
        # Az egyedi elemek előfordulási sorrendjének megtartásához dict.fromkeys()-t használunk,
        # ami Pythonban garantáltan megőrzi a beillesztési sorrendet halmazműveletek nélkül.
        elif task_id == 3:
            pattern = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+(\d+)\s+'
            all_pids = re.findall(pattern, log_text, re.MULTILINE)
            unique_pids = list(dict.fromkeys(all_pids).keys())
            output_content = '\n'.join(unique_pids)

        # ======================================================================
        # 4. ALFELADAT (--rgx 4): A legtöbb hibát (E) produkáló folyamat (PID)
        # ======================================================================
        # Kinyerjük az összes olyan PID-t, amelynél a log szint 'E' (Error).
        # A Counter segítségével meghatározzuk a leggyakrabban előforduló PID-t és a hibaszámot.
        # Formátum: PID=xx (xx errors)
        elif task_id == 4:
            pattern = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+(\d+)\s+\d+\s+E\s+'
            error_pids = re.findall(pattern, log_text, re.MULTILINE)
            top_pid, top_count = Counter(error_pids).most_common(1)[0]
            output_content = f"PID={top_pid} ({top_count} errors)"

        # ======================================================================
        # 5. ALFELADAT (--rgx 5): Fő szálon történt hibák (E) száma (PID == TID)
        # ======================================================================
        # A feladat feltétele, hogy a folyamatazonosító (PID) és a szálazonosító (TID) megegyezzen.
        # Ezt a reguláris kifejezések visszahivatkozásával (\1 backreference) oldjuk meg:
        #   - (\d+): az 1. csoportban elmentjük a PID-t
        #   - \s+\1\s+: a TID helyén pontosan ugyanannak a számnak kell szerepelnie!
        #   - \s+E\s+: a naplózási szint kizárólag Error ('E') lehet
        elif task_id == 5:
            pattern = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+(\d+)\s+\1\s+E\s+'
            main_thread_errors = re.findall(pattern, log_text, re.MULTILINE)
            output_content = str(len(main_thread_errors))

        else:
            raise ValueError(f"Érvénytelen alfeladat azonosító (--rgx {task_id}). 1 és 5 közötti érték szükséges.")

        # Eredmény kiírása a megadott kimeneti fájlba 'utf-8' kódolással
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)


# ==============================================================================
# 5. KÖZVETLEN HELYI TESZTELÉS / FUTTATÁS BLOKK
# ==============================================================================
if __name__ == '__main__':
    from run_all import run_all_problems
    run_all_problems()
