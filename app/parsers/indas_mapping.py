"""Mappings between Ind AS taxonomy tags and standardized field names."""

from typing import Dict

BALANCE_SHEET_MAPPING: Dict[str, str] = {
    "IndAS\_Assets": "total_assets",
    "IndAS\_Liabilities": "total_liabilities",
    "IndAS\_Equity": "total_equity",
    "IndAS\_CurrentAssets": "current_assets",
    "IndAS\_CurrentLiabilities": "current_liabilities",
}

INCOME_STATEMENT_MAPPING: Dict[str, str] = {
    "IndAS\_Revenue": "revenue",
    "IndAS\_CostOfRevenue": "cost_of_revenue",
    "IndAS\_GrossProfit": "gross_profit",
    "IndAS\_ProfitBeforeTax": "profit_before_tax",
    "IndAS\_ProfitAfterTax": "profit_after_tax",
}

CASH_FLOW_MAPPING: Dict[str, str] = {
    "IndAS\_CashFlowOperating": "net_cash_from_operations",
    "IndAS\_CashFlowInvesting": "net_cash_from_investing",
    "IndAS\_CashFlowFinancing": "net_cash_from_financing",
    "IndAS\_CashAndCashEquivalent": "cash_and_cash_equivalents",
}
