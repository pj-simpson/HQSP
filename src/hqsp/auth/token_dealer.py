from dataclasses import dataclass

import arrow
import requests

from src.hqsp.auth.storage import SingletonPickler


@dataclass
class OAuthToken:
    access_token: str
    access_expiry: int
    refresh_token: str
    refresh_expiry: int
    token_type: str
    user: str
    generation_time: arrow.Arrow


class OAuthHandler:
    """

    An object to provide the main application with valid OAuth tokens. The OAuthHandler class takes care of the token
    lifecycle, including checking validity, refreshing and storing tokens along with their metadata.
    A SingletonPickler object is used for storage.


    Attributes
    -----------

    storage:
        A instance of a SingletonPickler, for pickling and unpickling OAuthTokens.

    Methods
    -------
    get_token:
        Obtains a token from the storage. Checks whether or not the token has expired. If it hasnt, it returns the
        token. If the token needs refreshing, the OAuthHandler makes the nessecary refresh calls before storing and
        returning a new token.
    """

    def __init__(self, filename: str, seed: OAuthToken, base_url: str):
        """

        :param filename: str
        :param seed: OAuthToken dataclass
        :param

        Upon initializing the OAuthHandler, it's storage is also created and seeded with an initial value.
        """
        self.storage = SingletonPickler(filename, seed)
        self.base_url = base_url

    def _check_access_valid(self, token: OAuthToken) -> bool:
        """

        :param token: OAuthToken
        :return: bool

        Checks whether a token is valid to be used in an http call, by checking if the time 'now' is
            after the time it was created PLUS its expiry (which is counted in seconds).
        """

        expiry = token.generation_time.shift(seconds=token.access_expiry)
        return expiry > arrow.utcnow()

    def _refresh_token(self, token: OAuthToken) -> OAuthToken:
        """

        :param token: OAuthToken
        :return: OAuthToken

        makes the refresh token call to the third party servers
        """
        url = f"https://{self.base_url}/rest/auth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = f"refresh_token={token.refresh_token}"

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            response_body = response.json()
            new_token = OAuthToken(
                response_body["access_token"],
                int(response_body["expires_in"]),
                response_body["refresh_token"],
                int(response_body["refresh_token_expires_in"]),
                response_body["token_type"],
                response_body["useremail"],
                arrow.utcnow(),
            )

            self.storage.create_pickled_file_with_new_object(new_token)
            return new_token

        return token

    def get_token(self) -> OAuthToken:
        """
        :return: OAuthToken

        Fetches a valid token which can be used in an http call to the external service

        """
        token = self.storage.unpickle_object_from_database()
        if self._check_access_valid(token):
            return token
        else:
            return self._refresh_token(token)
