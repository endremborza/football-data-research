from .dvc_util import PipelineElement
from .pass_success_model.evaluate_model import eval_pass_model_pe

anal_networks_pe = ...
anal_styles_pe = ...


def export_report():
    ...


report_pe = PipelineElement(
    name="final_report",
    runner=export_report,
    dependency_list=[eval_pass_model_pe, anal_networks_pe, anal_styles_pe],
)
