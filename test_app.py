# test_app.py
from app import greet


def test_greet():
    assert greet("Jenkins") == "Hello, Jenkins from Jenkins CI!"
    assert greet("World") != "Goodbye, World"  # A simple negative test
