import os

import joblib
import lightgbm as lgbm
from sklearn.pipeline import make_pipeline

from .prepare_data_for_modelling import (
    AddCodes,
    categ_vals,
    load_all_model_data,
    prep_pass_model_pe,
)
from ..dvc_util import PipelineElement

model_file_path = os.path.join("models", "pass_success_lgbm.joblib")


def train_and_dump_model(split):
    joblib.dump(get_trained_model(split), model_file_path)


def load_trained_model():
    return joblib.load(model_file_path)


def get_trained_model(fraction, verbose=True):
    x_train_df = load_all_model_data("x_train")
    y_train_df = load_all_model_data("y_train").reindex(x_train_df.index)

    __X = x_train_df.sample(frac=fraction)
    __y = y_train_df.reindex(__X.index)

    add_codes = AddCodes(categ_vals)
    model = lgbm.LGBMClassifier()
    pipeline = make_pipeline(add_codes, model, verbose=verbose)

    return pipeline.fit(__X, __y)


run_pass_model_pe = PipelineElement(
    name="train_pass_success_model",
    runner=train_and_dump_model,
    output_path=model_file_path,
    param_list=["split", "seed"],
    dependency_list=[prep_pass_model_pe],
)
