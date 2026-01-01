import math
import random
from typing import List

class Ant:
    def __init__(self, num_of_locations):
        self.num_of_locations = num_of_locations
        # Losowy wybór pierwszej lokacji
        self.seen_locations = [random.randint(0, num_of_locations - 1)]

    def visit_next_location(self, distances, pheromones, alpha, beta, p_random):
        selected_location = self.select_next_location(distances, pheromones, alpha, beta, p_random)
        if selected_location is None:
            # brak dostępnych lokacji do odwiedzenia
            return False
        else:
            self.seen_locations.append(selected_location)
            return True

    # Dystans pokonany
    def get_total_distance(self, distances):
        total_distance = 0.0
        for i in range(1, len(self.seen_locations)):
            total_distance += distances[self.seen_locations[i-1]][self.seen_locations[i]]
        start = self.seen_locations[i-1]
        end = self.seen_locations[i]
        # Droga powrotna do lokacji startowej
        total_distance += distances[start][end]
        return total_distance
    
    def select_next_location(self, distances, pheromones, alpha, beta, p_random):
        current = self.seen_locations[-1]
        n = len(distances)
        # Lista dostępnych miast
        available = [i for i in range(n) if i not in self.seen_locations]
        
        if not available:
            return None

        # Wybór losowy (eksploracja)
        if random.random() < p_random:
            return random.choice(available)

        # Wybór probabilistycznie
        probabilities = []
        sum_of_probabilities = 0.0

        for loc in available:
            current_pheromons = pheromones[current][loc] ** alpha
            dist = distances[current][loc]
            current_heuristic = (1.0 / dist) ** beta if dist > 0 else 100.0
            
            value = current_pheromons * current_heuristic
            probabilities.append(value)
            sum_of_probabilities += value

        # Zabezpieczenie przed dzieleniem przez zero
        if sum_of_probabilities == 0:
            return random.choice(available)

        # Ruletka
        pick = random.uniform(0, sum_of_probabilities)
        current_val = 0
        for i, probability in enumerate(probabilities):
            current_val += probability
            if current_val >= pick:
                return available[i]
        
        return available[-1]

def update_pheromones(pheromones : List[List[float]], distances : List[List[float]], ants : List[Ant], evaporation : float):
    n = len(pheromones)
    # Wyparowywanie
    for i in range(n):
        for j in range(n):
            pheromones[i][j] *= (1.0 - evaporation)
            # Dolny limit
            if pheromones[i][j] < 0.01:
                pheromones[i][j] = 0.01
    # Nakładanie śladów mrówek
    for ant in ants:
        dist = ant.get_total_distance(distances)
        if dist > 0:
            deposit = 1.0 / dist
            path = ant.seen_locations
            for k in range(len(path) - 1):
                u = path[k]
                v = path[k+1]
                # dodanie dla feromona oraz jego odwrotności, żeby zachować spójność
                pheromones[u][v] += deposit
                pheromones[v][u] += deposit

def create_matrix_of_distances(pathfile):
    coordinates = []
    with open(pathfile, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].isdigit():
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    coordinates.append((x, y))
                except ValueError:
                    continue
    
    n = len(coordinates)
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                x1, y1 = coordinates[i]
                x2, y2 = coordinates[j]
                dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                matrix[i][j] = dist
                
    return matrix, coordinates

def create_matrix_of_pheromones(n):
    # początkowe założenie: wszystkie feromony równe 1.0
    return [[1.0 for _ in range(n)] for _ in range(n)]

def create_ants_population(ant_base : int, num_of_locations : int):
    ant_colony = []
    for _ in range(ant_base):
        ant_colony.append(Ant(num_of_locations))
    return ant_colony

