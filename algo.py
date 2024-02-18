class DSU:
    def __init__(self, initial_ids):
        self.resolver = {_id: i for (i, _id) in enumerate(initial_ids)}
        self.resolver_i =  list(initial_ids)
        self.count = len(self.resolver)
        # if negative, then it's root and size of set
        self.parent = [-1] * self.count

    def _get_root(self, node):
        if self.parent[node] < 0:
            return node
        self.parent[node] = self._get_root(self.parent[node])
        return self.parent[node]

    def merge(self, id1, id2):
        n1 = self._get_root(self.resolver[id1])
        n2 = self._get_root(self.resolver[id2])
        if n1 == n2:
            return
        if (-n1) > (-n2):
            self.parent[n2] = n1
        else:
            self.parent[n1] = n2

    def summarize(self):
        groups = {}
        for i in range(self.count):
            r = self._get_root(i)
            if r not in groups:
                groups[r] = set()
            groups[r].add(self.resolver_i[i])
        return groups
