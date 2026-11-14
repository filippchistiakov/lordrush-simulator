from benchmark.main import execute_benchmark

CONFIG = {
    "SIMULATIONS_PER_PAIR": 100,
    "TOP_N_PRINT": None,  # Сколько строк вывести в консоль (уберите или поставьте None для вывода всех)

    "ATTACKER": {
        "NAME": "ShibaTechOnly",
        "TIER": "t10",
        "TROOPS": 153020,
        "STATS": {
            "infantry": [43.4, 43.4, 12.0, 12.0],
            "lancers":  [43.4, 43.4, 12.0, 12.0],
            "marksman": [43.4, 43.4, 12.0, 12.0],
        },
        ## "HEROES": {
        ##     "Isabelle": (4, 4, 4),
        ##     "Bane": (3, 2),
        ##     "Porter": (1, 0, 1),
        ## },
        "STEP": 5,
        "INF": (0, 70),  # На скриншоте использовано 53
        "LAN": (0, 70),   # На скриншоте использовано 12
        "MARK": (0, 80), # На скриншоте использовано 35
    },

    "DEFENDER": {
        "NAME": "MolterFort",
        "TIER": "t10",
        "TROOPS": 150000,
        "STATS": {
            "infantry": [48.0, 48.0, 9.0, 9.0],
            "lancers":  [48.0, 48.0, 9.0, 9.0],
            "marksman": [48.0, 48.0, 9.0, 9.0],
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
