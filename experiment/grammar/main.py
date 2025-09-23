def foo(a, b, c, d):
    print(a, b, c, d)


if __name__ == '__main__':
    foo.__defaults__ = (1, 2)
    foo(10, 9, 8)
