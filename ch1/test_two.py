import pytest

def test_failing():
    assert (1, 2, 3) == (3, 2, 1)



@pytest.fixture(name='a')
def sample_a():
    return 1

class TestA:

    def test_add(self, a):
        assert 2 + a == 1 + 2