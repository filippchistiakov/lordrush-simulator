from benchmark.main import execute_benchmark

CONFIG = {
    "SIMULATIONS_PER_PAIR": 100,
    "TOP_N_PRINT": 20,  # Сколько строк вывести в консоль (уберите или поставьте None для вывода всех)

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
        "STEP": 1,
        "INF": (40, 65),
        "LAN": (5, 25),
        "ARC": (20, 45),
    },

    "DEFENDER": {
        "NAME": "MolterFort",
        "TIER": "t10",
        "TROOPS": 150000,
        "STATS": {
            "infantry": [51, 51, 9.0, 9.0],
            "lancers":  [51, 51, 9.0, 9.0],
            "marksman": [51, 51, 9.0, 9.0],
        },
        "HEROES": {},
        "STEP": 1,
        "INF": 40,
        "LAN": 30,
        "ARC": 30,
    },

    "SUMMARY_CSV_FILE": "benchmark_summary.csv",
    "DETAILED_CSV_FILE": "benchmark_detailed.csv",
}



if __name__ == "__main__":
    execute_benchmark(CONFIG)
