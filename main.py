from typing import List
import aco
from aco import Ant
import time
import matplotlib.pyplot as plt
import statistics
import os
import csv
from datetime import datetime

def run_experiment(distances, coords, params):
    """
    Uruchamia algorytm ACO dla zadanych parametrów.
    Zwraca: najlepszy_dystans, najlepsza_trasa, średnia_najlepsza_trasa, czas_wykonania
    """
    n = len(coords)
    pheromones = aco.create_matrix_of_pheromones(n)
    
    best_global_dist = float('inf')
    best_global_path = []
    iteration_best_distances = []

    start_time = time.time()

    # Główna pętla iteracji (T)
    for _ in range(params['T']):
        # Tworzenie mrówek (zakładamy, że funkcja przyjmuje: liczba_mrowek, liczba_miast)
        ants_colony : List[Ant] = aco.create_ants_population(params['m'], n) 
        
        # 1. Budowanie trasy
        for _ in range(n - 1):
            for ant in ants_colony:
                ant.visit_next_location(distances, pheromones, params['alpha'], params['beta'], params['p_random'])

        # 2. Ewaluacja i wybór najlepszej mrówki w tej iteracji
        iteration_best = float('inf')
        for ant in ants_colony:
            total_dist = ant.get_total_distance(distances)
            if total_dist < best_global_dist:
                best_global_dist = total_dist
                best_global_path = ant.seen_locations[:]
            if total_dist < iteration_best:
                iteration_best = total_dist

        iteration_best_distances.append(iteration_best)


        # 3. Aktualizacja feromonów
        aco.update_pheromones(pheromones, distances, ants_colony, params['rho'])
        
    mean_dist = statistics.mean(iteration_best_distances)
    duration = time.time() - start_time

    return best_global_dist, best_global_path, mean_dist, duration

def plot_route(coords, path, title, filepath):
    """Rysuje mapę trasy"""
    if not path: return
    
    x = [coords[i][0] for i in path]
    y = [coords[i][1] for i in path]
    # Domknięcie pętli
    x.append(coords[path[0]][0])
    y.append(coords[path[0]][1])

    plt.figure(figsize=(8, 6))
    plt.plot(x, y, 'o-', mfc='r', label='Trasa')
    # Opcjonalnie: numery miast (można wyłączyć dla czytelności przy 80 miastach)
    if len(coords) < 50:
        for i, (cx, cy) in enumerate(coords):
            plt.text(cx, cy, str(i), fontsize=8, color='blue')
            
    plt.title(title)
    plt.grid(True)
    plt.savefig(filepath)
    plt.close()

def plot_mean_of_runs_distances(means, params, title, filepath):
    plt.figure(figsize=(8, 6))

    x = range(1, len(means) + 1)
    plt.plot(x, means, marker = 'o', ls = '--')

    std = statistics.stdev(means)  if len(means) > 1 else 0.0

    plt.title(title + '\nm: ' + str(params['m']) + ', p_random: ' + str(params['p_random']) + ', alpha: ' + str(params['alpha']) + ', beta: ' + str(params['beta']) + ', T: ' + str(params['T']) + ', rho: ' + str(params['rho']))
    plt.xticks(x)

    plt.errorbar(x, means, yerr=std, linestyle='--', fmt='o', capsize=5, ecolor='red', color='blue')
    plt.xlabel('Numery uruchomień')
    plt.ylabel('Najkrótszy dystans')
    plt.grid(True)
    plt.savefig(filepath)
    plt.close()


