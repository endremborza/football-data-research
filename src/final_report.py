import os
import shutil
import glob

from .dvc_util import PipelineElement
from .pass_success_model.evaluate_model import (
    eval_pass_model_pe,
    pass_success_model_eval_dir,
)
from .network.present_network import plot_network_pe, network_plot_dir
from .style.report_style_vars import report_style_pe, style_report_dir

heatmap_fp = os.path.join(style_report_dir, "heatmap.png")
style_table_fp = os.path.join(style_report_dir, "style_table.html")
network_fps = glob.glob(network_plot_dir + "*.svg")


figure_dir = os.path.join("reports", "figures")
out_file = os.path.join("reports", "main_report.md")
frame_fp = os.path.join("reports", "main_report_frame.md")


def export_report():
    os.makedirs(figure_dir, exist_ok=True)
    shutil.copyfile(heatmap_fp, os.path.join(figure_dir, "heatmap.png"))
    shutil.copytree(network_plot_dir, figure_dir, dirs_exist_ok=True)

    style_table_str = open(style_table_fp).read()

    with open(frame_fp) as fp:
        report_frame = fp.read()

    with open(out_file, "w") as fp:
        fp.write(report_frame.format(style_table=style_table_str))


report_pe = PipelineElement(
    name="final_report",
    runner=export_report,
    dependency_list=[
        eval_pass_model_pe,
        plot_network_pe,
        report_style_pe,
        "reports/main_report_frame.md",
    ],
    out_nonchache=figure_dir
)
