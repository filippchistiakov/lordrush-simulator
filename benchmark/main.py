import os
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
from tqdm import tqdm

from Base_classes.Fighter import Fighter
from Base_classes.Fight import Fight
from Base_classes.BattleRound import BattleRound
from Base_classes.JsonUtil import JsonUtil
from benchmark.export_to_csv import save_to_csv, save_bear_csv

BattleRound.DEBUG = False
_ATT_BYTES = None
_DEF_BYTES = None


def _init_worker(att_bytes: bytes, def_bytes: bytes):
    global _ATT_BYTES, _DEF_BYTES
    BattleRound.DEBUG = False
    _ATT_BYTES, _DEF_BYTES = att_bytes, def_bytes


def _build_fighter(side_cfg: dict | str) -> Fighter:
    """Создает Fighter либо из словаря статов в CONFIG, либо по имени из JSON."""
    if isinstance(side_cfg, str):
        return Fighter(side_cfg)

    name = side_cfg.get("NAME", "CustomFighter")
    stats_dict = side_cfg.get("STATS")
    heroes_dict = side_cfg.get("HEROES", {})

    if stats_dict:
        # Подстраховка: если написали "marksmen", автоматически меняем на "marksman"
        fixed_stats = {("marksman" if k.lower() == "marksmen" else k): v for k, v in stats_dict.items()}
        JsonUtil.fighter_stats[name] = fixed_stats

    if hasattr(JsonUtil, "fighters_heroes"):
        JsonUtil.fighters_heroes[name] = heroes_dict
    elif hasattr(JsonUtil, "fighter_heroes"):
        JsonUtil.fighter_heroes[name] = heroes_dict

    return Fighter(name)


def _to_range(val: int | tuple[int, int], step: int) -> range:
    if isinstance(val, int):
        return range(val, val + 1)
    return range(val[0], val[1] + 1, step)


def collect_ratios(inf: int | tuple, lan: int | tuple, mark: int | tuple, step: int = 1) -> list[tuple[int, int, int]]:
    return sorted(
        (i, l, m)
        for i, l, m in product(_to_range(inf, step), _to_range(lan, step), _to_range(mark, step))
        if i + l + m == 100
    )


def build_troops_dict(ratio: tuple[int, int, int], total: int, tier: str) -> dict[str, int]:
    counts = [int(total * (p / 100)) for p in ratio]
    rem = total - sum(counts)
    for idx in (2, 1, 0):
        if ratio[idx] > 0:
            counts[idx] += rem
            break
    return {f"infantry_{tier}": counts[0], f"lancer_{tier}": counts[1], f"marksman_{tier}": counts[2]}


def _sim_pvp_batch(att_ratio: tuple, def_ratios: list, cfg: dict) -> tuple[dict, list[dict]]:
    att_cfg, def_cfg = cfg["ATTACKER"], cfg["DEFENDER"]
    att_str = "/".join(map(str, att_ratio))
    att_troops = build_troops_dict(att_ratio, att_cfg["TROOPS"], att_cfg["TIER"])
    sims = cfg["SIMULATIONS_PER_PAIR"]
    tot_w = tot_l = tot_d = 0
    details = []

    for def_ratio in def_ratios:
        def_str = "/".join(map(str, def_ratio))
        def_troops = build_troops_dict(def_ratio, def_cfg["TROOPS"], def_cfg["TIER"])
        w = l = d = att_rem = def_rem = rnds = 0

        for _ in range(sims):
            att, dfn = pickle.loads(_ATT_BYTES), pickle.loads(_DEF_BYTES)
            att.troops, dfn.troops = att_troops.copy(), def_troops.copy()
            f = Fight(att, dfn)
            sa, sd = f.battle()
            att_rem += sa
            def_rem += sd
            rnds += f.num_rounds
            if sa > sd:
                w += 1
            elif sd > sa:
                l += 1
            else:
                d += 1

        tot_w, tot_l, tot_d = tot_w + w, tot_l + l, tot_d + d
        details.append({
            "attacker": att_str, "defender": def_str, "win_rate": (w / sims) * 100,
            "wins": w, "losses": l, "draws": d,
            "avg_att_rem": att_rem / sims, "avg_def_rem": def_rem / sims, "avg_rounds": rnds / sims,
        })

    tot_battles = len(def_ratios) * sims
    summary = {
        "ratio": att_str, "win_rate": (tot_w / tot_battles) * 100 if tot_battles else 0.0,
        "wins": tot_w, "losses": tot_l, "draws": tot_d,
    }
    return summary, details


def _sim_bear_batch(att_ratio: tuple, cfg: dict) -> dict:
    att_cfg = cfg["ATTACKER"]
    att_str = "/".join(map(str, att_ratio))
    att_troops = build_troops_dict(att_ratio, att_cfg["TROOPS"], att_cfg["TIER"])
    sims = cfg["SIMULATIONS_PER_RATIO"]
    dmg = surv = rnds = 0

    for _ in range(sims):
        att, bear = pickle.loads(_ATT_BYTES), pickle.loads(_DEF_BYTES)
        att.troops, bear.troops = att_troops.copy(), cfg["BEAR_TROOPS"].copy()
        f = Fight(att, bear, dont_save=True, bear_hunt=True)
        sa, _ = f.battle()
        dmg += f.bear_damage
        surv += sa
        rnds += f.num_rounds

    return {"ratio": att_str, "avg_damage": dmg / sims, "avg_survived": surv / sims, "avg_rounds": rnds / sims}


