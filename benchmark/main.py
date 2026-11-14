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
_ATT_BYTES = _DEF_BYTES = None


def _init_worker(att_bytes: bytes, def_bytes: bytes):
    global _ATT_BYTES, _DEF_BYTES
    BattleRound.DEBUG = False
    _ATT_BYTES, _DEF_BYTES = att_bytes, def_bytes


def _build_fighter(side: dict | str) -> Fighter:
    if isinstance(side, str):
        return Fighter(side)
    name = side.get("NAME", "CustomFighter")
    if "STATS" in side:
        JsonUtil.fighter_stats[name] = {
            ("marksman" if k.lower() in ("marksmen", "arc", "archer", "archers") else k): v
            for k, v in side["STATS"].items()
        }
    heroes = {
        h: {"stats": {"attack": 0.0, "defense": 0.0},
            "skill_levels": {f"skill_{i}": l for i, l in enumerate(v, 1) if l > 0}}
        if isinstance(v, (list, tuple)) else v
        for h, v in side.get("HEROES", {}).items()
    }
    setattr(JsonUtil, "fighters_heroes" if hasattr(JsonUtil, "fighters_heroes") else "fighter_heroes",
            {**getattr(JsonUtil, "fighters_heroes", {}), name: heroes})
    return Fighter(name)


def collect_ratios(inf: int | tuple, lan: int | tuple, arc: int | tuple, step: int = 1) -> list[tuple[int, int, int]]:
    to_rng = lambda v: range(v, v + 1) if isinstance(v, int) else range(v[0], v[1] + 1, step)
    return sorted((i, l, a) for i, l, a in product(to_rng(inf), to_rng(lan), to_rng(arc)) if i + l + a == 100)


def build_troops_dict(ratio: tuple[int, int, int], total: int, tier: str) -> dict[str, int]:
    counts = [int(total * (p / 100)) for p in ratio]
    for idx in (2, 1, 0):
        if ratio[idx] > 0:
            counts[idx] += total - sum(counts)
            break
    return {f"infantry_{tier}": counts[0], f"lancer_{tier}": counts[1], f"marksman_{tier}": counts[2]}


def _sim_pvp_batch(att_ratio: tuple, def_ratios: list, cfg: dict) -> tuple[dict, list[dict]]:
    att_c, def_c, sims = cfg["ATTACKER"], cfg["DEFENDER"], cfg["SIMULATIONS_PER_PAIR"]
    att_str, att_troops = "/".join(map(str, att_ratio)), build_troops_dict(att_ratio, att_c["TROOPS"], att_c["TIER"])
    tot_w = tot_l = tot_d = 0
    details = []

    for def_ratio in def_ratios:
        def_str, def_troops = "/".join(map(str, def_ratio)), build_troops_dict(def_ratio, def_c["TROOPS"],
                                                                               def_c["TIER"])
        w = l = d = att_rem = def_rem = rnds = 0
        for _ in range(sims):
            att, dfn = pickle.loads(_ATT_BYTES), pickle.loads(_DEF_BYTES)
            att.troops, dfn.troops = att_troops.copy(), def_troops.copy()
            f = Fight(att, dfn)
            sa, sd = f.battle()
            att_rem, def_rem, rnds = att_rem + sa, def_rem + sd, rnds + f.num_rounds
            w, l, d = w + (sa > sd), l + (sd > sa), d + (sa == sd)
        tot_w, tot_l, tot_d = tot_w + w, tot_l + l, tot_d + d
        details.append(
            {"attacker": att_str, "defender": def_str, "win_rate": (w / sims) * 100, "wins": w, "losses": l, "draws": d,
             "avg_att_rem": att_rem / sims, "avg_def_rem": def_rem / sims, "avg_rounds": rnds / sims})

    tot_b = len(def_ratios) * sims
    return {"ratio": att_str, "win_rate": (tot_w / tot_b) * 100 if tot_b else 0.0, "wins": tot_w, "losses": tot_l,
            "draws": tot_d}, details


