import csv
import os
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
from tqdm import tqdm

from Base_classes.Fighter import Fighter
from Base_classes.Fight import Fight
from Base_classes.BattleRound import BattleRound
from Base_classes.JsonUtil import JsonUtil

BattleRound.DEBUG = False

# General settings
TOTAL_TROOPS = 100000
SIMULATIONS_PER_RATIO = 1000   # More runs per ratio for accurate average damage

# Attacker ranges (focused on damage-dealing ratios for Bear Hunt)
ATT_STEP = 1
ATT_INF_RANGE = (8, 10)
ATT_LAN_RANGE = (8, 25)
ATT_MARK_RANGE = (70, 100)

# Bear target settings (large pool of dummy troops so it survives all rounds)
BEAR_TROOPS = {
    "infantry_t8": 50000,
    "lancer_t8": 0,
    "marksman_t8": 0,
}
BEAR_CSV_FILE = "bear_hunt_results.csv"

_BASE_ATT_BYTES = None
_BASE_BEAR_BYTES = None


def _init_worker(att_bytes: bytes, bear_bytes: bytes):
    global _BASE_ATT_BYTES, _BASE_BEAR_BYTES
    BattleRound.DEBUG = False
    _BASE_ATT_BYTES = att_bytes
    _BASE_BEAR_BYTES = bear_bytes


def generate_ratios(
    step: int,
    inf_range: tuple[int, int],
    lan_range: tuple[int, int],
    mark_range: tuple[int, int],
) -> list[tuple[int, int, int]]:
    ratios = []
    inf_min, inf_max = inf_range
    lan_min, lan_max = lan_range
    mark_min, mark_max = mark_range

    for inf, lan, mark in product(
        range(inf_min, inf_max + 1, step),
        range(lan_min, lan_max + 1, step),
        range(mark_min, mark_max + 1, step),
    ):
        if inf + lan + mark == 100:
            ratios.append((inf, lan, mark))
    return ratios


def build_troops_dict(ratio: tuple[int, int, int], total: int) -> dict[str, int]:
    inf_pct, lan_pct, mark_pct = ratio
    return {
        "infantry_t8": int(total * (inf_pct / 100)),
        "lancer_t8": int(total * (lan_pct / 100)),
        "marksman_t8": int(total * (mark_pct / 100)),
    }


def _simulate_bear_ratio(att_ratio: tuple[int, int, int]) -> dict:
    """Simulates a specific troop ratio against the Bear and measures total damage dealt."""
    att_str = "/".join(map(str, att_ratio))
    att_troops_template = build_troops_dict(att_ratio, TOTAL_TROOPS)
    initial_bear_count = sum(BEAR_TROOPS.values())

    total_damage_dealt = 0
    total_att_survived = 0
    total_rounds = 0

    for _ in range(SIMULATIONS_PER_RATIO):
        attacker = pickle.loads(_BASE_ATT_BYTES)
        attacker.troops = att_troops_template.copy()

        bear = pickle.loads(_BASE_BEAR_BYTES)
        bear.troops = BEAR_TROOPS.copy()

        f = Fight(attacker, bear, dont_save=True, bear_hunt=True)
        sum_att, _ = f.battle()

        total_damage_dealt += f.bear_damage
        total_att_survived += sum_att
        total_rounds += f.num_rounds

    avg_damage = total_damage_dealt / SIMULATIONS_PER_RATIO
    avg_survived = total_att_survived / SIMULATIONS_PER_RATIO
    avg_rounds = total_rounds / SIMULATIONS_PER_RATIO

    return {
        "ratio": att_str,
        "avg_damage": avg_damage,
        "avg_survived": avg_survived,
        "avg_rounds": avg_rounds,
    }


def save_bear_csv(results: list[dict]) -> None:
    with open(BEAR_CSV_FILE, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Rank",
            "Ratio (Inf/Lan/Mark)",
            "Avg Bear Kills (Damage)",
            "Avg Attacker Survived",
            "Avg Rounds",
        ])
        for rank, r in enumerate(results, start=1):
            writer.writerow([
                rank,
                r["ratio"],
                f"{r['avg_damage']:.1f}",
                f"{r['avg_survived']:.1f}",
                f"{r['avg_rounds']:.1f}",
            ])


def run_bear_benchmark():
    JsonUtil.load_fighters_data(
        fighters_stats_path="fighters_data/fighters_stats.json",
        fighters_heroes_path="fighters_data/fighters_heroes.json"
    )

    # Create attacker profile
    base_attacker = Fighter("viper")

    # Create Bear profile without heroes and with zeroed offensive stats so it acts as a punching bag
    base_bear = Fighter("Bear")
    base_bear.heroes = []
    for stat_group in vars(base_bear.stats).values():
        if hasattr(stat_group, "__dict__"):
            for attr in vars(stat_group):
                setattr(stat_group, attr, 0)

    att_bytes = pickle.dumps(base_attacker)
    bear_bytes = pickle.dumps(base_bear)

    att_ratios = generate_ratios(ATT_STEP, ATT_INF_RANGE, ATT_LAN_RANGE, ATT_MARK_RANGE)
    total_ratios = len(att_ratios)
    total_battles = total_ratios * SIMULATIONS_PER_RATIO
    num_workers = os.cpu_count() or 4

    results = []

    print(f"Starting Bear Hunt simulation on {num_workers} CPU cores: {total_ratios} ratios x {SIMULATIONS_PER_RATIO} runs = {total_battles} battles.\n")

    with ProcessPoolExecutor(
        max_workers=num_workers,
        initializer=_init_worker,
        initargs=(att_bytes, bear_bytes)
    ) as executor:
        futures = {
            executor.submit(_simulate_bear_ratio, ratio): ratio
            for ratio in att_ratios
        }

        completed_ratios = 0
        with tqdm(total=total_battles, desc="Simulating Bear Hunt", unit="battle") as pbar:
            for future in as_completed(futures):
                res = future.result()
                results.append(res)
                completed_ratios += 1
                pbar.update(SIMULATIONS_PER_RATIO)
                pbar.set_postfix_str(
                    f"Ratios: {completed_ratios}/{total_ratios} | Last: {res['ratio']} (Dmg: {res['avg_damage']:.0f})"
                )

    # Sort by highest average damage dealt
    results.sort(key=lambda x: x["avg_damage"], reverse=True)
    save_bear_csv(results)

    print("\n" + "=" * 75)
    print(f"{'Rank':<6} | {'Ratio (Inf/Lan/Mark)':<22} | {'Avg Damage (Kills)':<20} | {'Avg Survived'}")
    print("=" * 75)
    for rank, r in enumerate(results, start=1):
        print(f"{rank:<6} | {r['ratio']:<22} | {r['avg_damage']:>18.1f} | {r['avg_survived']:>12.1f}")

    print(f"\nBear Hunt results saved to '{BEAR_CSV_FILE}'.")


if __name__ == "__main__":
    run_bear_benchmark()
