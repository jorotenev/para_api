#!/usr/bin/env python
import os
import click
import sys

from os.path import dirname, join

from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env_dev')  # will fail silently if file is missing
load_dotenv(dotenv_path, verbose=True)

from app import create_app
from config import EnvironmentName

try:
    app_mode = os.environ['APP_STAGE']

except KeyError:
    print("Set the APP_STAGE environmental variable: %s" % ",".join(EnvironmentName.all_names()))
    exit(1)

app = create_app(app_mode)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config['PORT'])
