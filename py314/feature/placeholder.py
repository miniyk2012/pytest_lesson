from functools import Placeholder, partial


if __name__ == '__main__':
    insert_front = partial(list.insert, Placeholder, 0)
    lst = [1, 2, 3]
    insert_front(lst, 5)
    print(lst)