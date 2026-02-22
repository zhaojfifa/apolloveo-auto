def test_app_import_smoke():
    from gateway.app.main import app

    assert app is not None
