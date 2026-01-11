import collections
from typing import List


def areSentencesSimilarTwo(words1: List[str], words2: List[str], pairs: List[List[str]]) -> bool:
    if len(words1) != len(words2): return False
    similars = collections.defaultdict(set)
    for w1, w2 in pairs:
        similars[w1].add(w2)
        similars[w2].add(w1)

    def dfs(words1, words2, visited):
        for similar in similars[words2]:
            if similar in visited: continue
            if words1 == similar:
                return True
            else:
                visited.add(similar)
                if dfs(words1, similar, visited):
                    return True
        return False

    for w1, w2 in zip(words1, words2):
        connected = dfs(w1, w2, {w2})
        if w1 != w2 and not connected:
            return False
    return True


if __name__ == '__main__':
    words1 = ["GET"]
    words2 = ["GET"]
    pairs = [["GET", "GET"]]
    v = areSentencesSimilarTwo(words1, words2, pairs)
    assert v is True
