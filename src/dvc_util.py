import random

from dataclasses import dataclass, field
from typing import Optional, List, Iterable, Union

from invoke import task
import numpy as np


@dataclass
class PipelineElement:

    element_dic = {}

    name: str
    runner: callable
    output_path: Optional[str] = None
    param_list: list = field(default_factory=list)
    dependency_list: List[Union[str, "PipelineElement"]] = field(default_factory=list)

    def __post_init__(self):
        self.element_dic[self.name] = self

    def run(self, loaded_params: dict):

        parsed_params = {}
        _level_params = loaded_params.get(self.name, {})
        for k in self.param_list:
            if k == "seed":
                v = loaded_params[k]
                np.random.seed(v)
                random.seed(v)
            else:
                parsed_params[k] = _level_params[k]

        self.runner(**parsed_params)

    def get_invoke_task(self):
        param_str = ",".join(
            [(".".join([self.name, p]) if p != "seed" else p) for p in self.param_list]
        )
        if param_str:
            param_str = "-p " + param_str
        dep_str = " -d ".join(
            [
                (dep.output_path if isinstance(dep, PipelineElement) else dep)
                for dep in self.dependency_list
            ]
        )
        if dep_str:
            dep_str = " -d " + dep_str
        out_str = f"-o {self.output_path}" if self.output_path else ""
        command = " ".join(
            [
                f"dvc run -n {self.name} --force",
                param_str,
                dep_str,
                out_str,
                f"python -m src {self.name}",
            ]
        )

        @task(name=self.name)
        def _task(c):
            c.run(command)

        return _task

    @classmethod
    def get_inst(cls, name: str) -> "PipelineElement":
        return cls.element_dic[name]

    @classmethod
    def all_instances(cls) -> Iterable["PipelineElement"]:
        return cls.element_dic.values()
