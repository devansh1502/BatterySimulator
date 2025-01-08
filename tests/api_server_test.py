from unittest.mock import patch

from src import api


def test_get_battery_exception():
    # Note: using app context fixes working outside app context and reqd by flask.
    # Mocking Session object to raise exception
    with patch("src.api.Session", MySession), api.app.app_context():
        resp, status_code = api.get_battery("/1")
        assert status_code == 500


def test_get_all_batteries_exception():
    with patch("src.api.Session", MySession), api.app.app_context():
        resp, status_code = api.get_all_batteries()
        assert status_code == 500


def test_create_battery_exception():
    with patch("src.api.Session", MySession), api.app.app_context():
        resp, status_code = api.create_battery()
        assert status_code == 500


def test_update_battery_exception():
    with patch("src.api.Session", MySession), api.app.app_context():
        with api.app.test_client() as client:
            response = client.patch(f"/update?battery_id=1&power=1&duration=60")
            assert response.status_code == 500


def test_delete_battery_exception():
    with patch("src.api.Session", MySession), api.app.app_context():
        resp, status_code = api.delete_battery("/1")
        assert status_code == 500


def test_get_soc_exception():
    with patch("src.api.Session", MySession), api.app.app_context():
        with api.app.test_client() as client:
            response = client.get("/soc")
            assert response.status_code == 500


def test_get_cycles_exception():
    with patch("src.api.Session", MySession), api.app.app_context():
        with api.app.test_client() as client:
            response = client.get("/cycles")
            assert response.status_code == 500


# Creating Empty Session and let it fail for exception
class MySession:
    def query(self, model):
        return self

    def filter_by(self, **kwargs):
        return self

    def all(self):
        raise Exception("Server error")

    def one_or_none(self):
        raise Exception("Server error")

    def rollback(self):
        return

    def close(self):
        return
