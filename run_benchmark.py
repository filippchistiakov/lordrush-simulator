from benchmark.main import execute_benchmark

CONFIG = {
    "SIMULATIONS_PER_PAIR": 100,
    "TOP_N_PRINT": 20,  # Сколько строк вывести в консоль (уберите или поставьте None для вывода всех)

    "ATTACKER": {
        "NAME": "ShibaTechOnly",
        "TIER": "t10",
        "TROOPS": 153020,
        "STATS": {
            "infantry": [26.3, 19.5, 20.5, 28.0],
            "lancers":  [22.3, 17.0, 20.5, 19.0],
            "marksman": [43.3, 17.0, 29.5, 19.0],
        },
        "HEROES": {},  # Characters can also be added here, if necessary.
        "STEP": 1,
        "INF": (45, 55),
        "LAN": (5, 20),
        "MARK": (30, 45),
    },

    "DEFENDER": {
        "NAME": "Nexus4-4",
        "TIER": "t10",
        "TROOPS": 150000,
        "STATS": {
            "infantry": [30, 30, 30, 30],
            "lancers":  [30, 30, 30, 30],
            "marksman": [30, 30, 30, 30],
        },
        "HEROES": {},
        "STEP": 1,
        "INF": 40,
        "LAN": 30,
        "MARK": 30,
    },

    "SUMMARY_CSV_FILE": "benchmark_summary.csv",
    "DETAILED_CSV_FILE": "benchmark_detailed.csv",
}

if __name__ == "__main__":
    execute_benchmark(CONFIG)
