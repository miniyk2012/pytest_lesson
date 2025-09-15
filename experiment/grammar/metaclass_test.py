class UpperAttrMetaclass(type):
    # __new__ is the method called before __init__
    # it's the method that creates the object and returns it
    # while __init__ just initializes the object passed as parameter
    # you rarely use __new__, except when you want to control how the object
    # is created.
    # here the created object is the class, and we want to customize it
    # so we override __new__
    # you can do some stuff in __init__ too if you wish
    # some advanced use involves overriding __call__ as well, but we won't
    # see this
    def __new__(
            upperattr_metaclass,
            future_class_name,
            future_class_parents,
            future_class_attrs
    ):
        uppercase_attrs = {
            attr if attr.startswith("__") else attr.upper(): v
            for attr, v in future_class_attrs.items()
        }
        return type(future_class_name, future_class_parents, uppercase_attrs)


class Foo(metaclass=UpperAttrMetaclass):
    # but we can define metaclass here instead to affect only this class
    # and this will work with "object" children
    bar = 'bip'


def test_upper():
    assert Foo.BAR == 'bip'
