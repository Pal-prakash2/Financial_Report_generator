"""Mapping utilities for Ind AS taxonomy concepts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class ConceptMapping:
    statement: str
    field: str
    description: Optional[str] = None


# Core mapping dictionary for frequently used Ind AS concepts. Keys are stored in lowercase
# to allow case-insensitive lookups and cover both prefixed (e.g., ind-as:Revenue) and
# plain concept names (e.g., Revenue).
_IND_AS_MAPPING: Dict[str, ConceptMapping] = {
    # Income Statement
    "ind-as:revenuefromoperations": ConceptMapping("income_statement", "operating_revenue", "Revenue from operations"),
    "revenuefromoperations": ConceptMapping("income_statement", "operating_revenue"),
    "ind-as:otherincome": ConceptMapping("income_statement", "other_income", "Other income"),
    "otherincome": ConceptMapping("income_statement", "other_income"),
    "ind-as:revenue": ConceptMapping("income_statement", "total_revenue", "Total revenue"),
    "revenue": ConceptMapping("income_statement", "total_revenue"),
    "ind-as:totalincome": ConceptMapping("income_statement", "total_income", "Total income"),
    "totalincome": ConceptMapping("income_statement", "total_income"),
    "ind-as:profitbeforetax": ConceptMapping("income_statement", "profit_before_tax"),
    "profitbeforetax": ConceptMapping("income_statement", "profit_before_tax"),
    "ind-as:taxexpense": ConceptMapping("income_statement", "tax_expense"),
    "taxexpense": ConceptMapping("income_statement", "tax_expense"),
    "ind-as:profitaftertax": ConceptMapping("income_statement", "profit_after_tax"),
    "profitaftertax": ConceptMapping("income_statement", "profit_after_tax"),
    "ind-as:totalexpenses": ConceptMapping("income_statement", "total_expenses"),
    "totalexpenses": ConceptMapping("income_statement", "total_expenses"),

    # Balance Sheet
    "ind-as:totalassets": ConceptMapping("balance_sheet", "total_assets"),
    "totalassets": ConceptMapping("balance_sheet", "total_assets"),
    "ind-as:currentassets": ConceptMapping("balance_sheet", "current_assets"),
    "currentassets": ConceptMapping("balance_sheet", "current_assets"),
    "ind-as:noncurrentassets": ConceptMapping("balance_sheet", "non_current_assets"),
    "noncurrentassets": ConceptMapping("balance_sheet", "non_current_assets"),
    "ind-as:totalliabilities": ConceptMapping("balance_sheet", "total_liabilities"),
    "totalliabilities": ConceptMapping("balance_sheet", "total_liabilities"),
    "ind-as:currentliabilities": ConceptMapping("balance_sheet", "current_liabilities"),
    "currentliabilities": ConceptMapping("balance_sheet", "current_liabilities"),
    "ind-as:shareholdersequity": ConceptMapping("balance_sheet", "shareholders_equity"),
    "shareholdersequity": ConceptMapping("balance_sheet", "shareholders_equity"),
    "ind-as:totalequity": ConceptMapping("balance_sheet", "total_equity"),
    "totalequity": ConceptMapping("balance_sheet", "total_equity"),

    # Cash Flow
    "ind-as:netcashflowfromoperatingactivities": ConceptMapping("cash_flow", "net_cash_from_operations"),
    "netcashflowfromoperatingactivities": ConceptMapping("cash_flow", "net_cash_from_operations"),
    "ind-as:netcashflowfrominvestingactivities": ConceptMapping("cash_flow", "net_cash_from_investing"),
    "netcashflowfrominvestingactivities": ConceptMapping("cash_flow", "net_cash_from_investing"),
    "ind-as:netcashflowfromfinancingactivities": ConceptMapping("cash_flow", "net_cash_from_financing"),
    "netcashflowfromfinancingactivities": ConceptMapping("cash_flow", "net_cash_from_financing"),
    "ind-as:cashandcashequivalents": ConceptMapping("cash_flow", "cash_and_cash_equivalents"),
    "cashandcashequivalents": ConceptMapping("cash_flow", "cash_and_cash_equivalents"),
}


def resolve_concept(concept_name: str) -> Optional[ConceptMapping]:
    """Return the mapping metadata for a given concept name.

    The lookup is case-insensitive and handles both prefixed (e.g. ``ind-as:Revenue``)
    and plain names (``Revenue``). When the concept is not recognised, ``None`` is
    returned so the caller can ignore the fact gracefully.
    """

    if not concept_name:
        return None
    key = concept_name.lower()
    if key in _IND_AS_MAPPING:
        return _IND_AS_MAPPING[key]
    # Attempt to remove namespace URI markers such as ``{namespace}TotalAssets``
    if key.startswith("{") and "}" in key:
        _, remainder = key.split("}", 1)
        remainder_key = remainder.lower()
        return _IND_AS_MAPPING.get(remainder_key)
    return None


def all_supported_concepts() -> Iterable[str]:
    """Return all concept keys supported by the mapper."""

    return _IND_AS_MAPPING.keys()
