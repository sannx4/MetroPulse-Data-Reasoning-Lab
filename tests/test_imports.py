import importlib


def test_package_imports() -> None:
    modules = [
        "evidence_graph",
        "evidence_graph.graph",
        "evidence_graph.loader",
        "evidence_graph.metrics",
        "evidence_graph.models",
    ]

    for module in modules:
        importlib.import_module(module)
