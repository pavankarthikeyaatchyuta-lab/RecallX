import re


def generate_match_explanation(
    query: str,
    extracted_text: str,
    window_title: str,
    app_name: str,
    semantic_score: float,
    keyword_score: float,
) -> tuple[str, str]:
    """
    Generates deterministic, evidence-grounded explanation and snippet without cloud LLMs.
    Returns:
        (explanation_text, relevant_snippet)
    """
    query_tokens = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    all_content = f"{window_title} {extracted_text}"
    content_lower = all_content.lower()

    # Find exact matching tokens and phrases
    matched_words: list[str] = []
    for tok in query_tokens:
        if tok in content_lower and tok not in matched_words:
            matched_words.append(tok)

    # Extract best snippet around the first matched word
    snippet = ""
    lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
    if lines:
        best_line = lines[0]
        max_overlap = -1
        for line in lines:
            line_lower = line.lower()
            overlap = sum(1 for w in query_tokens if w in line_lower)
            if overlap > max_overlap:
                max_overlap = overlap
                best_line = line
        snippet = best_line
        if len(snippet) > 160:
            snippet = snippet[:157] + "..."
    else:
        snippet = f"{app_name}: {window_title}"

    # Build human explanation
    sem_pct = int(round(semantic_score * 100))
    kw_pct = int(round(keyword_score * 100))

    if matched_words:
        terms_quoted = ", ".join(f"'{w}'" for w in matched_words[:4])
        explanation = (
            f"Matched because text in {app_name} contains keywords {terms_quoted} "
            f"with {sem_pct}% semantic relevance."
        )
    elif semantic_score > 0.60:
        explanation = (
            f"High conceptual match ({sem_pct}% semantic similarity) with activity in "
            f"'{window_title}' ({app_name})."
        )
    else:
        explanation = (
            f"Contextual association with '{window_title}' "
            f"(semantic score: {sem_pct}%, keyword overlap: {kw_pct}%)."
        )

    return explanation, snippet
