import json
from pathlib import Path
import pytest
from app.graph.lineage import LineageEngine
from app.graph.metadata_graph import MetadataGraph
from app.parser.csn_parser import CSNParser

# Resolve path relative to this file so tests work from any working directory
SAMPLE_CSN_PATH = Path(__file__).parent.parent.parent / "sample_data" / "sample_csn.json"


@pytest.fixture
def lineage_engine():
    with open(SAMPLE_CSN_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    parsed = CSNParser().parse(data, "sample_csn.json")
    meta_graph = MetadataGraph(parsed)
    return LineageEngine(meta_graph)


def test_object_lineage(lineage_engine):
    # Current_Month_OI_Analytic_Model depends on Current_Month_OI_Heirarchy which depends on Current_Month_Outgoing_Invoices
    lin = lineage_engine.get_object_lineage("Current_Month_OI_Analytic_Model")

    assert "Current_Month_OI_Heirarchy" in lin.upstream
    assert "Current_Month_Outgoing_Invoices" in lin.upstream
    assert "VBRP" in lin.upstream
    assert "VBRK_1" in lin.upstream
    assert "Time_table_heirarchy" in lin.upstream

    # Leaf consumer has no downstream objects
    assert len(lin.downstream) == 0


def test_impact_analysis(lineage_engine):
    # Changing Time_table_heirarchy should impact Current_Month_OI_Analytic_Model and Current_Month_OI_Heirarchy
    impact = lineage_engine.get_impact_analysis("Time_table_heirarchy")

    assert impact.target_object == "Time_table_heirarchy"
    assert "Current_Month_OI_Analytic_Model" in impact.downstream_dependents
    assert "Current_Month_OI_Heirarchy" in impact.downstream_dependents
    assert impact.affected_count >= 2
    assert impact.severity in ("HIGH", "CRITICAL", "MEDIUM")


def test_field_lineage_resolved(lineage_engine):
    # NETWR in Current_Month_OI_Heirarchy maps back to Current_Month_Outgoing_Invoices.NETWR and VBRP.NETWR
    res = lineage_engine.get_field_lineage("Current_Month_OI_Heirarchy", "NETWR")
    assert res.status == "resolved"
    assert res.source_field == "NETWR"
    assert len(res.hops) >= 2


def test_field_lineage_unknown(lineage_engine):
    res = lineage_engine.get_field_lineage("Current_Month_OI_Analytic_Model", "NON_EXISTENT_FIELD")
    assert res.status == "unknown"
    assert "not found" in res.reason.lower()


def test_chain_lineage_logic():
    # Synthetic chain test: A -> B -> C
    synth_csn = {
        "definitions": {
            "A": {
                "kind": "entity",
                "query": {"SELECT": {"from": {"ref": ["B"]}}}
            },
            "B": {
                "kind": "entity",
                "query": {"SELECT": {"from": {"ref": ["C"]}}}
            },
            "C": {
                "kind": "entity"
            }
        }
    }
    parsed = CSNParser().parse(synth_csn, "synth.json")
    graph = MetadataGraph(parsed)
    engine = LineageEngine(graph)

    lin_a = engine.get_object_lineage("A")
    assert "B" in lin_a.upstream
    assert "C" in lin_a.upstream

    impact_c = engine.get_impact_analysis("C")
    assert "B" in impact_c.downstream_dependents
    assert "A" in impact_c.downstream_dependents
