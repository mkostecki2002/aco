from typing import List
import aco
from aco import Ant
import time
import matplotlib.pyplot as plt
import statistics
import os

def run_experiment(distances, coords, params):
    """
    Uruchamia algorytm ACO dla zadanych parametrów.
    Zwraca: najlepszy_dystans, najlepsza_trasa, historia_zbieżności (lista najlepszych wyników w iteracjach)
    """
    n = len(coords)
    pheromones = aco.create_matrix_of_pheromones(n)
    
    best_global_dist = float('inf')
    best_global_path = []
    convergence_history = []

    start_time = time.time()

    for _ in range(params['T']):
        ants_colony : List[Ant] = aco.create_ants_population(params['m'], n) 
        
        # Budowanie trasy
        for _ in range(n - 1):
            for ant in ants_colony:
                ant.visit_next_location(distances, pheromones, params['alpha'], params['beta'], params['p_random'])
        
        for ant in ants_colony:
            total_dist = ant.get_total_distance(distances)
            
            if total_dist < best_global_dist:
                best_global_dist = total_dist
                best_global_path = ant.seen_locations[:] # kopia, a nie referencja do pola obiektu

        # Aktualizacja feromonów
        aco.update_pheromones(pheromones, distances, ants_colony, params['rho'])
        
        convergence_history.append(best_global_dist)

    duration = time.time() - start_time
    return best_global_dist, best_global_path, convergence_history, duration

def plot_route(coords, path, title, filename):
    x = [coords[i][0] for i in path]
    y = [coords[i][1] for i in path]
    # Domknięcie pętli
    x.append(coords[path[0]][0])
    y.append(coords[path[0]][1])

    plt.figure(figsize=(8, 6))
    plt.plot(x, y, 'o-', mfc='r')
    for i, (cx, cy) in enumerate(coords):
        plt.text(cx, cy, str(i), fontsize=9)
    plt.title(title)
    plt.grid(True)
    plt.savefig(filename)
    plt.close()

def main():
    # WYBÓR PLIKU DANYCH
    print("Wybierz plik z danymi do ACO:")
    print("1. A-n32-k5.txt (domyślny)")
    print("2. A-n80-k10.txt")
    file_choice = input("Wybór: ")

    filename = "A-n32-k5.txt"
    if file_choice == '2':
        filename = 'A-n80-k10.txt'

    if not os.path.exists(filename):
        print(f"Błąd: Plik {filename} nie istnieje w folderze roboczym.")
        return

    distances, coords = aco.create_matrix_of_distances(filename)
    print(f"Wczytano {len(coords)} miast z pliku {filename}")

    # Parametry bazowe (domyślne)
    base_params = {
        'm': 20,           # Liczba mrówek
        'p_random': 0.01,  # Szansa na losowy ruch
        'alpha': 1.0,      # Waga feromonu
        'beta': 2.0,       # Waga odległości
        'T': 50,           # Liczba iteracji
        'rho': 0.3         # Parowanie
    }

    # PLAN EKSPERYMENTÓW (zgodny z zadaniem)
    experiments_plan = {
        "m": [10, 20, 50, 100],
        "p_random": [0.0, 0.01, 0.05, 0.1],
        "alpha": [0.5, 1.0, 2.0, 5.0],
        "beta": [1.0, 2.0, 5.0, 10.0],
        "T": [10, 50, 100], # 500 może trwać długo, można dodać
        "rho": [0.1, 0.3, 0.5, 0.8]
    }
    
    stats_results = {} # Do przechowywania wyników do wykresów

    print("Rozpoczynam serię eksperymentów...")
    best_path_in_experiment = None
    min_dist_in_experiment = float('inf')
    print("--- Parametry bazowe ---\nm: 20\np_random: 0.01\nalpha: 1.0\nbeta: 2.0\nT: 50\nrho: 0.3")

    for param_name, values in experiments_plan.items():
        print(f"\n--- Badanie parametru: {param_name} ---")
        param_means = []
        param_stds = []
        
        for val in values:
            current_params = base_params.copy()
            current_params[param_name] = val
            
            results = []
            times = []
            best_path_in_series = None
            min_dist_in_series = float('inf')

            # 5 powtórzeń dla każdej konfiguracji
            for run_idx in range(5):
                dist, path, history, duration = run_experiment(distances, coords, current_params)
                results.append(dist)
                times.append(duration)

                print(f"    Run {run_idx + 1}/5: dist={dist:.2f}, time={duration:.4f}s")

                if dist < min_dist_in_series:
                    min_dist_in_series = dist
                    best_path_in_series = path
            
            mean_res = statistics.mean(results)
            median_res = statistics.median(results)
            std_res = statistics.stdev(results) if len(results) > 1 else 0.0
            param_means.append(mean_res)
            param_stds.append(std_res)
            if min_dist_in_series < min_dist_in_experiment:
                best_path_in_experiment = best_path_in_series
                min_dist_in_experiment = min_dist_in_series

            print(f"  Wartość {val}: Średnia={mean_res:.2f}, Median={median_res:.2f}"
                  f", Min={min(results):.2f}, Max={max(results):.2f},"
                  f" Std={std_res:.2f}")


        stats_results[param_name] = (values, param_means, param_stds)

    # GENEROWANIE RAPORTU GRAFICZNEGO
    print("\nGenerowanie wykresów...")
    
    # Wykresy wrażliwości parametrów
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'Analiza parametrów ACO dla pliku {filename}', fontsize=16)
    axs = axs.ravel()
    
    for i, (param, (x, y, err)) in enumerate(stats_results.items()):
        axs[i].errorbar(x, y, yerr=err, fmt='-o', capsize=5, ecolor='red')
        axs[i].set_title(f'Wpływ {param}')
        axs[i].set_xlabel('Wartość')
        axs[i].set_ylabel('Średni dystans trasy')
        axs[i].grid(True)
    
    plt.tight_layout()
    plt.savefig('wyniki_analiza_parametrow.png')
    print("Zapisano: wyniki_analiza_parametrow.png")

    # Mapa najlepszej trasy spośród wszystkich eksperymentów
    print("Generowanie mapy najlepszej trasy dla wszystkich eksperymentów...")
    plot_route(coords, best_path_in_experiment, f'Najlepsza trasa (dystans: {min_dist_in_experiment:.2f})', 'mapa_trasy.png')
    print("Zapisano: mapa_trasy.png")

    plt.show()

if __name__ == "__main__":
    main()