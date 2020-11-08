import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from src.dvc_util import PipelineElement
from src.pass_success_model.prepare_data_for_modelling import load_all_model_data
from src.pass_success_model.run_pass_success_model import (
    load_trained_model,
    run_pass_model_pe,
)

pass_success_model_eval_dir = os.path.join("reports", "pass_success_model_evaluation")
metric_table_fp = os.path.join(pass_success_model_eval_dir, "metrics.html")


def get_metrics(y_test_df, preds, y_score):
    return {
        "accuracy": accuracy_score(y_test_df, preds),
        "recall": recall_score(y_test_df, preds),
        "f1": f1_score(y_test_df, preds),
        "brier": brier_score_loss(y_test_df, y_score),
    }


def plot_success_bars(y_test_df, y_score):
    succ_with_prob = y_test_df.assign(predicted_prob=y_score)
    cat_colname = "Predicted success probability interval"
    bins = np.linspace(0, 1, 21)
    prob_cats = (
        succ_with_prob.assign(
            **{cat_colname: lambda df: pd.cut(df["predicted_prob"], bins)}
        )
        .groupby(cat_colname)
        .agg(["mean", "count"])
    )

    prob_cats["is_success"]["count"].pipe(lambda s: s / s.sum()).plot.bar(
        figsize=(13, 7)
    )
    plt.ylabel("rate of observations")
    plt.tight_layout()
    plt.savefig(os.path.join(pass_success_model_eval_dir, "pred_bins.png"))

    prob_cats.loc[:, (slice(None), "mean")].pipe(
        lambda df: pd.DataFrame(
            df.values,
            index=df.index,
            columns=["success rate in interval", "mean predicted success in interval"],
        )
    ).plot.bar(figsize=(13, 7))
    plt.tight_layout()
    plt.savefig(os.path.join(pass_success_model_eval_dir, "pred_bin_means.png"))


def plot_cm(y_test_df, preds):
    cm = confusion_matrix(y_test_df, preds, normalize="pred")
    ConfusionMatrixDisplay(cm).plot()
    plt.tight_layout()
    plt.savefig(os.path.join(pass_success_model_eval_dir, "confusion_matrix.png"))


def plot_roc(y_test_df, y_score, trained_pipeline):
    fpr, tpr, _ = roc_curve(y_test_df, y_score, pos_label=trained_pipeline.classes_[1])
    RocCurveDisplay(fpr=fpr, tpr=tpr).plot()
    plt.title(f"AUC: {roc_auc_score(y_test_df, y_score)}")
    plt.tight_layout()
    plt.savefig(os.path.join(pass_success_model_eval_dir, "roc.png"))


def plot_shap(trained_pipeline, x_test_df):
    lgbm_model = trained_pipeline.named_steps["lgbmclassifier"]
    cat_encoder = trained_pipeline.named_steps["addcodes"]
    explainer = shap.TreeExplainer(lgbm_model)
    x_transformed = cat_encoder.transform(x_test_df).sample(10000)
    shap_values = explainer.shap_values(x_transformed)
    shap.summary_plot(
        shap_values[1],
        x_transformed,
        title="SHAP value impact on pass predicted to be successful",
        show=False,
    )
    plt.title("SHAP value impact on pass predicted to be successful")
    plt.tight_layout()
    plt.savefig(os.path.join(pass_success_model_eval_dir, "shap.png"))


def dump_model_evaluation():
    os.makedirs(pass_success_model_eval_dir, exist_ok=True)
    plt.rcParams["figure.figsize"] = (10, 10)

    trained_pipeline = load_trained_model()

    x_test_df = load_all_model_data("x_test")
    y_test_df = load_all_model_data("y_test").reindex(x_test_df.index)

    preds = trained_pipeline.predict(x_test_df)
    pred_probas = trained_pipeline.predict_proba(x_test_df)
    y_score = pred_probas[:, 1]
    pd.Series(get_metrics(y_test_df, preds, y_score)).rename(
        "value"
    ).to_frame().to_html(metric_table_fp)

    plot_success_bars(y_test_df, y_score)
    plot_cm(y_test_df, preds)
    plot_roc(y_test_df, y_score, trained_pipeline)
    plot_shap(trained_pipeline, x_test_df)


eval_pass_model_pe = PipelineElement(
    name="evaluate_pass_success_model",
    runner=dump_model_evaluation,
    output_path=pass_success_model_eval_dir,
    param_list=["seed"],
    dependency_list=[run_pass_model_pe],
)
