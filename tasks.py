from invoke import task

from src import PipelineElement

tasks = []
for pe in PipelineElement.all_instances():
    globals()[pe.name] = pe.get_invoke_task()


@task
def clean(c):
    for _pe in PipelineElement.all_instances():
        c.run(f"rm -rf {_pe.output_path}")


@task
def dag(c):
    c.run("dvc dag --dot > dvcdag.dot")
    c.run("dvc dag > reports/dvcdag.txt")
    c.run("dot -Tpng dvcdag.dot -o dvcdag.png")
    c.run("rm dvcdag.dot")
