import pytest
from app.retriever import RAGRetriever

def test_scheme_resolution():
    retriever = RAGRetriever()
    
    # Verify resolution to slugs
    assert retriever.resolve_scheme("What is the exit load of HDFC Mid Cap?") == "hdfc-mid-cap-fund-direct-growth"
    assert retriever.resolve_scheme("HDFC Defence fund manager details") == "hdfc-defence-fund-direct-growth"
    assert retriever.resolve_scheme("Tell me about gold etf fof direct plan") == "hdfc-gold-etf-fund-of-fund-direct-plan-growth"
    assert retriever.resolve_scheme("What is the benchmark of large cap fund?") == "hdfc-large-cap-fund-direct-growth"
    assert retriever.resolve_scheme("General queries about mutual funds") is None

def test_semantic_retrieval():
    retriever = RAGRetriever()
    
    # 1. Scheme-Specific Retrieve
    res = retriever.retrieve("Who is the fund manager of HDFC Mid Cap?")
    assert res["resolved_scheme"] == "hdfc-mid-cap-fund-direct-growth"
    assert len(res["chunks"]) > 0
    # The boosted section (fund_management) chunk should be returned first
    assert res["chunks"][0]["metadata"]["section"] == "fund_management"
    assert res["chunks"][0]["metadata"]["scheme_slug"] == "hdfc-mid-cap-fund-direct-growth"

    # 2. Section specific query with exit load keyword
    res_load = retriever.retrieve("HDFC Small Cap exit load details")
    assert res_load["resolved_scheme"] == "hdfc-small-cap-fund-direct-growth"
    assert len(res_load["chunks"]) > 0
    # Boosted section (exit_load) chunk should be first or high priority
    assert res_load["chunks"][0]["metadata"]["section"] == "exit_load"
    assert res_load["chunks"][0]["metadata"]["scheme_slug"] == "hdfc-small-cap-fund-direct-growth"
