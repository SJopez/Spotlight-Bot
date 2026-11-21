from db import DataBase
import numpy as np

def build_matrix(count, replies):
    dim = min(count, 100)
    taken = {}
    matrix = [[0] * dim for _ in range(dim)]

    for rel in replies:
        user_from, user_to, ans = rel[1], rel[2], rel[3]
        
        i = taken.get(user_from, None)
        j = taken.get(user_to, None)

        need = (i is None) + (j is None)

        if len(taken) + need > dim:
            continue

        if i is None:
            i = len(taken)
            taken[user_from] = i

        if j is None:
            j = len(taken)
            taken[user_to] = j

        matrix[i][j] = ans
        
    return matrix, taken

def get_scores(ranking):
    total = sum(authority for _, authority, _ in ranking)
    return [(user_id, authority / total * 100) for user_id, authority, _ in ranking]

def get_list(database: DataBase, chat):
    count = database.count_users(chat)
    replies = database.get_replies(chat)

    matrix, taken = build_matrix(count, replies)
    matrix = np.array(matrix, dtype=float) ** 0.5
    U, S, Vt = np.linalg.svd(matrix)

    hub = U[:, 0]
    authority = Vt[0]

    if authority.sum() < 0:
        authority = -authority
    if hub.sum() < 0:
        hub = -hub
    
    ranking = [(user_id, authority[idx], hub[idx]) for user_id, idx in taken.items()]
    ranking.sort(key=lambda x: x[1], reverse=True)

    return ranking

