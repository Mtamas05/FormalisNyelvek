"""
Mind a négy feladat egymás utáni szekvenciális futtatása:
  1. Feladat: DFA szóellenőrzés (--check)
  2. Feladat: NFA determinizálás részhalmazos konstrukcióval (--det)
  3. Feladat: DFA minimalizálás partíció-finomítással (--mini)
  4. Feladat: Reguláris kifejezések Android logfájlokon (--rgx 1..5)
"""

import os
import subprocess
import sys
from pathlib import Path


def run_all_problems():
    starter_dir = Path(__file__).resolve().parent
    os.chdir(starter_dir)
    python_exe = sys.executable

    print("=" * 60)
    print("1. FELADAT: Determinisztikus véges automata szimuláció (DFA Check)")
    print("=" * 60)
    input_file_1 = "bemenet.txt"
    output_file_1 = "kimenet_dfa_check.txt"
    words = "10101,111,001"

    print(f"Bemeneti fájl: {input_file_1}")
    print(f"Ellenőrzendő szavak: {words}")
    print("-" * 60)

    cmd1 = [
        python_exe,
        "-m",
        "project",
        "--input",
        input_file_1,
        "--output",
        output_file_1,
        "--check",
        words,
    ]
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    if res1.returncode != 0:
        print(f"Hiba az 1. feladat futásakor:\n{res1.stderr}")
    else:
        if os.path.exists(output_file_1):
            with open(output_file_1, "r", encoding="utf-8") as f:
                print("Eredmény (szavak elfogadása):")
                print(f.read().strip())

    print("\n" + "=" * 60)
    print("2. FELADAT: Automata determinizálása (Subset Construction / DFA Det)")
    print("=" * 60)
    input_file_2 = "bemenet_nfa.txt" if os.path.exists("bemenet_nfa.txt") else "bemenet.txt"
    output_file_2 = "kimenet_dfa_det.txt"

    print(f"Bemeneti fájl: {input_file_2}")
    print("-" * 60)

    cmd2 = [
        python_exe,
        "-m",
        "project",
        "--input",
        input_file_2,
        "--output",
        output_file_2,
        "--det",
    ]
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    if res2.returncode != 0:
        print(f"Hiba a 2. feladat futásakor:\n{res2.stderr}")
    else:
        if os.path.exists(output_file_2):
            with open(output_file_2, "r", encoding="utf-8") as f:
                print("Eredmény (determinizált DFA leírása):")
                print(f.read().strip())

    print("\n" + "=" * 60)
    print("3. FELADAT: Determinisztikus automata minimalizálása (DFA Mini)")
    print("=" * 60)
    input_file_3 = "bemenet_mini.txt" if os.path.exists("bemenet_mini.txt") else "bemenet.txt"
    output_file_3 = "kimenet_dfa_mini.txt"

    print(f"Bemeneti fájl: {input_file_3}")
    print("-" * 60)

    cmd3 = [
        python_exe,
        "-m",
        "project",
        "--input",
        input_file_3,
        "--output",
        output_file_3,
        "--mini",
    ]
    res3 = subprocess.run(cmd3, capture_output=True, text=True)
    if res3.returncode != 0:
        print(f"Hiba a 3. feladat futásakor:\n{res3.stderr}")
    else:
        if os.path.exists(output_file_3):
            with open(output_file_3, "r", encoding="utf-8") as f:
                print("Eredmény (minimalizált DFA leírása):")
                print(f.read().strip())

    print("\n" + "=" * 60)
    print("4. FELADAT: Reguláris kifejezések Android logfájlon (Regex)")
    print("=" * 60)
    input_file_4 = "bemenet_log.txt" if os.path.exists("bemenet_log.txt") else "bemenet.txt"
    print(f"Bemeneti fájl: {input_file_4}")
    print("-" * 60)

    for task_id in range(1, 6):
        output_file_4 = f"kimenet_rgx_{task_id}.txt"
        cmd4 = [
            python_exe,
            "-m",
            "project",
            "--input",
            input_file_4,
            "--output",
            output_file_4,
            "--rgx",
            str(task_id),
        ]
        res4 = subprocess.run(cmd4, capture_output=True, text=True)
        if res4.returncode != 0:
            print(f"Hiba a 4. feladat (--rgx {task_id}) futásakor:\n{res4.stderr}")
        else:
            if os.path.exists(output_file_4):
                with open(output_file_4, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    lines = content.splitlines()
                    preview = '\n'.join(lines[:3]) + (f"\n... (+{len(lines)-3} sor)" if len(lines) > 3 else "")
                    print(f"--rgx {task_id} eredmény:\n{preview}\n")

    print("=" * 60)
    print("Mind a négy feladat sikeresen lefutott!")


# Visszafelé kompatibilitás korábbi hívásokhoz
def run_both_problems():
    run_all_problems()


if __name__ == '__main__':
    run_all_problems()
