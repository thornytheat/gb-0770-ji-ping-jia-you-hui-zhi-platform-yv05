import pytest
from app.bundles import sample_set
from app.main import create_app
from app.shift import compute


@pytest.fixture
def ramp(tmp_path):
    return create_app(tmp_path/'fuel.sqlite')


@pytest.fixture
def client(ramp):
    return ramp.test_client()


@pytest.fixture(scope='session')
def dirty():
    return compute(sample_set('dirty'))
