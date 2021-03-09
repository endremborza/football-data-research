import glob
import os
import shutil

from .dvc_util import PipelineElement
from .entity_coreference.run_entity_coreference import (
    coref_example_table_fp,
    coref_pe,
)
from .network.present_network import network_plot_dir, plot_network_pe
from .pass_success_model.evaluate_model import (
    eval_pass_model_pe,
    metric_table_fp,
    pass_success_model_eval_dir,
)
from .style.report_style_vars import ExportedFiles, report_style_pe

link_base = "https://github.com/endremborza/football-data-research/blob/main/{}#L{}"

network_fps = glob.glob(network_plot_dir + "*.svg")

figure_dir = os.path.join("reports", "figures")
out_file = os.path.join("reports", "main_report.md")
frame_fp = os.path.join("reports", "main_report_frame.md")


def export_report():
    os.makedirs(figure_dir, exist_ok=True)
    shutil.copyfile(ExportedFiles.heatmap, os.path.join(figure_dir, "heatmap.png"))
    shutil.copytree(network_plot_dir, figure_dir, dirs_exist_ok=True)
    for model_eval_fig in glob.glob(pass_success_model_eval_dir + "/*.png"):
        shutil.copy2(model_eval_fig, figure_dir)

    style_tables = [
        "source_example",
        "all_ginis",
        "result_of_sample_match",
        "style_agged",
        "under_probit",
        "over_probit",
    ]
    style_table_dic = {k: open(getattr(ExportedFiles, k)).read() for k in style_tables}
    metric_table_str = open(metric_table_fp).read()
    coref_table_str = open(coref_example_table_fp).read()

    with open(frame_fp) as fp:
        report_frame = fp.read()

    with open(out_file, "w") as fp:
        fp.write(
            report_frame.format(
                **{
                    **style_table_dic,
                    "metric_table": metric_table_str,
                    "coref_table": coref_table_str,
                }
            )
        )

    dag_base = "\n".join(
        [
            f"- {pe.name}".replace(*pe.get_dag_replace(link_base))
            for pe in PipelineElement.all_instances()
        ]
    )
    with open(os.path.join("reports", "dvcdag.md"), "w") as fp:
        fp.write(dag_base)


report_pe = PipelineElement(
    name="final_report",
    runner=export_report,
    dependency_list=[
        eval_pass_model_pe,
        plot_network_pe,
        report_style_pe,
        coref_pe,
        "reports/main_report_frame.md",
    ],
    out_nonchache=figure_dir,
)
