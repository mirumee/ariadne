def escape_default_query(query: str, js_sign: str = "'") -> str:
    while "\\" + js_sign in query:
        query = query.replace("\\" + js_sign, js_sign)
    while "\\n" in query:
        query = query.replace("\\n", "\n")
    while "\\\n" in query:
        query = query.replace("\\\n", "\n")
    return query.replace("\n", "\\n").replace(js_sign, "\\" + js_sign)
