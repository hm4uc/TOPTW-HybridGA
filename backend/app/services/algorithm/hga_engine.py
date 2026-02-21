from app.models.domain import Individual
from app.models.schemas import UserPreferences
from app.services.data_loader import load_solomon_c101
from app.services.algorithm.initialization import initialize_population, POPULATION_SIZE
from app.services.algorithm.fitness import calculate_fitness


class HybridGeneticAlgorithm:
    def __init__(self, user_prefs: UserPreferences):
        self.user_prefs = user_prefs
        self.pois = load_solomon_c101()
        self.depot = next((p for p in self.pois if p.id == 0), None)
        self.population_size = POPULATION_SIZE  # 50
        self.mutation_rate = 0.3
        self.generations = 50
        self.elitism_rate = 2
        self.population: list[Individual] = []

    # ── Step 1: Population Initialization ────────────────────────────────
    def initialize_population(self) -> list[Individual]:
        """
        Generate the initial population using a mix of:
          • 80% Randomized Insertion Heuristic (40 individuals)
          • 20% Pure Random                    (10 individuals)
        """
        self.population = initialize_population(self.pois, self.user_prefs)

        # Evaluate fitness for every individual
        for ind in self.population:
            calculate_fitness(ind, self.user_prefs)

        # Sort by fitness descending (best first)
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)

        print(f"[HGA] Population initialized and evaluated.")
        print(f"      Best fitness  = {self.population[0].fitness:.2f}")
        print(f"      Worst fitness = {self.population[-1].fitness:.2f}")

        return self.population

    # ── Step 2: Fitness Evaluation ───────────────────────────────────────
    def evaluate_fitness(self, individual: Individual) -> float:
        return calculate_fitness(individual, self.user_prefs)

    # ── Step 3: Parent Selection ─────────────────────────────────────────
    def select_parents(self, population):
        # Select parents from the population based on fitness
        pass

    # ── Step 4: Crossover ────────────────────────────────────────────────
    def crossover(self, parent1, parent2):
        # Perform crossover between two parents to produce offspring
        pass

    # ── Step 5: Mutation ─────────────────────────────────────────────────
    def mutate(self, individual):
        # Mutate an individual based on the mutation rate
        pass

    # ── Main Loop ────────────────────────────────────────────────────────
    def run(self):
        """Run the hybrid genetic algorithm."""
        self.initialize_population()
        # TODO: Implement the main GA loop (selection → crossover → mutation → replacement)
        pass