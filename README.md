# Lordrush Battle Simulator & Benchmark

A multi-core battle simulator and troop-ratio optimizer adapted for **Lordrush**, based on [ryo-HIT-1589/wos-simulator](https://github.com).

## What's Changed

* **Lordrush Hero Naming & Skills:** Hero rosters, skill mechanics, and CSV skill tables (`skills/Fitz_hero_skills.csv` & `fighters_data/fighters_heroes.json`) are mapped to **Lordrush** characters (e.g., *Sebastian, Hera, Valky, Mortis, Isabelle, Jack, Porter, Rita, Bane, Hyeri, Miko, Cyprus*).
* **Single-File Config Benchmark (`run_benchmark.py` & `run_bear_benchmark.py`):** Instead of editing multiple JSON files before every test, all fighter stats, troop tiers, march sizes, hero skill levels, and ratio ranges are configured directly inside the `CONFIG` dictionary in the runner scripts.
* **Parallel Execution & CSV Export:** Uses all available CPU cores (`ProcessPoolExecutor`) to simulate hundreds of troop ratios across thousands of iterations and exports summary and detailed breakdowns to CSV (`benchmark_summary.csv`, `benchmark_detailed.csv`, `bear_hunt_results.csv`).
* **Auto-Generated Narrow Configs:** At the end of a PvP benchmark run, the script automatically prints ready-to-paste `CONFIG` ratio bounds for the **TOP-20** setups and all setups with a **50%+ Win Rate** so you can quickly run a second pass with `STEP: 1`.

---

## Project Structure

* `run_benchmark.py` — Main entry point and `CONFIG` for **PvP / Garrison** simulations.
* `run_bear_benchmark.py` — Entry point and `CONFIG` for **Bear Hunt** damage optimization.
* `benchmark/main.py` — Core parallel simulation engine, ratio generator, and stats builder.
* `benchmark/export_to_csv.py` — CSV report formatting and export logic.
* `Base_classes/` — Underlying combat math, round resolution, and hero skill execution engine.
* `skills/` & `assets/` — Hero skill definitions and compiled skill dictionaries.

---

## How to Run

### 1. Install Dependencies
Make sure Python 3.10+ is installed, then install the required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Configure Your Battle (`run_benchmark.py`)
Open `run_benchmark.py` and edit the `CONFIG` dictionary:

* **`STATS`:** Enter the 4 percentage values from your battle report (*Bonus Details*) in order: `[Attack, Defense, Lethality, Health]`.
* **`HEROES`:** List your active heroes and their expedition skill levels (top-to-bottom from the right column in-game; use `0` for non-combat skills):
  ```python
  "HEROES": {
      "Isabelle": (4, 4, 4),
      "Bane": (3, 2),
      "Porter": (1, 0, 1),
  }
  ```
* **`INF`, `LAN`, `MARK`:** Pass either a fixed integer (e.g., `40`) or a `(min, max)` range tuple (e.g., `(45, 55)`). The benchmark automatically tests all combinations summing to `100%` using the defined `STEP`.

### 3. Execute Benchmark
Run the PvP optimizer:
```bash
python run_benchmark.py
```

Or run the Bear Hunt damage optimizer:
```bash
python run_bear_benchmark.py
```

---

## Example Output

```text
================================================================================
ATTACKER : ShibaTechOnly (153,020 t10) | Range: (40, 65)/(5, 25)/(20, 45) (step 1)
           Heroes: [None] | Stats: INF: [43.4, 43.4, 12.0, 12.0] | LAN: [43.4, 43.4, 12.0, 12.0] | MAR: [43.4, 43.4, 12.0, 12.0]
DEFENDER : MolterFort (150,000 t10) | Range: 40/30/30 (step 1)
           Heroes: [None] | Stats: INF: [51, 51, 9.0, 9.0] | LAN: [51, 51, 9.0, 9.0] | MAR: [51, 51, 9.0, 9.0]
SETTINGS : 100 sims/pair | Output: benchmark_summary.csv
================================================================================
Simulating PvP: 100%|██████████| 43600/43600 [00:40<00:00, 1075.02battle/s, Ratios: 436/436]

Rank   | Ratio          | Win Rate  | W/L/D
---------------------------------------------
1      | 51/12/37       |   82.00% | 82/18/0
2      | 52/10/38       |   79.00% | 79/21/0
3      | 53/11/36       |   79.00% | 79/21/0
4      | 54/12/34       |   79.00% | 79/21/0
5      | 54/14/32       |   79.00% | 79/21/0
6      | 50/12/38       |   78.00% | 78/22/0
7      | 53/12/35       |   77.00% | 77/23/0
8      | 53/15/32       |   77.00% | 77/23/0
9      | 54/15/31       |   77.00% | 77/23/0
10     | 49/17/34       |   76.00% | 76/24/0
11     | 53/9/38        |   76.00% | 76/24/0
12     | 54/13/33       |   76.00% | 76/24/0
13     | 56/9/35        |   76.00% | 76/24/0
14     | 56/13/31       |   76.00% | 76/24/0
15     | 53/8/39        |   75.00% | 75/25/0
16     | 53/16/31       |   75.00% | 75/24/1
17     | 54/17/29       |   75.00% | 75/25/0
18     | 56/11/33       |   75.00% | 75/25/0
19     | 57/10/33       |   75.00% | 75/25/0
20     | 47/18/35       |   74.00% | 74/26/0

--- TOP-20 CONFIG (Total: 20) ---
        "STEP": 1,
        "INF": (47, 57),
        "LAN": (8, 18),
        "ARC": (29, 39),

--- WR 50%+ CONFIG (Total: 320) ---
        "STEP": 1,
        "INF": (40, 64),
        "LAN": (5, 25),
        "ARC": (22, 45),
```

---

## Updating Hero Skills (Optional)

If you modify `skills/Fitz_hero_skills.csv` to add new Lordrush heroes or adjust skill multipliers, recompile the internal dictionaries before running a simulation:
```bash
python skills/export_hero_skills_dicts.py
```

---

## Credits

* Original combat engine by **HIT-Ryo** ([ryo-HIT-1589/wos-simulator](https://github.com)).
* Skill spreadsheet structure based on **Fitz's Hero Skill Spreadsheet** and community testing from WOS Nerds & HIT Alliance.
