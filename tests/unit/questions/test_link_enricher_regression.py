from questions import link_enricher


class ImmediateFuture:
    def __init__(self, response):
        self.response = response

    def result(self):
        return self.response


class Response:
    status_code = 404
    headers = {}


def test_schemeless_url_is_normalized_before_fetch(monkeypatch, capsys):
    requested_urls = []

    def fake_cached_request_get(url):
        requested_urls.append(url)
        return ImmediateFuture(Response())

    monkeypatch.setattr(link_enricher, "cached_request_get", fake_cached_request_get)

    titles = link_enricher.get_titles_from_urls(frozenset({"ub.com/lee101/cutellm"}))

    assert titles == [None]
    assert requested_urls == ["https://ub.com/lee101/cutellm"]
    assert "Traceback" not in capsys.readouterr().err


def test_http_url_is_fetched_unchanged(monkeypatch):
    requested_urls = []

    def fake_cached_request_get(url):
        requested_urls.append(url)
        return ImmediateFuture(Response())

    monkeypatch.setattr(link_enricher, "cached_request_get", fake_cached_request_get)

    link_enricher.get_titles_from_urls(frozenset({"http://example.com/page"}))

    assert requested_urls == ["http://example.com/page"]


def test_missing_content_type_header_does_not_raise(monkeypatch):
    def fake_cached_request_get(url):
        return ImmediateFuture(Response())

    monkeypatch.setattr(link_enricher, "cached_request_get", fake_cached_request_get)

    assert link_enricher.get_titles_from_urls(frozenset({"https://example.com/no-header"})) == [None]
