[![CircleCI](https://circleci.com/gh/jorotenev/para_api.svg?style=svg&circle-token=87228e3b9fad968994016a48fda0eb636bfc6491)](https://circleci.com/gh/jorotenev/para_api)
The backend for the [para mobile app](https://github.com/jorotenev/para)
## Run
* Install [pipenv](https://github.com/pypa/pipenv#installation)
* `$ pipenv install`
* `$ pipenv shell`
* make an `.env_dev` file at the root of the repo with the following structure
```
APP_STAGE=development
SECRET_KEY=not-that-secret
SHORT_CIRCUIT_FIREBASE=0 # see the Note below
FIREBASE_CONFIG_JSON_BASE64=<firebase admin sdk config, base64-ed> # see the note below
ROLLBAR_CLIENT_TOKEN=<rollbar client token here> # required only for staging and production APP_STAGE
```
* Set the following environmental variables
```
DOT_ENV_FILE=.env_dev
FLASK_APP=manage.py # the "new" way flask discovers apps
FLASK_DEBUG=0 # otherwise python signals don't work
```
* To run the API (see below the Note for PyCharm users)  
`$ flask run --host=0.0.0.0`

#### Note on FIREBASE_CONFIG_JSON_BASE64:
Client of this API authenticate by sending the `x-firebase-auth-token` header.
The header's content is a [firebase id token](https://firebase.google.com/docs/auth/admin/verify-id-tokens#retrieve_id_tokens_on_clients), generated client-side (by a firebase client sdk).

The `app.auth.FirebaseTokenValidator.validate_id_token_and_get_uid()` is called on each request to protected routes and
uses the header to extract the `user uid` from the `id token`. This way it's ensured that the request comes from an authenticated user of the correct firebase app.

##### Normal usage
To set the value of `FIREBASE_CONFIG_JSON_BASE64`, you need to get the [admin sdk credentials file](https://firebase.google.com/docs/admin/setup) of a valid Firebase project.
It should be the same Firease project, used for the [para mobile app](https://github.com/jorotenev/para), if the instance
of the API will configured as the backend of a para mobile app.
[base64](https://base64encode.org) the contents of the credentials file and use the
result as a value for the environmental variable.
This way, this API can decode [id tokens](https://firebase.google.com/docs/auth/admin/verify-id-tokens#retrieve_id_tokens_on_clients)
sent from the mobile app

##### Alternatively
During the development of the api or if you don't want to create Firebase project, it can be handy to skip the process of extraction of a firebase user uid from an id token and just send an user uid directly.
I.e., setting `FIREBASE_CONFIG_JSON_BASE64` can be omitted if:
 * the `SHORT_CIRCUIT_FIREBASE` is set to `'1'`
 * the `APP_STAGE` is `development` / `testing`
 * the `x-firebase-auth-token` header contains a valid firebase `user uid` (and **not** a firebase `id token`).

This way Firebase user uid extraction is "short-circuited" in the sense that the contents of the `x-firebase-auth-token` header won't be treated as a
id token and validate_id_token_and_get_uid() will be
effectively be the identity function. Thus, when short-circuited, the header can contain just an user uid.

#### Note for PyCharm users
When running via PyCharm and assuming that pipenv is used, you need to select the correct python interpreter.
```
$ pipenv shell
(para_api-tKuPD0ya) $ which python
/home/georgi/.local/share/virtualenvs/para_api-tKuPD0ya/bin/python
```


## Test
`unittest` is used for the tests.
To run them via PyCharm
* You need the '.env_test' file placed in the repo root with
```
APP_STAGE=testing
SECRET_KEY=not-that-secret
DB_PING_LAZY=True
```
* Create a new Python test run configuration with the `/tests` as the __Path__ target and the root of the repo as a working directory
* Run the configuration

## Misc
__How to generate a valid firebase id token without using the para mobile app__
* Use the [firebase-sample](https://github.com/firebase/quickstart-js), set up a firebase project (`firebase use`).
* `$ cd auth && firebase serve`
* use the server webpage to login - the returned object has `accessToken`, which can be used as the value of
the `x-firebase-auth-token` header when making requests to the `para_api` from curl/postman/etc.
