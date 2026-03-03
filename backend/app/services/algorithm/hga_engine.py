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

★ ABLATION FLAGS ★
  Hỗ trợ tắt/bật từng thành phần để đánh giá đóng góp (Ablation Study).
"""

import random
import time
from typing import Optional, List

from app.models.domain import POI, Individual
from app.models.schemas import UserPreferences, OptimizationResponse, ItineraryItem
from app.services.data_loader import load_solomon_instance
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
    PENALTY_WAIT,
)


def _format_time(minutes: float) -> str:
    """
    Chuyển đổi thời gian dạng PHÚT (Solomon time units) sang chuỗi HH:MM.
    VD: 480.0 → "08:00", 612.5 → "10:12"
    """
    total_minutes = int(round(minutes))
    hours = total_minutes // 60
    mins = total_minutes % 60
    return f"{hours:02d}:{mins:02d}"


class HybridGeneticAlgorithm:
    def __init__(
        self,
        user_prefs: UserPreferences,
        pois: Optional[List[POI]] = None,
        instance_name: str = "C101",
        # ── Ablation Flags ──────────────────────────────────────────
        use_smart_repair: bool = True,        # False → Simple Repair (xóa cuối)
        use_insertion_mutation: bool = True,   # False → chỉ 2-opt + Swap
        use_wait_penalty: bool = True,         # False → PENALTY_WAIT = 0
        use_heuristic_init: bool = True,       # False → 100% Random Init
        use_diversity_check: bool = True,      # False → không check duplicate
        # ── Tunable Parameters ──────────────────────────────────────
        population_size: int = POPULATION_SIZE,
        mutation_rate: float = 0.7,
        generations: int = 200,
        stagnation_limit: int = 25,
        tournament_k: int = 3,
    ):
        self.user_prefs = user_prefs

        # ── Load dữ liệu ────────────────────────────────────────────
        if pois is not None:
            self.pois = pois
        else:
            self.pois = load_solomon_instance(instance_name)

        # ── Pre-compute Distance Matrix ──────────────────────────────
        build_distance_matrix(self.pois)
        self.depot: Optional[POI] = next(
            (p for p in self.pois if p.id == 0), None
        )
        self.poi_map = {p.id: p for p in self.pois}

        # ── Ablation Flags ───────────────────────────────────────────
        self.use_smart_repair = use_smart_repair
        self.use_insertion_mutation = use_insertion_mutation
        self.use_wait_penalty = use_wait_penalty
        self.use_heuristic_init = use_heuristic_init
        self.use_diversity_check = use_diversity_check

        # ── GA Parameters ────────────────────────────────────────────
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.stagnation_limit = stagnation_limit
        self.improvement_threshold = 1e-4
        self.elitism_rate = 5
        self.tournament_k = tournament_k
        self.population: list[Individual] = []

        # ── Wait penalty weight (configurable for ablation) ──────────
        self.wait_penalty_weight = PENALTY_WAIT if use_wait_penalty else 0.0

        # ── Results Tracking ─────────────────────────────────────────
        self.convergence_log: list[dict] = []
        self.actual_gens: int = 0
        self.best_individual: Optional[Individual] = None

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 1: Population Initialization
    # ══════════════════════════════════════════════════════════════════════════
    def initialize_population(self) -> list[Individual]:
        self.population = initialize_population(
            self.pois, self.user_prefs,
            use_heuristic_init=self.use_heuristic_init,
        )
        # ★ Cải tiến: Repair + Greedy Refill cho MỖI cá thể khởi tạo
        #   → Giảm khoảng cách Best vs Avg fitness ngay từ Gen 1.
        for i, ind in enumerate(self.population):
            ind = self._repair(ind)
            ind = self._greedy_refill(ind)
            calculate_fitness(ind, self.user_prefs, self.wait_penalty_weight)
            self.population[i] = ind
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)

        print("[HGA] Population initialized and evaluated.")
        print(f"      Best fitness  = {self.population[0].fitness:.2f}")
        print(f"      Worst fitness = {self.population[-1].fitness:.2f}")
        return self.population

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 2: Fitness Evaluation
    # ══════════════════════════════════════════════════════════════════════════
    def evaluate_fitness(self, individual: Individual) -> float:
        return calculate_fitness(individual, self.user_prefs, self.wait_penalty_weight)

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
        Áp dụng đột biến (Depot-Safe).

        Chế độ mặc định (use_insertion_mutation=True):
          • 2-opt     (30%) : đảo ngược đoạn con → giảm quãng đường.
          • Swap      (30%) : hoán đổi 2 POI → thay đổi thứ tự.
          • Insertion (40%) : tìm POI mới chưa đi, chèn vào vị trí tốt nhất.

        Chế độ ablation (use_insertion_mutation=False):
          • 2-opt     (50%)
          • Swap      (50%)
        """
        if random.random() > self.mutation_rate:
            return individual

        interior = list(individual.route[1:-1])

        if len(interior) < 2:
            if self.use_insertion_mutation:
                individual = self._insertion_mutation(individual)
            return individual

        roll = random.random()

        if self.use_insertion_mutation:
            # ── Chế độ đầy đủ: 2-opt(30%) / Swap(30%) / Insertion(40%) ──
            if roll < 0.30:
                i, j = sorted(random.sample(range(len(interior)), 2))
                interior[i:j + 1] = interior[i:j + 1][::-1]
                individual.route = [self.depot] + interior + [self.depot]
            elif roll < 0.60:
                i, j = random.sample(range(len(interior)), 2)
                interior[i], interior[j] = interior[j], interior[i]
                individual.route = [self.depot] + interior + [self.depot]
            else:
                individual = self._insertion_mutation(individual)
        else:
            # ── Ablation: chỉ 2-opt(50%) + Swap(50%) ────────────────────
            if roll < 0.50:
                i, j = sorted(random.sample(range(len(interior)), 2))
                interior[i:j + 1] = interior[i:j + 1][::-1]
                individual.route = [self.depot] + interior + [self.depot]
            else:
                i, j = random.sample(range(len(interior)), 2)
                interior[i], interior[j] = interior[j], interior[i]
                individual.route = [self.depot] + interior + [self.depot]

        return individual

    def _insertion_mutation(self, individual: Individual) -> Individual:
        """
        ★ INSERTION MUTATION — Toán tử cốt lõi để phá Hội tụ sớm ★

        Tìm POI chưa ghé thăm, chèn vào vị trí tốn ít thời gian nhất.
        Duyệt TOÀN BỘ POI chưa thăm để không bỏ sót ứng viên tốt.
        """
        route = list(individual.route)
        visited_ids = {p.id for p in route}
        unvisited = [p for p in self.pois if p.id not in visited_ids and p.id != 0]

        if not unvisited:
            return individual

        # Sắp xếp theo score cá nhân hóa, xen kẽ random để giữ đa dạng
        weights = self.user_prefs.interest_weights
        random.shuffle(unvisited)
        unvisited.sort(
            key=lambda p: p.base_score * weights.get(p.category, 0.0),
            reverse=True,
        )

        for candidate in unvisited:
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
    #  Step 6: Repair (Smart or Simple)
    # ══════════════════════════════════════════════════════════════════════════
    def _repair(self, individual: Individual) -> Individual:
        """
        Sửa chữa cá thể vi phạm ràng buộc.

        Chế độ mặc định (use_smart_repair=True):
          ★ SMART REPAIR — xóa POI có tỷ lệ Score/Time kém nhất.

        Chế độ ablation (use_smart_repair=False):
          Simple Repair — luôn xóa POI áp chót.
        """
        route = individual.route

        while not check_constraints(route, self.user_prefs) and len(route) > 2:
            if self.use_smart_repair:
                # ── Smart Repair: tìm POI kém nhất ──────────────────────
                worst_idx = -1
                worst_value = float('inf')
                weights = self.user_prefs.interest_weights

                for i in range(1, len(route) - 1):
                    poi = route[i]
                    score_value = poi.base_score * weights.get(poi.category, 0.0)

                    prev_poi = route[i - 1]
                    next_poi = route[i + 1]
                    time_cost = (
                        get_travel_time(prev_poi, poi)
                        + poi.duration
                        + get_travel_time(poi, next_poi)
                        - get_travel_time(prev_poi, next_poi)
                    )

                    if time_cost > 0:
                        ratio = score_value / time_cost
                    else:
                        ratio = float('inf')

                    if ratio < worst_value:
                        worst_value = ratio
                        worst_idx = i

                if worst_idx > 0:
                    route.pop(worst_idx)
                else:
                    route.pop(-2)
            else:
                # ── Simple Repair: luôn xóa POI áp chót ─────────────────
                route.pop(-2)

        individual.route = route
        return individual

    # ══════════════════════════════════════════════════════════════════════════
    #  Step 6b: Greedy Refill — Lấp đầy route sau Repair
    # ══════════════════════════════════════════════════════════════════════════
    def _greedy_refill(self, individual: Individual) -> Individual:
        """
        ★ GREEDY REFILL — Chèn thêm POI vào route sau khi Repair xóa bớt ★

        Sau khi Repair cắt POI vi phạm, route thường rất ngắn (1-2 POI).
        Bước này tìm POI chưa ghé, thử chèn vào vị trí tốt nhất (tốn ít
        thời gian nhất), miễn là vẫn thỏa constraints.

        Ưu tiên POI theo: score × interest_weight (cao → thêm trước).
        Duyệt TOÀN BỘ POI chưa thăm (100 POI ~ O(1ms)).
        """
        route = list(individual.route)
        visited_ids = {p.id for p in route}
        unvisited = [p for p in self.pois if p.id not in visited_ids and p.id != 0]

        if not unvisited:
            individual.route = route
            return individual

        # Sắp xếp theo score cá nhân hóa (descending)
        weights = self.user_prefs.interest_weights
        unvisited.sort(
            key=lambda p: p.base_score * weights.get(p.category, 0.0),
            reverse=True,
        )

        for candidate in unvisited:
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
    #  Diversity Check (Chống đồng huyết)
    # ══════════════════════════════════════════════════════════════════════════
    def _is_duplicate(self, child: Individual, population: list[Individual]) -> bool:
        """
        Kiểm tra cá thể `child` có trùng lặp với bất kỳ cá thể nào
        trong `population` hay không.
        """
        child_ids = frozenset(p.id for p in child.route[1:-1])
        for ind in population:
            existing_ids = frozenset(p.id for p in ind.route[1:-1])
            if child_ids == existing_ids:
                return True
        return False

    def _create_diverse_individual(self) -> Individual:
        """
        Tạo 1 cá thể mới khi phát hiện bản sao.

        ★ Cải tiến: Thay vì random thuần (fitness rất thấp), ta:
          1. Tạo random cơ bản
          2. Repair nếu vi phạm
          3. Greedy Refill để lấp đầy route → chất lượng cao hơn nhiều
        → Giảm khoảng cách Best vs Avg fitness đáng kể.
        """
        ind = _create_random_individual(self.pois, self.depot, self.user_prefs)
        ind = self._repair(ind)
        ind = self._greedy_refill(ind)
        calculate_fitness(ind, self.user_prefs, self.wait_penalty_weight)
        return ind

    # ══════════════════════════════════════════════════════════════════════════
    #  Build API Response from best Individual
    # ══════════════════════════════════════════════════════════════════════════
    def _build_response(
        self, best: Individual, execution_time: float
    ) -> OptimizationResponse:
        """
        Chuyển đổi Individual tốt nhất thành OptimizationResponse.

        Mô phỏng lại timeline trên route để tính chính xác:
          • travel_distance, travel_time giữa 2 điểm liên tiếp
          • arrival, wait, start, leave tại mỗi POI
          • total_score, total_cost, total_distance, total_duration

        ĐƠN VỊ: Bên trong tính bằng PHÚT (Solomon time units).
        Output arrival/start/leave → format HH:MM.
        Output total_duration → giờ (để user dễ đọc).
        """
        route = best.route
        weights = self.user_prefs.interest_weights

        current_time = self.user_prefs.start_time_minutes  # Phút (VD: 8h → 480)
        items: list[ItineraryItem] = []
        total_cost = 0.0
        total_score = 0.0
        total_distance = 0.0

        for order, poi in enumerate(route):
            if order == 0:
                # Depot xuất phát — không có travel (điểm bắt đầu)
                items.append(ItineraryItem(
                    order=1,
                    id=poi.id,
                    name="Điểm xuất phát (Depot)",
                    category="depot",
                    travel_distance=None,
                    travel_time=None,
                    arrival=_format_time(current_time),
                    wait=0,
                    start=_format_time(current_time),
                    leave=_format_time(current_time),
                    cost=0.0,
                    score=0.0,
                ))
                continue

            # Tính khoảng cách và thời gian di chuyển (phút) từ điểm trước
            prev_poi = route[order - 1]
            travel = get_travel_time(prev_poi, poi)
            total_distance += travel
            travel_time_minutes = int(round(travel))

            arrival_raw = current_time + travel  # Thời điểm đến (phút)

            # Chờ nếu đến sớm hơn giờ mở cửa
            wait_minutes = 0
            if arrival_raw < poi.open_time:
                wait_minutes = int(round(poi.open_time - arrival_raw))
                arrival_effective = poi.open_time
            else:
                arrival_effective = arrival_raw

            start_service = arrival_effective
            leave_time = start_service + poi.duration
            current_time = leave_time

            # Tính điểm theo trọng số sở thích
            w = weights.get(poi.category, 0.0)
            score = poi.base_score * w

            if order == len(route) - 1:
                # Depot cuối (trở về)
                items.append(ItineraryItem(
                    order=order + 1,
                    id=poi.id,
                    name="Trở về (Depot)",
                    category="depot",
                    travel_distance=round(travel, 2),
                    travel_time=travel_time_minutes,
                    arrival=_format_time(arrival_raw),
                    wait=0,
                    start=None,
                    leave=None,
                    cost=0.0,
                    score=0.0,
                ))
            else:
                total_cost += poi.price
                total_score += score
                items.append(ItineraryItem(
                    order=order + 1,
                    id=poi.id,
                    name=f"POI-{poi.id} ({poi.category})",
                    category=poi.category,
                    travel_distance=round(travel, 2),
                    travel_time=travel_time_minutes,
                    arrival=_format_time(arrival_raw),
                    wait=wait_minutes,
                    start=_format_time(start_service),
                    leave=_format_time(leave_time),
                    cost=poi.price,
                    score=round(score, 2),
                ))

        # total_duration: phút → giờ (output cho user)
        total_duration_hours = (current_time - self.user_prefs.start_time_minutes) / 60.0

        return OptimizationResponse(
            total_score=round(total_score, 2),
            total_cost=round(total_cost, 2),
            total_distance=round(total_distance, 2),
            total_duration=round(total_duration_hours, 2),
            route=items,
            execution_time=round(execution_time, 4),
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  Main Loop — Early Stopping + Convergence Logging
    # ══════════════════════════════════════════════════════════════════════════
    def run(self) -> OptimizationResponse:
        """
        Chạy vòng lặp tiến hóa chính của Hybrid GA.

        ★ EARLY STOPPING ★
          Nếu best fitness không cải thiện (>= threshold) trong
          `stagnation_limit` thế hệ liên tiếp → dừng sớm.

        ★ CONVERGENCE LOGGING ★
          Lưu metrics mỗi thế hệ vào self.convergence_log để vẽ đồ thị.

        ★ ABLATION FLAGS ★
          Các toán tử có thể tắt/bật qua flags trong __init__.
        """
        start_time = time.perf_counter()

        self.initialize_population()
        best_ever = self.population[0]
        gens_without_improvement = 0
        actual_gens = 0

        for gen in range(self.generations):
            actual_gens = gen + 1


            duplicates_replaced = 0

            # ── Tạo con cái ──────────────────────────────────────────────
            children: list[Individual] = []
            while len(children) < self.population_size:
                p1, p2 = self.select_parents(self.population)
                child = self.crossover(p1, p2)
                child = self.mutate(child)
                child = self._repair(child)
                child = self._greedy_refill(child)  # ★ Lấp đầy route
                calculate_fitness(child, self.user_prefs, self.wait_penalty_weight)
                children.append(child)

            # ── Merged Replacement — giữ best từ (parents + children) ─────
            merged = list(self.population) + children
            merged.sort(key=lambda ind: ind.fitness, reverse=True)

            # Lấy top individuals, đồng thời đảm bảo diversity
            new_population: list[Individual] = []
            for ind in merged:
                if self.use_diversity_check and self._is_duplicate(ind, new_population):
                    duplicates_replaced += 1
                    continue
                new_population.append(ind)
                if len(new_population) >= self.population_size:
                    break

            # Nếu chưa đủ (do loại trùng), bổ sung random
            while len(new_population) < self.population_size:
                new_population.append(self._create_diverse_individual())
                duplicates_replaced += 1

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
            all_fitnesses = sorted([ind.fitness for ind in self.population], reverse=True)
            best_fit = all_fitnesses[0]
            avg_fit = sum(all_fitnesses) / len(all_fitnesses)
            median_fit = all_fitnesses[len(all_fitnesses) // 2]
            worst_fit = all_fitnesses[-1]

            # Đếm số lộ trình duy nhất (unique routes)
            unique_routes = len({
                frozenset(p.id for p in ind.route[1:-1])
                for ind in self.population
            })

            # ── Convergence Log (cho vẽ đồ thị) ─────────────────────────────
            self.convergence_log.append({
                "gen": gen + 1,
                "best_fitness": best_fit,
                "avg_fitness": avg_fit,
                "median_fitness": median_fit,
                "worst_fitness": worst_fit,
                "unique_routes": unique_routes,
                "wait_time": self.population[0].total_wait,
                "best_score": self.population[0].total_score,
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

        elapsed = time.perf_counter() - start_time

        # ── Store results ────────────────────────────────────────────────────
        self.actual_gens = actual_gens
        self.best_individual = best_ever

        print(f"\n[HGA] ═══ KẾT QUẢ CUỐI CÙNG ═══")
        print(f"      Generations run   = {actual_gens}/{self.generations}")
        print(f"      Best-ever fitness = {best_ever.fitness:.2f}")
        print(f"      Total wait time   = {best_ever.total_wait:.1f}")
        print(f"      Route IDs   : {[p.id for p in best_ever.route]}")
        print(f"      Route length: {len(best_ever.route)} nodes "
              f"({len(best_ever.route) - 2} POIs + 2 Depot)")
        print(f"      Execution time: {elapsed:.4f}s")

        return self._build_response(best_ever, elapsed)