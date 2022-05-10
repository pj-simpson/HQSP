from configparser import ConfigParser
from typing import Any, Callable, Dict

import arrow
from auth.token_dealer import OAuthHandler, OAuthToken
from jinja2 import Environment, PackageLoader
from parse import parse
from webob import Request, Response
from whitenoise import WhiteNoise


class Application:

    """
    A HQ Server Pages Application

    Attributes
    -----------

    routes:
        A mapping between a path and a function. Initialized as empty.

    templates_env:
        The template environment from the Jinja package. This stores the config and loads the
        templates from the appropriate file system location, which will always be a 'templates' folder
        relative to the application's working directory.


    Methods
    -------
    add_routes
        Iterates over a dictionary's items, which we expect to be a mapping of path to function,
        adding them to the routes dictionary. Checks for duplicates.

    default_404_response
        Produces a 404 not found web response.

    find_handler
        Takes a look a the request path and attempts to match it against the paths stored in the routes.
        uses parse to determine whether or not there are any path parameters and extracts those, returning them to be
        used as keyword arguments for the handler.

    handle_request
    """

    def __init__(self):
        """
        Initialises a HQSP Application object with:
            - an empty routes Dictionary.
            - an instance of the WhiteNoise, wrapping the WSGI response of the application.
                The root folder of the static resources is a folder below the working directory called 'static'
            - gets a ConfigParser and reads from a settings.ini file in the same directory as the application file.
            - sets an initial OAuth token, as read by the ConfigParser from the settings.ini file.
            - sets a base url for any http calls, as read by the ConfigParser from the settings.ini file.
            - sets a Template Environment for Jinja templating engine.Templates are loaded from a 'templates' directory
                relative to the application file
        """
        self.routes = {}
        self.whitenoise = WhiteNoise(self.wsgi_response, root="static")

        config = ConfigParser()
        config.read("settings.ini")

        self.initial_token = OAuthToken(
            access_token=config.get("AUTH", "access_token"),
            access_expiry=config.getint("AUTH", "access_expiry"),
            refresh_token=config.get("AUTH", "refresh_token"),
            refresh_expiry=config.getint("AUTH", "refresh_expiry"),
            token_type=config.get("AUTH", "token_type"),
            user=config.get("AUTH", "user"),
            generation_time=arrow.utcnow(),
        )

        self.base_url = config.get("INSTANCE", "host")

        self.templates_env = Environment(
            loader=PackageLoader(config.get("APP", "name"))
        )

    def add_routes(self, mappings: Dict[str, Callable]) -> None:
        """

        :param mappings: Dictonary mapping between a route and a handler function
        :return: None

        Iterates over the key, value pairs in the Dict and if the path is not already in use by the Application,
            the mapping is added to the Applications 'routes' store.
        """
        for path, handler in mappings.items():
            assert path not in self.routes, "Attempting to add duplicate route"
            self.routes[path] = handler

    def wsgi_response(self, environ: Dict, start_response: Callable) -> Response:
        """

        :param environ: Dict of environment variables relevant to the http req
        :param start_response: Callback function accepting status and headers
        :return: WSGI compatible HTTP response object

        Passes the incoming request to the Application's handle_request method and then returns a WSGI Response
        """
        request = Request(environ)
        response = self.handle_request(request)
        return response(environ, start_response)

    def __call__(self, environ: Dict, start_response: Callable) -> Response:
        """

        :param environ: Dict of environment variables relevant to the http req
        :param start_response: Callback function accepting status and headers
        :return: WSGI compatible HTTP response object

        Provides an interface so that the Application object can be called like a function.
        """
        return self.whitenoise(environ, start_response)

    def default_404_response(self, response: Response) -> None:
        """

        :param response: a WSGI Response Object
        :return: None

        Sets a default 404 fallback for when a request cannot be properly handled
        """
        response.status_code = 404
        response.text = "Not found."

    def find_handler(self, request_path: str) -> Any:
        """

        :param request_path: str path from an http request
        :return: Either a tuple of handler function and the parsed request path or a Tuple of None responses.

        Iterates over the key,value mappings from the Application's routes and attempts to parse the path from
        the http request against the path stored in the routes. If there is a parse result object, the handler function
        for the given route is returned, along with the kwargs via the parameter(s) contained in the path.

        NB: 'parse is the opposite of format' / reverse string interpolation.
            We have some known values and we want to check them against paths which may or may not include path parameters
            if the patterns match, we pair the parameters with their values as a dict.

        """
        for path, handler in self.routes.items():
            parse_result = parse(path, request_path)
            if parse_result is not None:
                return handler, parse_result.named

        return None, None

    def handle_request(self, request: Request) -> Response:

        """

        :param request: an Http Request Object
        :return: a WSGI Response Object.

        Fetches the appropriate handler function for the incoming request and executes it, returning
            a WSGI compatible response.
        """

        response = Response()
        handler, kwargs = self.find_handler(request_path=request.path)
        if handler is not None:
            handler(request, response, **kwargs)
        else:
            self.default_404_response(response)
        return response

    def template(self, template_name: str, context: Dict = None) -> bytes:
        """

        :param template_name: str
        :param context: Dict of values to be formatted into the template
        :return: str

        Fetches the correct template, based on template name and renders it as a string,
        having passed in any variables.

        """
        if context is None:
            context = {}
        return (
            self.templates_env.get_template(template_name)
            .render(**context)
            .encode("utf-8")
        )

    def set_headers(self, function: Callable):
        """
        Decorator to provide a dictionary of headers so that the wrapped function
        can easily construct http requests to the external system. Utilizes the frameworks
        OAuthHandler to obtain a valid OAuth token.

        """

        def wrap_function(*args, **kwargs):
            oauth_handler = OAuthHandler(
                "../../demo/database", self.initial_token, self.base_url
            )
            token = oauth_handler.get_token()
            base_url = self.base_url
            headers = {
                "Authorization": f"Bearer {token.access_token}",
                "Accept": "application/json",
            }
            return function(headers, base_url, *args, **kwargs)

        return wrap_function
