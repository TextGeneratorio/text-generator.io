from requests_futures.sessions import FuturesSession

session = FuturesSession(max_workers=10)


def request_get(url):
    return session.get(url, timeout=480)