def _run_parallel(worker_fn, tasks: list, step_battles: int, att_bytes: bytes, def_bytes: bytes, desc: str) -> list:
    workers = os.cpu_count() or 4
    results = []
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(att_bytes, def_bytes)) as ex:
        futures = [ex.submit(worker_fn, *args) for args in tasks]
        with tqdm(total=len(tasks) * step_battles, desc=desc, unit="battle") as pbar:
            for done, fut in enumerate(as_completed(futures), 1):
                results.append(fut.result())
                pbar.update(step_battles)
                pbar.set_postfix_str(f"Ratios: {done}/{len(tasks)}")
    return results


def _normalize_csv_cfg(cfg: dict) -> dict:
    """Адаптирует новый формат CONFIG под ключи export_to_csv.py."""
    att = cfg["ATTACKER"]
    flat = dict(cfg)
    flat["ATTACKER_NAME"] = att.get("NAME", "Attacker")
    flat["ATT_TROOP_TIER"] = att["TIER"]
    flat["ATT_TOTAL_TROOPS"] = att["TROOPS"]
    if "DEFENDER" in cfg:
        dfn = cfg["DEFENDER"]
        flat["DEFENDER_NAME"] = dfn.get("NAME", "Defender")
        flat["DEF_TROOP_TIER"] = dfn["TIER"]
        flat["DEF_TOTAL_TROOPS"] = dfn["TROOPS"]
    return flat


def execute_benchmark(cfg: dict) -> None:
    def _print_ratio_bounds(label: str, items: list[dict]) -> None:
        """Prints min/max troop ratios on English formatted as a ready-to-paste CONFIG snippet."""
        if not items:
            print(f"\n--- {label}: No matching combinations found ---")
            return

        parsed = [tuple(map(int, x["ratio"].split("/"))) for x in items]
        infs, lans, marks = zip(*parsed)

        print(f"\n--- {label} (Total: {len(items)}) ---")
        print('        "STEP": 1,')
        print(f'        "INF": ({min(infs)}, {max(infs)}),')
        print(f'        "LAN": ({min(lans)}, {max(lans)}),')
        print(f'        "MARK": ({min(marks)}, {max(marks)}),')

    JsonUtil.load_fighters_data("fighters_data/fighters_stats.json", "fighters_data/fighters_heroes.json")
    att_cfg, def_cfg = cfg["ATTACKER"], cfg["DEFENDER"]

    att_ratios = collect_ratios(att_cfg["INF"], att_cfg["LAN"], att_cfg["MARK"], att_cfg.get("STEP", 1))
    def_ratios = collect_ratios(def_cfg["INF"], def_cfg["LAN"], def_cfg["MARK"], def_cfg.get("STEP", 1))
    if not att_ratios or not def_ratios:
        return print("Error: Ни одна комбинация не дает 100% в сумме.")

    att_fighter = _build_fighter(att_cfg)
    def_fighter = _build_fighter(def_cfg)

    tasks = [(r, def_ratios, cfg) for r in att_ratios]
    raw = _run_parallel(_sim_pvp_batch, tasks, len(def_ratios) * cfg["SIMULATIONS_PER_PAIR"], pickle.dumps(att_fighter),
                        pickle.dumps(def_fighter), "Simulating PvP")

    summary = sorted([x[0] for x in raw], key=lambda x: x["win_rate"], reverse=True)
    detailed = sorted([item for x in raw for item in x[1]], key=lambda x: (x["attacker"], x["defender"]))
    save_to_csv(_normalize_csv_cfg(cfg), summary, detailed)

    top_n = cfg.get("TOP_N_PRINT", len(summary))
    print(f"\n{'Rank':<6} | {'Ratio':<14} | {'Win Rate':<9} | {'W/L/D'}")
    for i, r in enumerate(summary[:top_n], 1):
        print(f"{i:<6} | {r['ratio']:<14} | {r['win_rate']:>7.2f}% | {r['wins']}/{r['losses']}/{r['draws']}")

    # Вывод диапазонов для Top-20 и WR >= 50%
    _print_ratio_bounds("TOP-20 CONFIG", summary[:20])
    wr_50_plus = [r for r in summary if r["win_rate"] >= 50.0]
    _print_ratio_bounds("WR 50%+ CONFIG", wr_50_plus)



def execute_bear_benchmark(cfg: dict) -> None:
    JsonUtil.load_fighters_data("fighters_data/fighters_stats.json", "fighters_data/fighters_heroes.json")
    att_cfg = cfg["ATTACKER"]
    att_ratios = collect_ratios(att_cfg["INF"], att_cfg["LAN"], att_cfg["MARK"], att_cfg.get("STEP", 1))
    if not att_ratios:
        return print("Error: Ни одна комбинация не дает 100% в сумме.")

    att_fighter = _build_fighter(att_cfg)

    bear = Fighter("Bear")
    bear.heroes = []
    for grp in vars(bear.stats).values():
        if hasattr(grp, "__dict__"):
            for k in vars(grp):
                setattr(grp, k, 0)

    tasks = [(r, cfg) for r in att_ratios]
    results = _run_parallel(_sim_bear_batch, tasks, cfg["SIMULATIONS_PER_RATIO"], pickle.dumps(att_fighter),
                            pickle.dumps(bear), "Simulating Bear")

    results.sort(key=lambda x: x["avg_damage"], reverse=True)
    save_bear_csv(_normalize_csv_cfg(cfg), results)

    top_n = cfg.get("TOP_N_PRINT", len(results))
    print(f"\n{'Rank':<6} | {'Ratio':<14} | {'Avg Damage':<14} | {'Survived'}")
    for i, r in enumerate(results[:top_n], 1):
        print(f"{i:<6} | {r['ratio']:<14} | {r['avg_damage']:>14.1f} | {r['avg_survived']:>8.1f}")
