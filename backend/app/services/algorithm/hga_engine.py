"""
Hybrid Genetic Algorithm Engine (HGA) — TOPTW Solver

Luồng chính mỗi thế hệ:
  1. Elitism   – giữ nguyên N cá thể tốt nhất.
  2. Selection – Tournament Selection chọn cặp cha-mẹ.
  3. Crossover – Order Crossover OX1 (trên interior).
  4. Mutation  – 2-opt / Swap / Insertion (trên interior).
  5. Smart Repair – xóa POI có tỷ lệ Score/Time kém nhất.
  6. Diversity – loại con trùng lặp, thay bằng cá thể random.
  7. Evaluate  – tính fitness cho con mới.
  8. Replace   – thay thế quần thể, sắp xếp, lặp lại.

Nguyên tắc "Depot-Safe":
  Mọi toán tử GA đều CHỈ thao tác trên "interior" = route[1:-1].
  Depot được gắn lại sau khi xử lý xong.
"""

import random
from typing import Optional, List

from app.models.domain import POI, Individual
from app.models.schemas import UserPreferences
from app.services.data_loader import load_solomon_c101
from app.services.algorithm.initialization import (
    initialize_population,
    POPULATION_SIZE,
    _create_random_individual,
)
from app.services.algorithm.fitness import (
    calculate_fitness,
    check_constraints,
    get_travel_time,
    build_distance_matrix,
)


