from wh40k_cheatsheet.render.glossary import sort_glossary_terms


def _term(term: str, text: str = "def") -> dict:
    return {"term": term, "text": text}


def test_shuffled_ascii_terms_sort_alphabetically():
    terms = [_term("TORRENT"), _term("ASSAULT"), _term("MELTA X"), _term("BLAST X")]
    result = sort_glossary_terms(terms)
    assert [t["term"] for t in result] == ["ASSAULT", "BLAST X", "MELTA X", "TORRENT"]


def test_german_umlauts_and_sharp_s_fold_under_base_letter():
    terms = [
        _term("ZUSÄTZLICHE ATTACKEN"),
        _term("ÜBERSCHWERER LÄUFER"),
        _term("TÖDLICHE TREFFER"),
        _term("VERHEERENDE WUNDEN"),
        _term("STRAßE"),
        _term("STRASSE"),
    ]
    result = [t["term"] for t in sort_glossary_terms(terms)]
    assert result.index("TÖDLICHE TREFFER") < result.index("ÜBERSCHWERER LÄUFER")
    assert result.index("ÜBERSCHWERER LÄUFER") < result.index("VERHEERENDE WUNDEN")
    assert result.index("VERHEERENDE WUNDEN") < result.index("ZUSÄTZLICHE ATTACKEN")
    # "STRAßE" and "STRASSE" fold to the same key ("strasse") and must sort adjacently.
    assert abs(result.index("STRAßE") - result.index("STRASSE")) == 1


def test_mixed_case_terms_interleave_rather_than_forming_separate_runs():
    terms = [_term("torrent"), _term("ASSAULT"), _term("Blast X")]
    result = [t["term"] for t in sort_glossary_terms(terms)]
    assert result == ["ASSAULT", "Blast X", "torrent"]


def test_ordering_ignores_text_and_html_bodies():
    terms = [_term("TORRENT", text="zzz"), _term("ASSAULT", text="aaa")]
    result = [t["term"] for t in sort_glossary_terms(terms)]
    assert result == ["ASSAULT", "TORRENT"]


def test_duplicate_terms_keep_authored_relative_order():
    first = {"term": "ASSAULT", "text": "first"}
    second = {"term": "ASSAULT", "text": "second"}
    result = sort_glossary_terms([first, second])
    assert result == [first, second]


def test_entry_count_and_payload_are_preserved():
    terms = [_term("TORRENT", text="Auto-hits."), _term("ASSAULT", text="Enables Assault Shooting.")]
    result = sort_glossary_terms(terms)
    assert len(result) == len(terms)
    assert {id(t) for t in result} == {id(t) for t in terms}
    for entry in terms:
        assert entry in result


def test_input_list_is_not_mutated_and_result_is_a_new_list():
    terms = [_term("TORRENT"), _term("ASSAULT")]
    original_order = list(terms)
    result = sort_glossary_terms(terms)
    assert terms == original_order
    assert result is not terms


def test_empty_terms_list_returns_empty_list():
    assert sort_glossary_terms([]) == []


def test_single_term_list_returns_that_term():
    terms = [_term("ASSAULT")]
    assert sort_glossary_terms(terms) == terms


def test_entry_missing_term_key_sorts_first_without_raising():
    malformed = {"text": "no term here"}
    terms = [_term("ASSAULT"), malformed]
    result = sort_glossary_terms(terms)
    assert result[0] is malformed
    assert result[1]["term"] == "ASSAULT"


def test_entry_with_non_string_term_sorts_first_without_raising():
    malformed = {"term": 42, "text": "not a string"}
    terms = [_term("ASSAULT"), malformed]
    result = sort_glossary_terms(terms)
    assert result[0] is malformed
    assert result[1]["term"] == "ASSAULT"


def test_authored_order_never_affects_output():
    terms = [_term("TORRENT"), _term("ASSAULT"), _term("MELTA X"), _term("BLAST X")]
    forward = [t["term"] for t in sort_glossary_terms(terms)]
    reversed_terms = list(reversed(terms))
    reversed_result = [t["term"] for t in sort_glossary_terms(reversed_terms)]
    assert forward == reversed_result


def test_appending_a_new_term_lands_in_alphabetical_position_not_last():
    already_sorted = [_term("ASSAULT"), _term("TORRENT")]
    appended = [*already_sorted, _term("MELTA X")]
    result = [t["term"] for t in sort_glossary_terms(appended)]
    assert result == ["ASSAULT", "MELTA X", "TORRENT"]
