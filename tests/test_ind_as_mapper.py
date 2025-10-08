from app.utils.ind_as_mapper import ConceptMapping, resolve_concept


def test_resolve_concept_with_prefix():
    mapping = resolve_concept("ind-as:TotalAssets")
    assert mapping is not None
    assert mapping.statement == "balance_sheet"
    assert mapping.field == "total_assets"


def test_resolve_concept_without_prefix():
    mapping = resolve_concept("RevenueFromOperations")
    assert mapping is not None
    assert mapping.statement == "income_statement"
    assert mapping.field == "operating_revenue"
