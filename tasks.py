from invoke import task

from src import PipelineElement

tasks = []
for pe in PipelineElement.all_instances():
    globals()[pe.name] = pe.get_invoke_task()


@task
def clean(c):
    for _pe in PipelineElement.all_instances():
        c.run(f"rm -rf {_pe.output_path}")

"""
dvc run -n train \
          -p train.seed, train.n_estimators \
          -d src/train.py -d data/features \
          -o model.pkl \
          python src/train.py data/features model.pkl
"""
