import json
from flask import current_app
from firebase_admin.credentials import Certificate
from firebase_admin.auth import verify_id_token
from firebase_admin import initialize_app as initialize_firebase_app
from base64 import b64decode
from config import EnvironmentName

firebase_app = None


def init_firebase(flask_app):
    """
    https://firebase.google.com/docs/admin/setup
    """
    global firebase_app
    conf = flask_app.config.get("FIREBASE_CONFIG_JSON", "")
    conf = b64decode(conf).decode()
    conf_json = json.loads(conf)

    conf_json['private_key'] = conf_json['private_key'].replace("\\n", '\n')
    credentials = Certificate(conf_json)

    firebase_app = initialize_firebase_app(credential=credentials)


class FirebaseTokenValidator(object):
    """
    exposes functionality to verify that a given string is indeed a firebase
    auth token and then extract the firebase user uid out of the token.

    https://firebase.google.com/docs/auth/admin/verify-id-tokens#retrieve_id_tokens_on_clients
    """

    class FirebaseIdTokenValidationExc(Exception):
        pass

    @staticmethod
    def validate_id_token_and_get_uid(id_token):
        """
        :param id_token [str]:
        :return: firebase uid : [str]

        :raises FirebaseIdTokenValidationExc if the `id_token` paramater is not a valid firebase id token
        """

        if current_app.config['APP_STAGE'] not in [EnvironmentName.production, EnvironmentName.staging] and \
                current_app.config.get("SHORT_CIRCUIT_FIREBASE", False):
            # must never happen in production/staging
            print('[FIREBASE] validation and extraction short-circuited')
            return id_token
        try:
            # https://firebase.google.com/docs/auth/admin/verify-id-tokens
            user = verify_id_token(id_token)
            return user['uid']
        except ValueError as err:
            raise FirebaseTokenValidator.FirebaseIdTokenValidationExc()
