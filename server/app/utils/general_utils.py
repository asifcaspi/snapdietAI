def clean_results(results):
    cleaned = []
    for r in results:
        s = r

        # 1. if it starts with "and ", strip that off
        if s.startswith("and "):
            s = s[len("and ") :]

        # 2. drop leading chars until the first is a–z
        while s and not ("a" <= s[0] <= "z"):
            s = s[1:]

        # 3. if non-empty, keep it
        if s:
            cleaned.append(s)

    return cleaned


def merge_objects(captions):
    seen = set()
    merged = []
    for cap in captions:
        # split on commas, strip whitespace, ignore empty pieces
        items = [item.strip().lower() for item in cap.split(",") if item.strip()]
        for food in items:
            if food not in seen:
                seen.add(food)
                merged.append(food)
    return merged
