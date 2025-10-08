"""Service-level XBRL parsing utilities focused on Ind AS concepts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional
from xml.etree import ElementTree as ET

from app.utils.currency import normalize_to_abs
from app.utils.date import financial_year_for
from app.utils.ind_as_mapper import resolve_concept

try:  # pragma: no cover - optional dependency
    from pyxbrl import XBRLParser as PyXBRLParser  # type: ignore
except ImportError:  # pragma: no cover - graceful fallback when library missing
    PyXBRLParser = None  # type: ignore

StatementMatrix = Dict[str, Dict[str, Dict[str, Decimal]]]


@dataclass(slots=True)
class ContextInfo:
    """Normalized context information extracted from the XBRL document."""

    id: str
    entity: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    instant: Optional[date]

    @property
    def label(self) -> str:
        if self.start_date and self.end_date:
            try:
                fy = financial_year_for(self.end_date)
                return f"{fy} ({self.start_date.isoformat()} to {self.end_date.isoformat()})"
            except ValueError:
                pass
            return f"{self.start_date.isoformat()} to {self.end_date.isoformat()}"
        if self.instant:
            return f"As of {self.instant.isoformat()}"
        return self.id

    @property
    def financial_year(self) -> Optional[str]:
        if self.end_date:
            try:
                return financial_year_for(self.end_date)
            except ValueError:
                return None
        if self.instant:
            try:
                return financial_year_for(self.instant)
            except ValueError:
                return None
        return None


@dataclass(slots=True)
class AuditRecord:
    statement: str
    field: str
    concept: str
    context_ref: str
    period: str
    unit: Optional[str]
    value: Decimal


@dataclass(slots=True)
class UnmappedFact:
    concept: str
    raw_tag: Optional[str]
    context_ref: Optional[str]
    unit: Optional[str]
    raw_value: str


@dataclass(slots=True)
class XBRLParseResult:
    statements: StatementMatrix
    audit_trail: List[AuditRecord]
    contexts: Dict[str, ContextInfo]
    metadata: Dict[str, object]
    unmapped_facts: List[UnmappedFact]

    def statement(self, name: str) -> Dict[str, Dict[str, Decimal]]:
        return self.statements.get(name, {})


class XBRLParserService:
    """Parse MCA AOC-4 XBRL instance documents into normalized financial statements."""

    SUPPORTED_EXTENSIONS = {".xml", ".xbrl"}

    # Best-effort mapping from raw unit names to multiplier identifiers used in currency helpers.
    UNIT_ALIASES: Dict[str, str] = {
        "inr": "INR",
        "iso4217:inr": "INR",
        "inrincrores": "CRORES",
        "inrincrore": "CRORES",
        "crore": "CRORES",
        "crores": "CRORES",
        "inrinlakhs": "LAKHS",
        "inrlakhs": "LAKHS",
        "lakh": "LAKHS",
        "lakhs": "LAKHS",
    }

    def parse(self, file_path: str | Path) -> XBRLParseResult:
        path = Path(file_path)
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported file extension for XBRL parsing")
        if PyXBRLParser is not None:  # pragma: no cover - exercised when dependency installed
            try:
                parser = PyXBRLParser()
                xbrl = parser.parse(path.read_bytes())
                return self._parse_with_pyxbrl(xbrl, source=str(path))
            except Exception:
                # Fall back to XML parsing on failure to keep robustness.
                pass
        return self._parse_with_xml(path.read_bytes(), source=str(path))

    # ------------------------------------------------------------------
    # XML parsing fallback
    # ------------------------------------------------------------------

    def _parse_with_xml(self, payload: bytes, *, source: str) -> XBRLParseResult:
        root = ET.fromstring(payload)
        contexts = self._extract_contexts_xml(root)
        units = self._extract_units_xml(root)
        statements: Dict[str, DefaultDict[str, Dict[str, Decimal]]] = {
            "income_statement": defaultdict(dict),
            "balance_sheet": defaultdict(dict),
            "cash_flow": defaultdict(dict),
        }
        audit_trail: List[AuditRecord] = []
        unmapped: List[UnmappedFact] = []
        entities: set[str] = set()
        used_units: set[str] = set()

        for element in root.findall('.//*[@contextRef]'):
            concept_name = self._concept_name(element)
            concept = resolve_concept(concept_name) or resolve_concept(element.tag)
            context_ref = element.attrib.get("contextRef")
            if not context_ref or context_ref not in contexts:
                if concept is None:
                    unmapped.append(
                        UnmappedFact(
                            concept=concept_name,
                            raw_tag=element.tag,
                            context_ref=context_ref,
                            unit=element.attrib.get("unitRef"),
                            raw_value=(element.text or "").strip(),
                        )
                    )
                continue
            raw_value = (element.text or "").strip()
            if not raw_value or element.attrib.get("{http://www.xbrl.org/2003/instance}nil") == "true":
                if concept is None:
                    unmapped.append(
                        UnmappedFact(
                            concept=concept_name,
                            raw_tag=element.tag,
                            context_ref=context_ref,
                            unit=element.attrib.get("unitRef"),
                            raw_value=raw_value,
                        )
                    )
                continue
            if concept is None:
                unmapped.append(
                    UnmappedFact(
                        concept=concept_name,
                        raw_tag=element.tag,
                        context_ref=context_ref,
                        unit=element.attrib.get("unitRef"),
                        raw_value=raw_value,
                    )
                )
                continue
            unit_ref = element.attrib.get("unitRef")
            unit = units.get(unit_ref) if unit_ref else None
            normalized_unit = self._normalize_unit(unit)
            try:
                value = normalize_to_abs(raw_value, normalized_unit)
            except (ValueError, TypeError):
                continue
            if value is None:
                continue

            context = contexts[context_ref]
            period_label = context.label
            statement_bucket = statements[concept.statement]
            exists = statement_bucket[concept.field].get(period_label)
            if exists is not None:
                # Keep the most recently encountered value when duplicates exist.
                statement_bucket[concept.field][period_label] = value
            else:
                statement_bucket[concept.field][period_label] = value

            audit_trail.append(
                AuditRecord(
                    statement=concept.statement,
                    field=concept.field,
                    concept=concept_name,
                    context_ref=context_ref,
                    period=period_label,
                    unit=unit,
                    value=value,
                )
            )
            if context.entity:
                entities.add(context.entity)
            if unit:
                used_units.add(unit)

        metadata = {
            "source": source,
            "entities": sorted(entities),
            "periods": {
                ctx_id: {
                    "label": ctx.label,
                    "start_date": ctx.start_date.isoformat() if ctx.start_date else None,
                    "end_date": ctx.end_date.isoformat() if ctx.end_date else None,
                    "instant": ctx.instant.isoformat() if ctx.instant else None,
                    "financial_year": ctx.financial_year,
                }
                for ctx_id, ctx in contexts.items()
            },
            "units": sorted(used_units),
            "unmapped_count": len(unmapped),
        }

        normalized_statements: StatementMatrix = {
            name: {field: dict(periods) for field, periods in bucket.items()}
            for name, bucket in statements.items()
        }
        return XBRLParseResult(
            statements=normalized_statements,
            audit_trail=audit_trail,
            contexts=contexts,
            metadata=metadata,
            unmapped_facts=unmapped,
        )

    # ------------------------------------------------------------------
    # Optional py-xbrl parsing path (best effort, falls back to XML otherwise)
    # ------------------------------------------------------------------

    def _parse_with_pyxbrl(self, xbrl: object, *, source: str) -> XBRLParseResult:  # pragma: no cover
        contexts = {}
        for context in getattr(xbrl, "contexts", []):
            context_id = getattr(context, "id", None)
            if not context_id:
                continue
            start = self._coerce_date(getattr(getattr(context, "period", None), "start_date", None))
            end = self._coerce_date(getattr(getattr(context, "period", None), "end_date", None))
            instant = self._coerce_date(getattr(getattr(context, "period", None), "instant", None))
            entity = getattr(getattr(context, "entity", None), "identifier", None)
            contexts[context_id] = ContextInfo(
                id=context_id,
                entity=entity,
                start_date=start,
                end_date=end,
                instant=instant,
            )

        statements: Dict[str, DefaultDict[str, Dict[str, Decimal]]] = {
            "income_statement": defaultdict(dict),
            "balance_sheet": defaultdict(dict),
            "cash_flow": defaultdict(dict),
        }
        audit_trail: List[AuditRecord] = []
        unmapped: List[UnmappedFact] = []
        entities: set[str] = set()
        used_units: set[str] = set()

        unit_lookup: Dict[str, Optional[str]] = {}
        for unit in getattr(xbrl, "units", []):
            unit_id = getattr(unit, "id", None)
            measures = getattr(unit, "measures", [])
            unit_lookup[unit_id] = measures[0] if measures else None

        for fact in getattr(xbrl, "facts", []):
            concept_name = getattr(fact, "name", "")
            mapping = resolve_concept(concept_name)
            if mapping is None:
                value = getattr(fact, "value", None)
                raw_value = str(value) if value is not None else ""
                unmapped.append(
                    UnmappedFact(
                        concept=concept_name,
                        raw_tag=concept_name,
                        context_ref=getattr(fact, "context_id", None),
                        unit=getattr(fact, "unit_id", None),
                        raw_value=raw_value,
                    )
                )
                continue
            context_ref = getattr(fact, "context_id", None)
            if not context_ref or context_ref not in contexts:
                continue
            unit_ref = getattr(fact, "unit_id", None)
            unit = unit_lookup.get(unit_ref) if unit_ref else None
            normalized_unit = self._normalize_unit(unit)
            value = getattr(fact, "value", None)
            try:
                decimal_value = normalize_to_abs(value, normalized_unit)
            except (ValueError, TypeError):
                continue
            if decimal_value is None:
                continue

            context = contexts[context_ref]
            period_label = context.label
            statements[mapping.statement][mapping.field][period_label] = decimal_value
            audit_trail.append(
                AuditRecord(
                    statement=mapping.statement,
                    field=mapping.field,
                    concept=concept_name,
                    context_ref=context_ref,
                    period=period_label,
                    unit=unit,
                    value=decimal_value,
                )
            )
            if context.entity:
                entities.add(context.entity)
            if unit:
                used_units.add(unit)

        metadata = {
            "source": source,
            "entities": sorted(entities),
            "periods": {
                ctx_id: {
                    "label": ctx.label,
                    "start_date": ctx.start_date.isoformat() if ctx.start_date else None,
                    "end_date": ctx.end_date.isoformat() if ctx.end_date else None,
                    "instant": ctx.instant.isoformat() if ctx.instant else None,
                    "financial_year": ctx.financial_year,
                }
                for ctx_id, ctx in contexts.items()
            },
            "units": sorted(used_units),
            "unmapped_count": len(unmapped),
        }
        normalized_statements: StatementMatrix = {
            name: {field: dict(periods) for field, periods in bucket.items()}
            for name, bucket in statements.items()
        }
        return XBRLParseResult(
            statements=normalized_statements,
            audit_trail=audit_trail,
            contexts=contexts,
            metadata=metadata,
            unmapped_facts=unmapped,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_date(value: object) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                if "T" in value:
                    return datetime.fromisoformat(value.replace("Z", "")).date()
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    def _extract_contexts_xml(self, root: ET.Element) -> Dict[str, ContextInfo]:
        contexts: Dict[str, ContextInfo] = {}
        for context in root.findall(".//{*}context"):
            context_id = context.attrib.get("id")
            if not context_id:
                continue
            entity_ident = context.findtext("{*}entity/{*}identifier")
            period = context.find("{*}period")
            start_date = self._coerce_date(period.findtext("{*}startDate") if period is not None else None)
            end_date = self._coerce_date(period.findtext("{*}endDate") if period is not None else None)
            instant = self._coerce_date(period.findtext("{*}instant") if period is not None else None)
            contexts[context_id] = ContextInfo(
                id=context_id,
                entity=entity_ident,
                start_date=start_date,
                end_date=end_date,
                instant=instant,
            )
        return contexts

    def _extract_units_xml(self, root: ET.Element) -> Dict[str, Optional[str]]:
        units: Dict[str, Optional[str]] = {}
        for unit in root.findall(".//{*}unit"):
            unit_id = unit.attrib.get("id")
            if not unit_id:
                continue
            measure = unit.findtext("{*}measure")
            if not measure:
                # Handle <divide> / <unitNumerator> style units by taking the first measure.
                divide = unit.find("{*}divide/{*}unitNumerator/{*}measure")
                measure = divide.text if divide is not None else None
            units[unit_id] = measure
        return units

    @staticmethod
    def _concept_name(element: ET.Element) -> str:
        tag = element.tag
        if tag.startswith("{") and "}" in tag:
            _, local = tag[1:].split("}", 1)
            return local
        return tag

    def _normalize_unit(self, unit: Optional[str]) -> Optional[str]:
        if unit is None:
            return None
        normalized = unit.lower().split(":")[-1]
        return self.UNIT_ALIASES.get(unit.lower(), self.UNIT_ALIASES.get(normalized, None))


__all__ = [
    "XBRLParserService",
    "XBRLParseResult",
    "ContextInfo",
    "AuditRecord",
]
