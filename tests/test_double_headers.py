import hiro  # type: ignore
import pytest  # type: ignore
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.testclient import TestClient

from slowapi.util import get_ipaddr
from tests import TestSlowapi


def get_user_rate_limit() -> str:
    return "1/10 seconds"



def default_identifier(request: Request) -> str: #SNM
    """
    Returns a known api key contained in a request, else returns either client ip or local host
    :param request: [required] FastAPI request object
    :return str: the known api_key contained in a request, or client ip or local host
    """
    identifier = None
    try:
        identifier = request.state.user['client_id']
    except AttributeError as e:
        identifier = request.client.host or "127.0.0.1"

    return identifier


class TestHeaders(TestSlowapi):
    def test_double_header(self): #SNM

        app, limiter = self.build_fastapi_app(key_func=default_identifier,
                  headers_enabled=True,
                  in_memory_fallback_enabled=True,
                  swallow_errors=True)


        @app.get("/t1")
        @limiter.limit(get_user_rate_limit)
        async def t1(request: Request,
                        response: Response,
                          ):

            return PlainTextResponse("test")

        client = TestClient(app)
        response = client.get("/t1")
        assert response.status_code == 200

        # assert x_ratelimit_limit header is a single int
        x_ratelimit_limit = response.headers['x-ratelimit-limit']
        x_ratelimit_limit_arr = x_ratelimit_limit.split(',')
        assert len(x_ratelimit_limit_arr) >=1

        assert response.headers['x-ratelimit-limit']
        assert response.headers['x-ratelimit-remaining']
        assert response.headers['x-ratelimit-reset']

    def test_single_header(self): #SNM

        app, limiter = self.build_fastapi_app(key_func=default_identifier,
                  headers_enabled=True,
                  in_memory_fallback_enabled=True,
                  swallow_errors=True)


        @app.get("/t2")
        @limiter.limit("1/10 seconds")
        async def t2(request: Request,
                        response: Response,
                          ):

            return PlainTextResponse("test")

        client = TestClient(app)
        response = client.get("/t2")
        assert response.status_code == 200

        # assert x_ratelimit_limit header is a single int
        x_ratelimit_limit = response.headers['x-ratelimit-limit']
        x_ratelimit_limit_arr = x_ratelimit_limit.split(',')
        assert len(x_ratelimit_limit_arr) <=1

        # assert rate limit headers
        assert response.headers['x-ratelimit-limit']
        assert response.headers['x-ratelimit-remaining']
        assert response.headers['x-ratelimit-reset']