def _sim_bear_batch(att_ratio: tuple, cfg: dict) -> dict:
    att_c, sims = cfg["ATTACKER"], cfg["SIMULATIONS_PER_RATIO"]
    att_str, att_troops = "/".join(map(str, att_ratio)), build_troops_dict(att_ratio, att_c["TROOPS"], att_c["TIER"])
    dmg = surv = rnds = 0
    for _ in range(sims):
        att, bear = pickle.loads(_ATT_BYTES), pickle.loads(_DEF_BYTES)
        att.troops, bear.troops = att_troops.copy(), cfg["BEAR_TROOPS"].copy()
        f = Fight(att, bear, dont_save=True, bear_hunt=True)
        sa, _ = f.battle()
        dmg, surv, rnds = dmg + f.bear_damage, surv + sa, rnds + f.num_rounds
    return {"ratio": att_str, "avg_damage": dmg / sims, "avg_survived": surv / sims, "avg_rounds": rnds / sims}


def _run_parallel(fn, tasks: list, step_b: int, att_b: bytes, def_b: bytes, desc: str) -> list:
    results = []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 4, initializer=_init_worker, initargs=(att_b, def_b)) as ex:
        futures = [ex.submit(fn, *args) for args in tasks]
        with tqdm(total=len(tasks) * step_b, desc=desc, unit="battle") as pbar:
            for done, fut in enumerate(as_completed(futures), 1):
                results.append(fut.result())
                pbar.update(step_b)
                pbar.set_postfix_str(f"Ratios: {done}/{len(tasks)}")
    return results


def _normalize_csv_cfg(cfg: dict) -> dict:
    att, dfn = cfg["ATTACKER"], cfg.get("DEFENDER", {})
    return {**cfg, "ATTACKER_NAME": att.get("NAME", "Attacker"), "ATT_TROOP_TIER": att["TIER"],
            "ATT_TOTAL_TROOPS": att["TROOPS"],
            "DEFENDER_NAME": dfn.get("NAME", "Defender"), "DEF_TROOP_TIER": dfn.get("TIER", ""),
            "DEF_TOTAL_TROOPS": dfn.get("TROOPS", 0)}


def _print_header(cfg: dict, is_bear: bool = False) -> None:
    print("\n" + "=" * 80)
    for role, key in (("ATTACKER", "ATTACKER"), ("DEFENDER", "DEFENDER")):
        if key not in cfg:
            continue
        s = cfg[key]
        heroes = ", ".join(f"{h}{tuple(v)}" for h, v in s.get("HEROES", {}).items()) or "None"
        stats = " | ".join(f"{k[:3].upper()}: {v}" for k, v in s.get("STATS", {}).items()) or "From JSON"
        print(
            f"{role:<9}: {s.get('NAME', 'Unknown')} ({s['TROOPS']:,} {s['TIER']}) | Range: {s['INF']}/{s['LAN']}/{s['ARC']} (step {s.get('STEP', 1)})\n           Heroes: [{heroes}] | Stats: {stats}")
    print(
        f"TARGET   : Bear Hunt ({cfg['BEAR_TROOPS']}) | Runs/ratio: {cfg['SIMULATIONS_PER_RATIO']}" if is_bear else f"SETTINGS : {cfg['SIMULATIONS_PER_PAIR']} sims/pair | Output: {cfg['SUMMARY_CSV_FILE']}")
    print("=" * 80)


def _print_bounds(label: str, items: list[dict]) -> None:
    if not items:
        return print(f"\n--- {label}: No matching combinations found ---")
    infs, lans, arcs = zip(*(map(int, x["ratio"].split("/")) for x in items))
    print(
        f"\n--- {label} (Total: {len(items)}) ---\n        \"STEP\": 1,\n        \"INF\": ({min(infs)}, {max(infs)}),\n        \"LAN\": ({min(lans)}, {max(lans)}),\n        \"ARC\": ({min(arcs)}, {max(arcs)}),")


