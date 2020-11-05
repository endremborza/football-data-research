import sys

import yaml

from src import PipelineElement

all_params = yaml.safe_load(open("params.yaml"))

PipelineElement.get_inst(sys.argv[1]).run(all_params)
