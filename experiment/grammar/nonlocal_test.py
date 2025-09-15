def create_counter(start=0):
    count = start
    def counter():
        nonlocal count
        count += 1
        return count
    return counter


class Task:
    def __init__(self, a):
        self.a = a

    def find(self):
        return self.a

def test_counter():
    c1 = create_counter()
    assert c1() == 1
    assert c1() == 2
    c2 = create_counter(10)
    assert c2() == 11
    assert c2() == 12
    assert c1() == 3


def test_find():
    task = Task(1)
    print(task.find() + 100)
    assert task.find() == 1



