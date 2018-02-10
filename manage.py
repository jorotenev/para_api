#!/usr/bin/env python
import os
from app import create_app

try:
    app_mode = os.environ['APP_MODE']
except KeyError:
    print("Set the APP_MODE environmental variable: 'development', 'testing', 'staging', 'production")
    exit(1)

print("Environment from env vars: " + app_mode)



port = os.getenv('PORT', 5000)

app = create_app(app_mode)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
