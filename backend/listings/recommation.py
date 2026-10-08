import math
import random
from collections import defaultdict
from typing import Dict, Iterable, List, Set

from django.db.models import QuerySet

from .models import Favorite, House

def _build_user_house_matrix() -> Dict[int, Set[int]]:
    """构建用户-房源交互矩阵."""
    matrix: Dict[int, Set[int]] = defaultdict(set)
    for item in Favorite.objects.values('user_id', 'house_id'):
        matrix[item['user_id']].add(item['house_id'])
    return matrix

def _compute_similar_users(
    target_user_id: int,
    matrix: Dict[int, Set[int]],
    k_sim_user: int,
) -> List[tuple[int, float]]:
    """计算与目标用户相似的用户列表."""
    target_items = matrix.get(target_user_id)
    if not target_items:
        return []

    scores: List[tuple[int, float]] = []
    target_len = len(target_items)
    if target_len == 0:
        return []

    for other_user_id, items in matrix.items():
        if other_user_id == target_user_id:
            continue
        inter_size = len(target_items & items)
        if inter_size == 0:
            continue
        score = inter_size / math.sqrt(target_len * len(items))
        if score > 0:
            scores.append((other_user_id, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:k_sim_user]

def _rank_candidate_houses(
    similar_users: Iterable[tuple[int, float]],
    matrix: Dict[int, Set[int]],
    target_items: Set[int],
) -> List[tuple[int, float]]:
    """根据相似用户累计房源得分."""
    rank: Dict[int, float] = {}
    for other_user_id, score in similar_users:
        for house_id in matrix.get(other_user_id, set()):
            if house_id in target_items:
                continue
            rank[house_id] = rank.get(house_id, 0.0) + score
    ranked_items = sorted(rank.items(), key=lambda x: x[1], reverse=True)
    return ranked_items

def _fetch_houses_by_ids(house_ids: Iterable[int]) -> Dict[int, House]:
    qs: QuerySet[House] = House.objects.filter(id__in=list(house_ids))
    return {house.id: house for house in qs}

def _random_houses(exclude_ids: Set[int], count: int) -> list[House]:
    if count <= 0:
        return []
    available_ids = list(
        House.objects.exclude(id__in=exclude_ids).values_list('id', flat=True)
    )
    if not available_ids:
        return []
    if len(available_ids) <= count:
        sample_ids = available_ids
    else:
        sample_ids = random.sample(available_ids, count)
    house_map = _fetch_houses_by_ids(sample_ids)
    # 保持与抽样顺序一致
    return [house_map[i] for i in sample_ids if i in house_map]

def get_user_recommendations(
    user_id: int,
    *,
    k_sim_user: int = 5,
    max_candidates: int = 20,
    min_count: int = 4,
    max_count: int = 0,
) -> List[dict]:
    """获取指定用户的房源推荐结果."""
    matrix = _build_user_house_matrix()
    target_items = matrix.get(user_id, set())

    similar_users = _compute_similar_users(user_id, matrix, k_sim_user)
    ranked_candidates = _rank_candidate_houses(similar_users, matrix, target_items)

    candidate_ids = [item[0] for item in ranked_candidates[:max_candidates]]
    candidate_scores = {item[0]: item[1] for item in ranked_candidates[:max_candidates]}
    house_map = _fetch_houses_by_ids(candidate_ids)

    results: List[dict] = []
    for hid in candidate_ids:
        house = house_map.get(hid)
        if not house:
            continue
        results.append(
            {
                'house': house,
                'score': round(candidate_scores.get(hid, 0.0), 4),
                'source': 'collaborative',
            }
        )

    desired_total = None
    if len(results) < min_count:
        # 保证 randint 的参数范围有效：当调用者未提供合适的 max_count 时，使用至少 min_count
        hi = max(max_count, min_count)
        desired_total = random.randint(min_count, hi)

    existing_ids = {item['house'].id for item in results}
    existing_ids.update(target_items)

    if desired_total is not None:
        need_fill = max(desired_total - len(results), 0)
        random_houses = _random_houses(existing_ids, need_fill)
        for house in random_houses:
            results.append(
                {
                    'house': house,
                    'score': None,
                    'source': 'random_fill',
                }
            )

    # 如果协同过滤没有任何结果且也没有随机补充（例如房源不足），仍返回已有结果
    return results