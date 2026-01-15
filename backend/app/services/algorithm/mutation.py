# Kỹ thuật Hybrid Local Search (2-opt).

from .fitness import calculate_fitness
import copy

def apply_smart_mutation(ind, user_prefs):
    best_fitness = ind.fitness
    improved = False

    # Thử đảo ngược các đoạn con (2-opt)
    # Bỏ qua điểm đầu (Depot) nếu cần cố định
    n = len(ind.route)
    if n < 4: return ind # Quá ngắn không cần đảo

    for i in range(1, n - 2):
        for j in range(i + 1, n):
            # Clone route để thử nghiệm
            new_route = ind.route[:]
            # Đảo ngược đoạn từ i đến j
            new_route[i:j] = new_route[i:j][::-1]

            # Tính fitness mới
            new_ind = copy.deepcopy(ind)
            new_ind.route = new_route
            new_fit = calculate_fitness(new_ind, user_prefs)

            if new_fit > best_fitness:
                ind.route = new_route
                ind.fitness = new_fit
                improved = True
                break # First improvement
        if improved: break

    return ind