class HybridGeneticAlgorithm:
    def __init__(self, user_prefs: UserPreferences):
        self.user_prefs = user_prefs
        self.pois = load_solomon_c101()

        # ── Pre-compute Distance Matrix (O(1) lookups) ────────────────────
        build_distance_matrix(self.pois)
        self.depot: Optional[POI] = next(
            (p for p in self.pois if p.id == 0), None
        )
        self.poi_map = {p.id: p for p in self.pois}
        self.population_size = POPULATION_SIZE   # 50
        self.mutation_rate   = 0.3
        self.generations     = 200               # Max cap (early stopping sẽ bảo vệ)
        self.stagnation_limit = 15               # Dừng nếu 15 gen không cải thiện
        self.improvement_threshold = 1e-4        # Min delta để tính là "cải thiện"
        self.elitism_rate    = 2
        self.tournament_k    = 3
        self.population: list[Individual] = []

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 1: Population Initialization
    # ══════════════════════════════════════════════════════════════════════════
    def initialize_population(self) -> list[Individual]:
        self.population = initialize_population(self.pois, self.user_prefs)
        for ind in self.population:
            calculate_fitness(ind, self.user_prefs)
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)

        print("[HGA] Population initialized and evaluated.")
        print(f"      Best fitness  = {self.population[0].fitness:.2f}")
        print(f"      Worst fitness = {self.population[-1].fitness:.2f}")
        return self.population

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 2: Fitness Evaluation
    # ══════════════════════════════════════════════════════════════════════════
    def evaluate_fitness(self, individual: Individual) -> float:
        return calculate_fitness(individual, self.user_prefs)

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 3: Parent Selection — Tournament
    # ══════════════════════════════════════════════════════════════════════════
    def select_parents(
        self, population: list[Individual]
    ) -> tuple[Individual, Individual]:
        """
        Tournament Selection: chọn k cá thể ngẫu nhiên, lấy cá thể tốt nhất.
        """
        def tournament(pop: list[Individual]) -> Individual:
            contestants = random.sample(pop, min(self.tournament_k, len(pop)))
            return max(contestants, key=lambda ind: ind.fitness)

        return tournament(population), tournament(population)

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 4: Crossover — Order Crossover OX1 (Depot-Safe)
    # ══════════════════════════════════════════════════════════════════════════
    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """
        OX1 chỉ thao tác trên interior (bỏ Depot 2 đầu).
        """
        r1 = parent1.route[1:-1]
        r2 = parent2.route[1:-1]

        size = min(len(r1), len(r2))
        if size < 2:
            return Individual(route=list(parent1.route))

        r1, r2 = r1[:size], r2[:size]

        cut1, cut2 = sorted(random.sample(range(size), 2))

        child_interior: list[Optional[POI]] = [None] * size

        segment_ids = set()
        for k in range(cut1, cut2 + 1):
            child_interior[k] = r1[k]
            segment_ids.add(r1[k].id)

        remaining = [poi for poi in r2 if poi.id not in segment_ids]
        empty_positions = [k for k in range(size) if child_interior[k] is None]
        for pos, poi in zip(empty_positions, remaining):
            child_interior[pos] = poi

        child_interior_clean = [p for p in child_interior if p is not None]

        new_route = [self.depot] + child_interior_clean + [self.depot]
        return Individual(route=new_route)

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 5: Mutation — 2-opt / Swap / Insertion  (Depot-Safe)
    # ══════════════════════════════════════════════════════════════════════════

    def mutate(self, individual: Individual) -> Individual:
        """
        Áp dụng 1 trong 3 kiểu đột biến:
          • 2-opt     (30%) : đảo ngược đoạn con → giảm quãng đường.
          • Swap      (30%) : hoán đổi 2 POI → thay đổi thứ tự.
          • Insertion (40%) : tìm POI mới chưa đi, chèn vào vị trí tốt nhất
                              → TĂNG ĐIỂM (biến thời gian dư thành điểm thưởng).
        """
        if random.random() > self.mutation_rate:
            return individual

        interior = list(individual.route[1:-1])

        if len(interior) < 2:
            individual = self._insertion_mutation(individual)
            return individual

        roll = random.random()

        if roll < 0.30:
            # ── 2-opt ────────────────────────────────────────────────────────
            i, j = sorted(random.sample(range(len(interior)), 2))
            interior[i:j + 1] = interior[i:j + 1][::-1]
            individual.route = [self.depot] + interior + [self.depot]

        elif roll < 0.60:
            # ── Swap ─────────────────────────────────────────────────────────
            i, j = random.sample(range(len(interior)), 2)
            interior[i], interior[j] = interior[j], interior[i]
            individual.route = [self.depot] + interior + [self.depot]

        else:
            # ── Insertion Mutation ────────────────────────────────────────────
            individual = self._insertion_mutation(individual)

        return individual

    def _insertion_mutation(self, individual: Individual) -> Individual:
        """
        ★ INSERTION MUTATION — Toán tử cốt lõi để phá Hội tụ sớm ★

        Tìm POI chưa ghé thăm, chèn vào vị trí tốn ít thời gian nhất.
        Lấy tối đa 10 ứng viên ngẫu nhiên để giữ hiệu năng.
        """
        route = list(individual.route)
        visited_ids = {p.id for p in route}
        unvisited = [p for p in self.pois if p.id not in visited_ids and p.id != 0]

        if not unvisited:
            return individual

        random.shuffle(unvisited)
        candidates = unvisited[:10]

        weights = self.user_prefs.interest_weights
        candidates.sort(
            key=lambda p: p.base_score * weights.get(p.category, 0.0),
            reverse=True,
        )

        for candidate in candidates:
            best_pos = -1
            best_cost_increase = float('inf')

            for pos in range(1, len(route)):
                prev_poi = route[pos - 1]
                next_poi = route[pos]

                old_travel = get_travel_time(prev_poi, next_poi)
                new_travel = (
                    get_travel_time(prev_poi, candidate)
                    + candidate.duration
                    + get_travel_time(candidate, next_poi)
                )
                cost_increase = new_travel - old_travel

                if cost_increase < best_cost_increase:
                    best_cost_increase = cost_increase
                    best_pos = pos

            if best_pos > 0:
                test_route = list(route)
                test_route.insert(best_pos, candidate)
                if check_constraints(test_route, self.user_prefs):
                    route = test_route

        individual.route = route
        return individual

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 6: Smart Repair (Bước 3 — Xóa POI kém nhất, không phải cuối)
    # ══════════════════════════════════════════════════════════════════════════
    def _repair(self, individual: Individual) -> Individual:
        """
        ★ SMART REPAIR — Xóa POI có tỷ lệ Score/Time kém nhất ★

        Thay vì luôn xóa POI áp chót (có thể là POI rất tốt),
        chúng ta tìm POI có "giá trị" thấp nhất trong interior
        và xóa nó. Giá trị = (base_score × interest_weight) / added_time.

        Nếu POI tốn nhiều thời gian nhưng chỉ mang lại ít điểm → xóa trước.

        Vẫn đảm bảo Depot-Safe: chỉ xóa trong interior (route[1:-1]).
        """
        route = individual.route

        while not check_constraints(route, self.user_prefs) and len(route) > 2:
            # Tìm POI kém nhất trong interior (index 1 đến len-2)
            worst_idx = -1
            worst_value = float('inf')
            weights = self.user_prefs.interest_weights

            for i in range(1, len(route) - 1):
                poi = route[i]

                # Tính điểm thực tế của POI này
                score_value = poi.base_score * weights.get(poi.category, 0.0)

                # Tính thời gian POI này "ngốn" khỏi lộ trình
                # = travel(prev → poi) + poi.duration + travel(poi → next) - travel(prev → next)
                prev_poi = route[i - 1]
                next_poi = route[i + 1]
                time_cost = (
                    get_travel_time(prev_poi, poi)
                    + poi.duration
                    + get_travel_time(poi, next_poi)
                    - get_travel_time(prev_poi, next_poi)
                )

                # Tỷ lệ giá trị: score mang lại / thời gian tốn
                # POI có ratio thấp nhất = kém nhất → ưu tiên xóa
                if time_cost > 0:
                    ratio = score_value / time_cost
                else:
                    ratio = float('inf')  # Không tốn thời gian → giữ lại

                if ratio < worst_value:
                    worst_value = ratio
                    worst_idx = i

            if worst_idx > 0:
                route.pop(worst_idx)
            else:
                # Fallback: xóa áp chót
                route.pop(-2)

        individual.route = route
        return individual

    # ══════════════════════════════════════════════════════════════════════════
    #  Diversity Check (Bước 2 — Chống đồng huyết)
    # ══════════════════════════════════════════════════════════════════════════
    def _is_duplicate(self, child: Individual, population: list[Individual]) -> bool:
        """
        Kiểm tra cá thể `child` có trùng lặp với bất kỳ cá thể nào
        trong `population` hay không.

        Hai cá thể được coi là "trùng" nếu tập hợp POI ID giống hệt nhau
        (không cần cùng thứ tự — vì thứ tự có thể khác nhưng bản chất giống).
        """
        child_ids = frozenset(p.id for p in child.route[1:-1])
        for ind in population:
            existing_ids = frozenset(p.id for p in ind.route[1:-1])
            if child_ids == existing_ids:
                return True
        return False

    def _create_diverse_individual(self) -> Individual:
        """
        Tạo 1 cá thể Random hoàn toàn mới khi phát hiện bản sao.
        Đảm bảo quần thể luôn có sự đa dạng.
        """
        ind = _create_random_individual(self.pois, self.depot, self.user_prefs)
        calculate_fitness(ind, self.user_prefs)
        return ind

    # ══════════════════════════════════════════════════════════════════════════
    #  Main Loop — Early Stopping + Enhanced Logging
    # ══════════════════════════════════════════════════════════════════════════
    def run(self) -> Individual:
        """
        Chạy vòng lặp tiến hóa chính của Hybrid GA.

        ★ EARLY STOPPING ★
          Nếu best fitness không cải thiện (>= threshold) trong
          `stagnation_limit` thế hệ liên tiếp → dừng sớm.
          Giúp API phản hồi nhanh hơn khi thuật toán đã hội tụ.

        Log mỗi thế hệ:
          • Best Fitness / Average Fitness
          • Unique Routes (diversity)
          • Wait Time (best individual)
          • Stagnation counter (bao nhiêu gen chưa cải thiện)
        """
        self.initialize_population()
        best_ever = self.population[0]
        gens_without_improvement = 0
        actual_gens = 0

        for gen in range(self.generations):
            actual_gens = gen + 1

            new_population: list[Individual] = list(
                self.population[:self.elitism_rate]
            )

            duplicates_replaced = 0

            while len(new_population) < self.population_size:
                p1, p2 = self.select_parents(self.population)
                child = self.crossover(p1, p2)
                child = self.mutate(child)
                child = self._repair(child)
                calculate_fitness(child, self.user_prefs)

                # ── Diversity Check ──────────────────────────────────────────
                if self._is_duplicate(child, new_population):
                    child = self._create_diverse_individual()
                    duplicates_replaced += 1

                new_population.append(child)

            new_population.sort(key=lambda ind: ind.fitness, reverse=True)
            self.population = new_population

            # ── Cập nhật Best Ever + Early Stopping ───────────────────────────
            improvement = self.population[0].fitness - best_ever.fitness
            if improvement > self.improvement_threshold:
                best_ever = self.population[0]
                gens_without_improvement = 0
            else:
                gens_without_improvement += 1

            # ── Enhanced Logging ──────────────────────────────────────────────
            best_fit = self.population[0].fitness
            avg_fit = sum(ind.fitness for ind in self.population) / len(self.population)

            # Đếm số lộ trình duy nhất (unique routes)
            unique_routes = len({
                frozenset(p.id for p in ind.route[1:-1])
                for ind in self.population
            })

            print(
                f"[HGA] Gen {gen + 1:>3}/{self.generations} | "
                f"Best = {best_fit:8.2f} | "
                f"Avg = {avg_fit:8.2f} | "
                f"Unique = {unique_routes:>2}/{self.population_size} | "
                f"Wait = {self.population[0].total_wait:6.1f} | "
                f"Stag = {gens_without_improvement:>2}/{self.stagnation_limit} | "
                f"Dup = {duplicates_replaced}"
            )

            # ── Early Stopping Check ──────────────────────────────────────────
            if gens_without_improvement >= self.stagnation_limit:
                print(
                    f"\n[HGA] ★ EARLY STOPPING ★ "
                    f"Best fitness không cải thiện trong "
                    f"{self.stagnation_limit} thế hệ liên tiếp. "
                    f"Dừng tại gen {gen + 1}/{self.generations}."
                )
                break

        print(f"\n[HGA] ═══ KẾT QUẢ CUỐI CÙNG ═══")
        print(f"      Generations run   = {actual_gens}/{self.generations}")
        print(f"      Best-ever fitness = {best_ever.fitness:.2f}")
        print(f"      Total wait time   = {best_ever.total_wait:.1f}")
        print(f"      Route IDs   : {[p.id for p in best_ever.route]}")
        print(f"      Route length: {len(best_ever.route)} nodes "
              f"({len(best_ever.route) - 2} POIs + 2 Depot)")
        return best_ever