from .dvc_util import PipelineElement
from .pass_success_model.evaluate_model import eval_pass_model_pe
from .network.present_network import plot_network_pe

anal_styles_pe = ...


def export_report():
    ...


report_pe = PipelineElement(
    name="final_report",
    runner=export_report,
    dependency_list=[eval_pass_model_pe, plot_network_pe, anal_styles_pe],
)
