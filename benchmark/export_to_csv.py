import csv


def save_to_csv(cfg: dict, summary_results: list[dict], detailed_results: list[dict]) -> None:
    with open(cfg["SUMMARY_CSV_FILE"], mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Rank",
            "Attacker Name",
            "Attacker Tier",
            "Attacker Troops",
            "Defender Name",
            "Defender Tier",
            "Defender Troops",
            "Attacker Ratio (Inf/Lan/Arc)",
            "Win Rate (%)",
            "Wins",
            "Losses",
            "Draws",
        ])
        for rank, r in enumerate(summary_results, start=1):
            writer.writerow([
                rank,
                cfg["ATTACKER_NAME"],
                cfg["ATT_TROOP_TIER"],
                cfg["ATT_TOTAL_TROOPS"],
                cfg["DEFENDER_NAME"],
                cfg["DEF_TROOP_TIER"],
                cfg["DEF_TOTAL_TROOPS"],
                r["ratio"],
                f"{r['win_rate']:.2f}",
                r["wins"],
                r["losses"],
                r["draws"],
            ])

    with open(cfg["DETAILED_CSV_FILE"], mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Attacker Name",
            "Attacker Tier",
            "Attacker Troops",
            "Defender Name",
            "Defender Tier",
            "Defender Troops",
            "Attacker (Inf/Lan/Arc)",
            "Defender (Inf/Lan/Arc)",
            "Attacker Win Rate (%)",
            "Wins",
            "Losses",
            "Draws",
            "Avg Attacker Remaining",
            "Avg Defender Remaining",
            "Avg Rounds",
        ])
        for d in detailed_results:
            writer.writerow([
                cfg["ATTACKER_NAME"],
                cfg["ATT_TROOP_TIER"],
                cfg["ATT_TOTAL_TROOPS"],
                cfg["DEFENDER_NAME"],
                cfg["DEF_TROOP_TIER"],
                cfg["DEF_TOTAL_TROOPS"],
                d["attacker"],
                d["defender"],
                f"{d['win_rate']:.2f}",
                d["wins"],
                d["losses"],
                d["draws"],
                f"{d['avg_att_rem']:.1f}",
                f"{d['avg_def_rem']:.1f}",
                f"{d['avg_rounds']:.1f}",
            ])


def save_bear_csv(cfg: dict, results: list[dict]) -> None:
    with open(cfg["BEAR_CSV_FILE"], mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Rank",
            "Attacker Name",
            "Attacker Tier",
            "Attacker Troops",
            "Ratio (Inf/Lan/Arc)",
            "Avg Bear Kills (Damage)",
            "Avg Attacker Survived",
            "Avg Rounds",
        ])
        for rank, r in enumerate(results, start=1):
            writer.writerow([
                rank,
                cfg["ATTACKER_NAME"],
                cfg["ATT_TROOP_TIER"],
                cfg["ATT_TOTAL_TROOPS"],
                r["ratio"],
                f"{r['avg_damage']:.1f}",
                f"{r['avg_survived']:.1f}",
                f"{r['avg_rounds']:.1f}",
            ])
