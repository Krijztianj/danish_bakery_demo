"""Helpers shared by the metric view notebooks (02 and 05)."""
import os
import re

import yaml

YAML_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "metric_views"))


def render(file_name: str, catalog: str, schema: str) -> str:
    """Read a metric view YAML file and substitute ${catalog} / ${schema}."""
    with open(os.path.join(YAML_DIR, file_name), encoding="utf-8") as f:
        text = f.read()
    return text.replace("${catalog}", catalog).replace("${schema}", schema)


def drop_window_measures(yaml_text: str) -> str:
    """Remove window measures and every measure that (transitively) references them."""
    spec = yaml.safe_load(yaml_text)
    dropped = {m["name"] for m in spec.get("measures", []) if "window" in m}
    changed = True
    while changed:
        changed = False
        for m in spec.get("measures", []):
            if m["name"] in dropped:
                continue
            refs = set(re.findall(r"MEASURE\(\s*`?([A-Za-z0-9_ ]+)`?\s*\)", m["expr"]))
            if refs & dropped:
                dropped.add(m["name"])
                changed = True
    spec["measures"] = [m for m in spec["measures"] if m["name"] not in dropped]
    print(f"  dropped window-dependent measures: {sorted(dropped)}")
    return yaml.safe_dump(spec, sort_keys=False, allow_unicode=True)


def apply_metric_view(spark, fqn: str, yaml_text: str, alter: bool = False) -> None:
    """CREATE OR REPLACE (or ALTER) a metric view; retry without window measures if rejected."""
    def run(text):
        if alter:
            spark.sql(f"ALTER VIEW {fqn} AS $$\n{text}\n$$")
        else:
            spark.sql(f"CREATE OR REPLACE VIEW {fqn} WITH METRICS LANGUAGE YAML AS $$\n{text}\n$$")

    try:
        run(yaml_text)
    except Exception as e:  # noqa: BLE001
        if "window:" not in yaml_text:
            raise
        print(f"  failed with window measures ({str(e).splitlines()[0][:200]}) – retrying without them")
        run(drop_window_measures(yaml_text))
    print(f"  {'altered' if alter else 'created'} {fqn}")
