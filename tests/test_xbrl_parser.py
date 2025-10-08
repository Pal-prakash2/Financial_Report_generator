from decimal import Decimal
from textwrap import dedent

from app.services.xbrl_parser import XBRLParserService


SAMPLE_XBRL = dedent(
    """
    <xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:ind-as="http://mca.gov.in/indas/2016">
        <context id="C1">
            <entity>
                <identifier scheme="http://www.mca.gov.in/CIN">L12345MH1956PLC012345</identifier>
            </entity>
            <period>
                <startDate>2023-04-01</startDate>
                <endDate>2024-03-31</endDate>
            </period>
        </context>
        <unit id="U1">
            <measure>iso4217:INR</measure>
        </unit>
        <ind-as:TotalAssets contextRef="C1" unitRef="U1">1000</ind-as:TotalAssets>
        <ind-as:TotalLiabilities contextRef="C1" unitRef="U1">600</ind-as:TotalLiabilities>
        <ind-as:ShareholdersEquity contextRef="C1" unitRef="U1">400</ind-as:ShareholdersEquity>
        <ind-as:RevenueFromOperations contextRef="C1" unitRef="U1">900</ind-as:RevenueFromOperations>
        <ind-as:OtherIncome contextRef="C1" unitRef="U1">100</ind-as:OtherIncome>
        <ind-as:Revenue contextRef="C1" unitRef="U1">1000</ind-as:Revenue>
    </xbrl>
    """
)


def test_xbrl_parser_extracts_statements(tmp_path):
    sample_path = tmp_path / "sample.xbrl"
    sample_path.write_text(SAMPLE_XBRL)

    parser = XBRLParserService()
    result = parser.parse(sample_path)

    balance_sheet = result.statements["balance_sheet"]
    period_label = next(iter(balance_sheet["total_assets"].keys()))

    assert balance_sheet["total_assets"][period_label] == Decimal("1000")
    assert balance_sheet["total_liabilities"][period_label] == Decimal("600")
    assert balance_sheet["shareholders_equity"][period_label] == Decimal("400")

    income_statement = result.statements["income_statement"]
    assert income_statement["operating_revenue"][period_label] == Decimal("900")
    assert income_statement["total_revenue"][period_label] == Decimal("1000")

    assert result.metadata["entities"] == ["L12345MH1956PLC012345"]
    assert result.metadata["unmapped_count"] == 0
    assert result.unmapped_facts == []
    assert result.audit_trail


def test_xbrl_parser_collects_unmapped_concepts(tmp_path):
    xbrl_payload = dedent(
        """
        <xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:ind-as="http://mca.gov.in/indas/2016">
            <context id="C1">
                <entity>
                    <identifier scheme="http://www.mca.gov.in/CIN">L54321MH1956PLC999999</identifier>
                </entity>
                <period>
                    <startDate>2022-04-01</startDate>
                    <endDate>2023-03-31</endDate>
                </period>
            </context>
            <unit id="U1">
                <measure>iso4217:INR</measure>
            </unit>
            <ind-as:UnknownMetric contextRef="C1" unitRef="U1">123</ind-as:UnknownMetric>
        </xbrl>
        """
    )

    sample_path = tmp_path / "unknown.xbrl"
    sample_path.write_text(xbrl_payload)

    parser = XBRLParserService()
    result = parser.parse(sample_path)

    assert result.metadata["unmapped_count"] == 1
    assert len(result.unmapped_facts) == 1
    fact = result.unmapped_facts[0]
    assert fact.concept == "UnknownMetric"
    assert fact.raw_tag == "{http://mca.gov.in/indas/2016}UnknownMetric"
    assert fact.context_ref == "C1"
    assert fact.unit == "U1"
    assert fact.raw_value == "123"