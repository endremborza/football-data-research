import os

from ..data_loaders import t2_dir
from ..dvc_util import PipelineElement


entity_coreference_report_dir = os.path.join("reports", "entity_coreference")
coref_example_table_fp = os.path.join(entity_coreference_report_dir, "eg_table.html")


def dump_ecref():
    os.makedirs(entity_coreference_report_dir, exist_ok=True)
    with open(coref_example_table_fp, "w") as fp:
        ...
    # TODO


coref_pe = PipelineElement(
    name="entity_coreference",
    runner=dump_ecref,
    output_path=entity_coreference_report_dir,
    dependency_list=[t2_dir],
)
