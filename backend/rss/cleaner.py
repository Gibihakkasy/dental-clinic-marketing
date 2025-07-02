from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def clean_knowyourteeth_link(link: str) -> str:
    """
    Clean knowyourteeth.com links by preserving only relevant parameters.
    
    Args:
        link: The URL to clean
        
    Returns:
        Cleaned URL with only relevant parameters preserved
    """
    parsed = urlparse(link)
    if "knowyourteeth.com" in parsed.netloc:
        query = parse_qs(parsed.query)
        cleaned = {}
        # Preserve relevant parameters if present
        for key in ("abc", "iid", "aid"):
            if key in query:
                cleaned[key] = query[key][0]
        new_query = urlencode(cleaned)
        return urlunparse((
            "https",
            "knowyourteeth.com",
            parsed.path,
            "",
            new_query,
            ""
        ))
    return link 