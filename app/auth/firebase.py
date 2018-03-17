import json
import warnings

from flask import current_app
from firebase_admin.credentials import Certificate
from firebase_admin.auth import verify_id_token
from firebase_admin import initialize_app as initialize_firebase_app
from base64 import b64decode
from config import EnvironmentName

firebase_app = None


def can_short_circuit_firebase(app=current_app):
    """
    short circuit means that the FirebaseTokenValidator.validate_id_token_and_get_uid(token) will act as the identity function.
    Useful when locally testing the api and want to avoid generating proper firebase id tokens.
    :param app: flask app object
    :return: bool
    """
    if app.config["FIREBASE_CONFIG_JSON_BASE64"] and app.config['SHORT_CIRCUIT_FIREBASE']:
        warnings.warn(
            "If both FIREBASE_CONFIG_JSON_BASE64 and SHORT_CIRCUIT_FIREBASE are set, SHORT_CIRCUIT_FIREBASE is ignored")
    return (not app.config['FIREBASE_CONFIG_JSON_BASE64']) \
           and app.config['APP_STAGE'] not in [EnvironmentName.production, EnvironmentName.staging] \
           and app.config.get("SHORT_CIRCUIT_FIREBASE", False)


def init_firebase(flask_app):
    """
    https://firebase.google.com/docs/admin/setup
    """

    global firebase_app
    firebase_config_env_var_name = "FIREBASE_CONFIG_JSON_BASE64"
    firebase_config = flask_app.config.get(firebase_config_env_var_name, "")

    if can_short_circuit_firebase(app=flask_app):
        warnings.warn(
            "WARNING: Firebase Admin SDK has not been initialised. Using the identity function to extract the id token")
        FirebaseTokenValidator.validate_id_token_and_get_uid = id  # monkey patch as the identity function
        return

    if not can_short_circuit_firebase(flask_app) and not firebase_config:
        raise Exception("%s is required" % firebase_config_env_var_name)

    conf = flask_app.config.get(firebase_config_env_var_name, "")
    conf = b64decode(conf).decode()
    conf_json = json.loads(conf)

    conf_json['private_key'] = conf_json['private_key'].replace("\\n", '\n')
    credentials = Certificate(conf_json)

    firebase_app = initialize_firebase_app(credential=credentials)


class FirebaseTokenValidator(object):
    class FirebaseIdTokenValidationExc(Exception):
        pass

    @staticmethod
    def validate_id_token_and_get_uid(id_token):
        """
        verify that a given string is indeed a firebase auth token and then extract the
        firebase user uid out of the token.
        https://firebase.google.com/docs/auth/admin/verify-id-tokens
        https://firebase.google.com/docs/auth/admin/verify-id-tokens#retrieve_id_tokens_on_clients

        :param id_token [str]:
        :return: firebase uid : [str]
        :raises FirebaseIdTokenValidationExc if the `id_token` paramater is not a valid firebase id token
        """
        try:
            user = verify_id_token(id_token)
            return user['uid']
        except ValueError as err:
            current_app.logger.error(str(err))
            raise FirebaseTokenValidator.FirebaseIdTokenValidationExc()
