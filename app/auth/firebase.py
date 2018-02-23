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
        raise FirebaseTokenValidator.FirebaseIdTokenValidationExc()