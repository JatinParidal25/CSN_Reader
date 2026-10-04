import json
from pathlib import Path
import pytest
from app.parser.csn_parser import CSNParser

# Resolve path relative to this file so tests work from any working directory
SAMPLE_CSN_PATH = Path(__file__).parent.parent.parent / "sample_data" / "sample_csn.json"


@pytest.fixture
def sample_csn():
    with open(SAMPLE_CSN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_csn_parser_basic(sample_csn):
    parser = CSNParser()
    result = parser.parse(sample_csn, "sample_csn.json")

    assert result.object_count > 0
    assert result.relationship_count > 0
    assert result.field_count > 0
    assert result.measure_count > 0


def test_object_extraction(sample_csn):
    parser = CSNParser()
    result = parser.parse(sample_csn, "sample_csn.json")
    names = [obj.name for obj in result.objects]

    assert "Current_Month_OI_Analytic_Model" in names
    assert "Current_Month_OI_Heirarchy" in names
    assert "Time_table_heirarchy" in names
    assert "Current_Month_Outgoing_Invoices" in names
    assert "VBRP" in names
    assert "VBRK_1" in names


def test_measure_extraction(sample_csn):
    parser = CSNParser()
    result = parser.parse(sample_csn, "sample_csn.json")

    cube = next(obj for obj in result.objects if obj.name == "Current_Month_OI_Analytic_Model")
    measures = [m.name for m in cube.measures]
    assert "NETWR" in measures

    netwr_field = next(f for f in cube.fields if f.name == "NETWR")
    assert netwr_field.is_measure is True
    assert netwr_field.aggregation == "SUM"


def test_association_extraction(sample_csn):
    parser = CSNParser()
    result = parser.parse(sample_csn, "sample_csn.json")

    cube = next(obj for obj in result.objects if obj.name == "Current_Month_OI_Analytic_Model")
    targets = [a.target for a in cube.associations]
    assert "Time_table_heirarchy" in targets


def test_relationship_creation(sample_csn):
    parser = CSNParser()
    result = parser.parse(sample_csn, "sample_csn.json")

    rel_tuples = [(r.source, r.target, r.relationship_type) for r in result.relationships]

    # Verify key lineage relationships
    assert any(
        r[0] == "Current_Month_OI_Analytic_Model" and r[1] == "Current_Month_OI_Heirarchy"
        for r in rel_tuples
    )
    assert any(
        r[0] == "Current_Month_OI_Heirarchy" and r[1] == "Current_Month_Outgoing_Invoices"
        for r in rel_tuples
    )
    assert any(
        r[0] == "Current_Month_Outgoing_Invoices" and r[1] in ("VBRP", "VBRK_1")
        for r in rel_tuples
    )


def test_defensive_parser_on_empty_and_minimal():
    parser = CSNParser()
    # Empty definitions
    res = parser.parse({"definitions": {}}, "empty.json")
    assert res.object_count == 0

    # Minimal entity without elements or query
    res2 = parser.parse({"definitions": {"EntityA": {"kind": "entity"}}}, "minimal.json")
    assert res2.object_count == 1
    assert res2.objects[0].name == "EntityA"
    assert res2.objects[0].fields == []
