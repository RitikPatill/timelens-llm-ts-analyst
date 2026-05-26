def test_package_importable():
    import timelens
    assert timelens.__version__ == "0.1.0"
