# Class chính điều khiển thuật toán di truyền

import random
from app.models.domain import Individual
from .fitness import calculate_fitness
from .mutation import apply_smart_mutation

class GeneticAlgorithm:
    def __init__(self, all_pois, user_prefs):
        self.all_pois = all_pois
        self.prefs = user_prefs
        self.pop_size = 50
        self.generations = 100

    def init_population(self):
        population = []
        for _ in range(self.pop_size):
            # Tạo ngẫu nhiên: Shuffle list rồi cắt bớt cho vừa thời gian
            # (Ở đây làm đơn giản là lấy sample)
            k = random.randint(3, len(self.all_pois))
            route = random.sample(self.all_pois, k)
            ind = Individual(route)
            calculate_fitness(ind, self.prefs)
            population.append(ind)
        return population

    def run(self):
        population = self.init_population()

        for gen in range(self.generations):
            # Sort giảm dần theo fitness
            population.sort(key=lambda x: x.fitness, reverse=True)

            # Elitism: Giữ top 2
            next_gen = population[:2]

            # Tạo thế hệ mới (Giả lập đơn giản để chạy được flow)
            while len(next_gen) < self.pop_size:
                # 1. Selection (Lấy top 50%)
                parent = random.choice(population[:int(self.pop_size/2)])

                # 2. Clone (Thay cho Crossover phức tạp tạm thời)
                child = Individual(parent.route[:])

                # 3. Hybrid Mutation (Quan trọng)
                if random.random() < 0.3:
                    child = apply_smart_mutation(child, self.prefs)

                calculate_fitness(child, self.prefs)
                next_gen.append(child)

            population = next_gen

        # Trả về cá thể tốt nhất
        return population[0]