def execute_benchmark(cfg: dict) -> None:
    JsonUtil.load_fighters_data("fighters_data/fighters_stats.json", "fighters_data/fighters_heroes.json")
    att_c, def_c = cfg["ATTACKER"], cfg["DEFENDER"]
    att_r = collect_ratios(att_c["INF"], att_c["LAN"], att_c["ARC"], att_c.get("STEP", 1))
    def_r = collect_ratios(def_c["INF"], def_c["LAN"], def_c["ARC"], def_c.get("STEP", 1))
    if not att_r or not def_r:
        return print("Error: No ratio combinations sum up to 100%.")

    _print_header(cfg)
    raw = _run_parallel(_sim_pvp_batch, [(r, def_r, cfg) for r in att_r], len(def_r) * cfg["SIMULATIONS_PER_PAIR"],
                        pickle.dumps(_build_fighter(att_c)), pickle.dumps(_build_fighter(def_c)), "Simulating PvP")
    summary = sorted([x[0] for x in raw], key=lambda x: x["win_rate"], reverse=True)
    save_to_csv(_normalize_csv_cfg(cfg), summary,
                sorted([i for x in raw for i in x[1]], key=lambda x: (x["attacker"], x["defender"])))

    print(f"\n{'Rank':<6} | {'Ratio':<14} | {'Win Rate':<9} | {'W/L/D'}\n" + "-" * 45)
    for i, r in enumerate(summary[:cfg.get("TOP_N_PRINT", len(summary))], 1):
        print(f"{i:<6} | {r['ratio']:<14} | {r['win_rate']:>7.2f}% | {r['wins']}/{r['losses']}/{r['draws']}")
    _print_bounds("TOP-20 CONFIG", summary[:20])
    _print_bounds("WR 50%+ CONFIG", [r for r in summary if r["win_rate"] >= 50.0])


def execute_bear_benchmark(cfg: dict) -> None:
    JsonUtil.load_fighters_data("fighters_data/fighters_stats.json", "fighters_data/fighters_heroes.json")
    att_c = cfg["ATTACKER"]
    att_r = collect_ratios(att_c["INF"], att_c["LAN"], att_c["ARC"], att_c.get("STEP", 1))
    if not att_r:
        return print("Error: No ratio combinations sum up to 100%.")

    _print_header(cfg, is_bear=True)
    bear = Fighter("Bear")
    bear.heroes = []
    for grp in vars(bear.stats).values():
        if hasattr(grp, "__dict__"):
            for k in vars(grp):
                setattr(grp, k, 0)

    results = sorted(_run_parallel(_sim_bear_batch, [(r, cfg) for r in att_r], cfg["SIMULATIONS_PER_RATIO"],
                                   pickle.dumps(_build_fighter(att_c)), pickle.dumps(bear), "Simulating Bear"),
                     key=lambda x: x["avg_damage"], reverse=True)
    save_bear_csv(_normalize_csv_cfg(cfg), results)

    print(f"\n{'Rank':<6} | {'Ratio':<14} | {'Avg Damage':<14} | {'Survived'}\n" + "-" * 52)
    for i, r in enumerate(results[:cfg.get("TOP_N_PRINT", len(results))], 1):
        print(f"{i:<6} | {r['ratio']:<14} | {r['avg_damage']:>14.1f} | {r['avg_survived']:>8.1f}")


def execute_bear_benchmark(cfg: dict) -> None:
    JsonUtil.load_fighters_data("fighters_data/fighters_stats.json", "fighters_data/fighters_heroes.json")
    att_c = cfg["ATTACKER"]
    att_r = collect_ratios(att_c["INF"], att_c["LAN"], att_c["ARC"], att_c.get("STEP", 1))
    if not att_r:
        return print("Error: No ratio combinations sum up to 100%.")

    _print_header(cfg, is_bear=True)
    bear = Fighter("Bear")
    bear.heroes = []
    for grp in vars(bear.stats).values():
        if hasattr(grp, "__dict__"):
            for k in vars(grp):
                setattr(grp, k, 0)

    results = sorted(_run_parallel(_sim_bear_batch, [(r, cfg) for r in att_r], cfg["SIMULATIONS_PER_RATIO"],
                                   pickle.dumps(_build_fighter(att_c)), pickle.dumps(bear), "Simulating Bear"),
                     key=lambda x: x["avg_damage"], reverse=True)
    save_bear_csv(_normalize_csv_cfg(cfg), results)

    _print_header(cfg, is_bear=True)
    print(f"{'Rank':<6} | {'Ratio':<14} | {'Avg Damage':<14} | {'Survived'}\n" + "-" * 52)
    for i, r in enumerate(results[:cfg.get("TOP_N_PRINT", len(results))], 1):
        print(f"{i:<6} | {r['ratio']:<14} | {r['avg_damage']:>14.1f} | {r['avg_survived']:>8.1f}")
