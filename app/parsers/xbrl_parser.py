"""Core Ind AS XBRL parsing utilities."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional
from xml.etree import ElementTree as ET

from app.parsers.indas_mapping import (
    BALANCE_SHEET_MAPPING,
    CASH_FLOW_MAPPING,
    INCOME_STATEMENT_MAPPING,
)
from app.utils.currency import normalize_to_abs
from app.utils.date import financial_year_for

try:  # pragma: no cover - optional dependency
    from pyxbrl import XBRLParser  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    XBRLParser = None  # type: ignore


@dataclass(slots=True)
class ParsedStatementBundle:
    balance_sheet: Dict[str, Decimal]
    income_statement: Dict[str, Decimal]
    cash_flow: Dict[str, Decimal]
    metadata: Dict[str, Any]


class IndASXBRLParser:
    """Parser that maps Ind AS taxonomy values into standardized statements."""

    def __init__(self, tolerance: Decimal | float = Decimal("0")) -> None:
        self.tolerance = Decimal(str(tolerance))

    def parse_document(self, file_path: str | Path) -> ParsedStatementBundle:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)

        if XBRLParser is not None:  # pragma: no cover - depends on external library
            try:
                return self._parse_with_pyxbrl(path)
            except Exception as exc:  # fall back to standard parser
                raise RuntimeError("Failed to parse XBRL using py-xbrl") from exc

        return self._parse_with_etree(path)

    def _parse_with_pyxbrl(self, path: Path) -> ParsedStatementBundle:  # pragma: no cover
        parser = XBRLParser()
        xbrl = parser.parse(path.read_bytes())
        facts = {fact.name: fact for fact in xbrl.facts}  # type: ignore[attr-defined]
        units = self._build_units_from_pyxbrl(xbrl)
        context_dates = self._extract_context_dates(xbrl)

        balance_sheet = self._map_section(facts, units, BALANCE_SHEET_MAPPING)
        income_statement = self._map_section(facts, units, INCOME_STATEMENT_MAPPING)
        cash_flow = self._map_section(facts, units, CASH_FLOW_MAPPING)

        metadata = {
            "period_start": context_dates[0],
            "period_end": context_dates[1],
            "financial_year": financial_year_for(context_dates[1]),
            "source": str(path),
        }
        return ParsedStatementBundle(balance_sheet, income_statement, cash_flow, metadata)

    def _parse_with_etree(self, path: Path) -> ParsedStatementBundle:
        tree = ET.parse(path)
        root = tree.getroot()
        units = self._build_units_from_xml(root)
        context_dates = self._extract_context_dates_from_xml(root)

        balance_sheet = self._map_section_xml(root, units, BALANCE_SHEET_MAPPING)
        income_statement = self._map_section_xml(root, units, INCOME_STATEMENT_MAPPING)
        cash_flow = self._map_section_xml(root, units, CASH_FLOW_MAPPING)

        metadata = {
            "period_start": context_dates[0].isoformat(),
            "period_end": context_dates[1].isoformat(),
            "financial_year": financial_year_for(context_dates[1]),
            "source": str(path),
        }
        return ParsedStatementBundle(balance_sheet, income_statement, cash_flow, metadata)

    @staticmethod
    def _map_section(
        facts: Mapping[str, Any],
        units: Mapping[str, Optional[str]],
        mapping: Mapping[str, str],
    ) -> Dict[str, Decimal]:  # pragma: no cover - exercised when dependency present
        data: Dict[str, Decimal] = {}
        for taxonomy_tag, std_name in mapping.items():
            fact = facts.get(taxonomy_tag)
            if fact is None:
                continue
            unit = units.get(getattr(fact, "unit_id", ""))
            value = getattr(fact, "value", None)
            if value is None:
                continue
            data[std_name] = normalize_to_abs(value, unit or None) or Decimal("0")
        return data

    def _map_section_xml(
        self,
        root: ET.Element,
        units: Mapping[str, Optional[str]],
        mapping: Mapping[str, str],
    ) -> Dict[str, Decimal]:
        data: Dict[str, Decimal] = {}
        for taxonomy_tag, std_name in mapping.items():
            element = self._find_fact(root, taxonomy_tag)
            if element is None or element.text is None:
                continue
            unit_ref = element.attrib.get("unitRef")
            unit = units.get(unit_ref) if unit_ref else None
            data[std_name] = normalize_to_abs(element.text, unit)
        return data

    @staticmethod
    def _find_fact(root: ET.Element, tag: str) -> Optional[ET.Element]:
        # Search while ignoring namespaces
        for elem in root.iter():
            if elem.tag.split("}")[-1] == tag:
                return elem
        return None

    @staticmethod
    def _build_units_from_pyxbrl(xbrl: Any) -> Dict[str, Optional[str]]:  # pragma: no cover
        units: Dict[str, Optional[str]] = {}
        for unit in getattr(xbrl, "units", []):
            unit_id = getattr(unit, "id", None)
            measures = getattr(unit, "measures", [])
            unit_name = measures[0] if measures else None
            if unit_id:
                units[unit_id] = unit_name
        return units

    @staticmethod
    def _build_units_from_xml(root: ET.Element) -> Dict[str, Optional[str]]:
        units: Dict[str, Optional[str]] = {}
        for unit in root.findall(".//{*}unit"):
            unit_id = unit.attrib.get("id")
            measure = None
            measure_elem = unit.find("{*}measure")
            if measure_elem is not None and measure_elem.text:
                measure = measure_elem.text.split(":")[-1]
            if unit_id:
                units[unit_id] = measure
        return units

    @staticmethod
    def _extract_context_dates(xbrl: Any) -> tuple[Any, Any]:  # pragma: no cover
        contexts = getattr(xbrl, "contexts", [])
        if not contexts:
            raise ValueError("No context found in XBRL document")
        context = contexts[0]
        period = getattr(context, "period", None)
        return getattr(period, "start_date"), getattr(period, "end_date")

    @staticmethod
    def _extract_context_dates_from_xml(root: ET.Element) -> tuple[Any, Any]:
        for context in root.findall(".//{*}context"):
            period = context.find("{*}period")
            if period is None:
                continue
            start = period.findtext("{*}startDate")
            end = period.findtext("{*}endDate") or period.findtext("{*}instant")
            if start and end:
                return IndASXBRLParser._parse_iso_date(start), IndASXBRLParser._parse_iso_date(end)
        raise ValueError("Unable to determine reporting period from XBRL")

    @staticmethod
    def _parse_iso_date(value: str) -> date:
        return date.fromisoformat(value)
