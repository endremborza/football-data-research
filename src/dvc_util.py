import random
import traceback
import os
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Union

import numpy as np
from invoke import task


@dataclass
class PipelineElement:

    element_dic = {}

    name: str
    runner: callable
    output_path: Optional[str] = None
    param_list: list = field(default_factory=list)
    dependency_list: List[Union[str, "PipelineElement"]] = field(default_factory=list)
    out_nonchache: Optional[str] = None

    def __post_init__(self):
        fs = traceback.extract_stack()[-3]
        relpath = os.path.relpath(fs.filename, os.getcwd())
        self.dependency_list.insert(0, relpath)
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
        out_noncache_str = f"-O {self.out_nonchache}" if self.out_nonchache else ""
        command = " ".join(
            [
                f"dvc run -n {self.name} --force",
                param_str,
                dep_str,
                out_str,
                out_noncache_str,
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
