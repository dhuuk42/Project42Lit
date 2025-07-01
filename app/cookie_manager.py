import streamlit.components.v1 as components


def get_cookie(name: str):
    """Return cookie value or None."""
    cookie = components.html(
        f"""
        <script>
        const value = '; ' + document.cookie;
        const parts = value.split('; {name}=');
        if (parts.length === 2) {{
            const cookie = parts.pop().split(';').shift();
            Streamlit.setComponentValue(cookie);
        }} else {{
            Streamlit.setComponentValue(null);
        }}
        </script>
        """,
        height=0,
    )
    return cookie


def set_cookie(name: str, value: str, days: int = 30):
    """Set cookie via JavaScript."""
    components.html(
        f"""
        <script>
        const d = new Date();
        d.setTime(d.getTime() + ({days}*24*60*60*1000));
        document.cookie = '{name}=' + '{value}' + '; expires=' + d.toUTCString() + '; path=/; SameSite=Lax';
        </script>
        """,
        height=0,
    )


def delete_cookie(name: str):
    """Delete a cookie."""
    components.html(
        f"""
        <script>
        document.cookie = '{name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
        </script>
        """,
        height=0,
    )