def main():
    # --- KONFIGURACJA ---
    print("=== ALGORYTM MRÓWKOWY - PEŁNE EKSPERYMENTY ===")
    
    # Wybór pliku
    filename = "A-n32-k5.txt"
    print(f"Domyślny plik: {filename}")
    choice = input("Wpisz '2' aby wybrać A-n80-k10.txt, lub Enter by zostawić domyślny: ")
    if choice == '2': 
        filename = 'A-n80-k10.txt'

    if not os.path.exists(filename):
        print(f"BŁĄD: Brak pliku {filename}")
        return

    # Przygotowanie folderu na wyniki
    output_dir = "wyniki_eksperymentu"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Utworzono folder na wyniki: {output_dir}")
    else:
        print(f"Wyniki będą zapisywane w folderze: {output_dir}")

    # Wczytanie danych
    distances, coords = aco.create_matrix_of_distances(filename)
    print(f"Wczytano {len(coords)} miast.")

    # Parametry bazowe
    base_params = {
        'm': 20,           # Liczba mrówek
        'p_random': 0.01,  # Szansa na losowy ruch
        'alpha': 1.0,      # Waga feromonu
        'beta': 2.0,       # Waga odległości
        'T': 50,           # Liczba iteracji
        'rho': 0.3         # Parowanie
    }

    # Plan testów
    experiments_plan = {
        "m": [10, 20, 50, 100],
        "p_random": [0.0, 0.01, 0.05, 0.1],
        "alpha": [0.5, 1.0, 2.0, 5.0],
        "beta": [1.0, 2.0, 5.0, 10.0],
        "T": [10, 50, 100],
        "rho": [0.1, 0.3, 0.5, 0.8]
    }
    
    # Słownik na wyniki zbiorcze (do wykresów podsumowujących)
    # Klucz: nazwa parametru -> (wartości_x, średnie_y, błędy_y, średnie_czasy)
    stats_summary = {}

    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_csv_path = os.path.join(output_dir, f"summary_{run_tag}.csv")
    summary_file = open(summary_csv_path, "w", newline="", encoding="utf-8")
    summary_writer = csv.writer(summary_file, delimiter=";")

    summary_writer.writerow([
        "Badany parametr",
        "Wartosc parametru",
        "Sredni dystans",
        "Mediana",
        "Najkrotsza trasa",
        "Najdluzsza trasa",
        "Odchylenie standardowe",
        "Sredni czas"
    ])

    print("\nRozpoczynam serię eksperymentów...")

    for param_name, values in experiments_plan.items():
        print(f"\n>>> Badanie parametru: {param_name} <<<")
        
        # Listy na statystyki zbiorcze dla tego parametru
        agg_means_dist = []
        agg_stds_dist = []
        agg_means_time = []
        
        for val in values:
            # Ustawienie parametrów
            current_params = base_params.copy()
            current_params[param_name] = val
            
            # Zmienne na wyniki 5 uruchomień tego konkretnego scenariusza
            runs_distances = []
            mean_distances = []
            runs_times = []
            
            best_batch_dist = float('inf')
            best_batch_path = None

            print(f" Scenariusz {param_name} = {val}")

            # 2. Wykonanie 5 powtórzeń
            for i in range(5):
                dist, path, mean_dist, duration = run_experiment(distances, coords, current_params)
                
                runs_distances.append(dist)
                runs_times.append(duration)
                mean_distances.append(mean_dist)

                # Szukanie najlepszej trasy w tej serii
                if dist < best_batch_dist:
                    best_batch_dist = dist
                    best_batch_path = path

                print(f" Run {i + 1}/5: dist={dist:.2f}, time={duration:.4f}s")

            # statystyki po 5 uruchomieniach
            mean_res = statistics.mean(runs_distances)
            median_res = statistics.median(runs_distances)
            std_res = statistics.stdev(runs_distances) if len(runs_distances) > 1 else 0.0
            min_res = min(runs_distances)  # najlepszy
            max_res = max(runs_distances)  # najgorszy
            mean_time = statistics.mean(runs_times)

            print(f"| Wartość parametru {val} | Średni dystans = {mean_res:.2f} | Mediana = {median_res:.2f}"
                f" | Najkrótsza trasa = {min_res:.2f} | Najdłuższa trasa = {max_res:.2f} |"
                  f" Odchylenie st. = {std_res:.2f} | Średni czas = {mean_time:.4f}s "
            )

            # Zapis do pliku csv (ułatwi sprawko)
            summary_writer.writerow([
                param_name,
                val,
                f"{mean_res:.2f}",
                f"{median_res:.2f}",
                f"{min_res:.2f}",
                f"{max_res:.2f}",
                f"{std_res:.2f}",
                f"{mean_time:.4f}",
            ])

            # 3. GENEROWANIE WYKRESÓW DLA SCENARIUSZA
            # Mapa najlepszej trasy w tej serii
            route_filename = os.path.join(output_dir, f"route_{param_name}_{val}.png")
            plot_route(coords, best_batch_path, 
                       f"Najlepsza trasa: {param_name}={val} (Dystans: {best_batch_dist:.2f})", 
                       route_filename)

            # 4. Zbieranie statystyk do podsumowania
            mean_d = statistics.mean(runs_distances)
            std_d = statistics.stdev(runs_distances) if len(runs_distances) > 1 else 0.0
            mean_t = statistics.mean(runs_times)

            plot_mean_of_runs_distances(mean_distances, current_params, "Średnia dla każdego z 5 uruchomień dla parametrów", f'wyniki_eksperymentu/stats_{param_name}_{current_params[param_name]}.png')
            
            
            agg_means_dist.append(mean_d)
            agg_stds_dist.append(std_d)
            agg_means_time.append(mean_t)

        # Zapisanie zbiorczych danych
        stats_summary[param_name] = (values, agg_means_dist, agg_stds_dist, agg_means_time)

    summary_file.close()
    print(f"\nZapisano podsumowanie do: {summary_csv_path}")

    # --- GENEROWANIE RAPORTU ZBIORCZEGO ---
    print("\nGenerowanie wykresów podsumowujących...")
    
    # 1. Wykresy wrażliwości (Dystans)
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'Podsumowanie: Jakość rozwiązania (Dystans) - {filename}', fontsize=16)
    axs = axs.ravel()
    
    for i, (param, data) in enumerate(stats_summary.items()):
        vals, means, stds, _ = data
        axs[i].errorbar(vals, means, yerr=stds, fmt='-o', capsize=5, ecolor='red', color='blue')
        axs[i].set_title(f'Wpływ {param}')
        axs[i].set_xlabel('Wartość')
        axs[i].set_ylabel('Średni dystans')
        axs[i].grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'summary_distance.png'))

    # 2. Wykresy wrażliwości (Czas)
    fig_t, axs_t = plt.subplots(2, 3, figsize=(15, 10))
    fig_t.suptitle(f'Podsumowanie: Czas wykonania - {filename}', fontsize=16)
    axs_t = axs_t.ravel()
    
    for i, (param, data) in enumerate(stats_summary.items()):
        vals, _, _, times = data
        axs_t[i].plot(vals, times, 's--', color='green')
        axs_t[i].set_title(f'Wpływ {param} na czas')
        axs_t[i].set_xlabel('Wartość')
        axs_t[i].set_ylabel('Średni czas [s]')
        axs_t[i].grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'summary_time.png'))
    
    print(f"Zakończono! Wszystkie wyniki znajdują się w folderze '{output_dir}'.")
    plt.show()

if __name__ == "__main__":
    main()