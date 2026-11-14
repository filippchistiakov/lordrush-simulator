from benchmark.main import execute_bear_benchmark

CONFIG = {
    "ATTACKER_NAME": "ShibaTechOnly",
    "ATT_TROOP_TIER": "t8",
    "ATT_TOTAL_TROOPS": 100000,
    "SIMULATIONS_PER_RATIO": 1000,

    # Можно указать одно число (10) или диапазон ((8, 10))
    "ATT_STEP": 1,
    "ATT_INF": (8, 10),
    "ATT_LAN": (8, 25),
    "ATT_MARK": (70, 100),

    "BEAR_TROOPS": {"infantry_t8": 50000, "lancer_t8": 0, "marksman_t8": 0},
    "BEAR_CSV_FILE": "bear_hunt_results.csv",
}

if __name__ == "__main__":
    execute_bear_benchmark(CONFIG)
