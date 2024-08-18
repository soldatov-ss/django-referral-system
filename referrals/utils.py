from typing import Any, Dict
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs


def append_query_params(url: str, params: Dict[str, Any]) -> str:
    """
    Appends query parameters to a given URL.

    Args:
        url (str): The base URL to which query parameters will be added.
        params (Dict[str, Any]): A dictionary of query parameters to add to the URL.

    Returns:
        str: The modified URL with the new query parameters appended.
    """
    url_parts = list(urlparse(url))
    query = dict(parse_qs(url_parts[4]))
    for key, value in params.items():
        if key in query:
            if isinstance(query[key], list):
                query[key].extend([value] if not isinstance(value, list) else value)
            else:
                query[key] = [query[key]] + ([value] if not isinstance(value, list) else value)
        else:
            query[key] = [value] if not isinstance(value, list) else value

    url_parts[4] = urlencode(query, doseq=True)
    return urlunparse(url_parts)
