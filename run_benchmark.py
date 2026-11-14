from benchmark.main import execute_benchmark

CONFIG = {
    "ATTACKER_NAME": "ShibaTechOnly",
    "DEFENDER_NAME": "ShibaNexus210",
    "ATT_TROOP_TIER": "t10",
    "ATT_TOTAL_TROOPS": 153020,
    "DEF_TROOP_TIER": "t10",
    "DEF_TOTAL_TROOPS": 150000,
    "SIMULATIONS_PER_PAIR": 100,

    # Точные пропорции со скриншота (76510 / 30604 / 45906 = 50 / 20 / 30)
    "ATT_STEP": 1,
    "ATT_INF": (40,60),
    "ATT_LAN": (0,40),
    "ATT_MARK": (20, 70),

    # Точные пропорции врага со скриншота (60000 / 45000 / 45000 = 40 / 30 / 30)
    "DEF_STEP": 1,
    "DEF_INF": 40,
    "DEF_LAN": 30,
    "DEF_MARK": 30,

    "SUMMARY_CSV_FILE": "benchmark_summary.csv",
    "DETAILED_CSV_FILE": "benchmark_detailed.csv",
}

if __name__ == "__main__":
    execute_benchmark(CONFIG)
