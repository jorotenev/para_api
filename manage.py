#!/usr/bin/env python
import os
import click
import sys

from app import create_app

try:
    app_mode = os.environ['APP_STAGE']
    print("Environment from env vars: " + app_mode)
except KeyError:
    print("Set the APP_STAGE environmental variable: 'development', 'testing', 'staging', 'production")
    exit(1)

port = os.getenv('PORT', 5000)

app = create_app(app_mode)


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage.')
def test(coverage):
    """Run the unit tests."""
    with app.app_context():
        from flask import current_app as c
        print('OPAAA' + c.config['APP_STAGE'])


        import unittest
        tests = unittest.TestLoader().discover('tests')
        result = unittest.TextTestRunner(verbosity=2).run(tests)
        sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
