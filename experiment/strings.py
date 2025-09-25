from functools import partial


def foo():
    lst = []
    insert_front = partial(list.insert, lst, 0)
    insert_front(5)
    print(lst)

if __name__ == '__main__':
    foo()