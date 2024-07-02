#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

from argparse import ArgumentParser, Namespace
import sys
import os

class GroupParams:
    pass

class ParamGroup:
    def __init__(self, parser: ArgumentParser, name : str, fill_none = False):
        print("DISREGARD THIS Class of self is", self.__class__)
        group = parser.add_argument_group(name)
        # creates a new argument group in the parser
        # used to logically group arguments that belong together.
        for key, value in vars(self).items():
            # iterates over all the arguments of the class
            # add shorthand for arguments that start with _
            shorthand = False
            if key.startswith("_"):
                shorthand = True
                key = key[1:]
                # stores key name without _
            t = type(value)
            value = value if not fill_none else None 
            if shorthand:
                if t == bool:
                    # if boolean type then passing --arg or -a will set it to True 
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, action="store_true")
                else:
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, type=t)
            else:
                if t == bool:
                    # if boolean type then passing --arg will set it to True
                    group.add_argument("--" + key, default=value, action="store_true")
                else:
                    group.add_argument("--" + key, default=value, type=t)

    def extract(self, args: Namespace):
        # self is an instance of some subclass
        # args is an instance of Namespace class
        group = GroupParams()
        for arg in vars(args).items():
            # vars(args) is dict
            # vars(args).items() is a list of tuples
            # arg is a tuple of key and value
            if arg[0] in vars(self) or ("_" + arg[0]) in vars(self):
                setattr(group, arg[0], arg[1])
        # Essentially return arguments for a group
        return group

class ModelParams(ParamGroup): 
# inherits from ParamGroup class
    def __init__(self, parser, sentinel=False):
        # childs __init__ method overrides the parent class __init__ method
        # to use the parent class __init__ method, we need to call it explicitly in the end
        # main arguments of the model
        # self is an instance of ModelParams class
        self.sh_degree = 3
        self._source_path = ""
        self._model_path = ""
        self._images = "images"
        self._resolution = -1
        self._white_background = False
        self.data_device = "cuda"
        self.eval = False
        # arguements begin with _ will also have an option for shorthand 
        super().__init__(parser, "Loading Parameters", sentinel)
        # in the end we want to add all arguments to parser

    def extract(self, args : Namespace):
        # self is an instance of ModelParams class
        # args is an instance of Namespace class
        g = super().extract(args)
        g.source_path = os.path.abspath(g.source_path)
        return g

class PipelineParams(ParamGroup):
    # inherits ParamGroup class
    # childs __init__ method overrides ParamGroup class __init__ method
    # need to call it explicitly
    def __init__(self, parser : ArgumentParser):
        # self is an instance of PipelineParams class
        self.convert_SHs_python = False
        self.compute_cov3D_python = False
        self.debug = False
        # in the end we add all arguments to parser
        super().__init__(parser, "Pipeline Parameters")

class OptimizationParams(ParamGroup):
    # inherits ParamGroup class
    # childs __init__ method overrides ParamGroup class __init__ method
    # need to call it explicitly 
    def __init__(self, parser : ArgumentParser):
        # self is an instance OptimizationParams class
        self.iterations = 30_000
        self.position_lr_init = 0.00016
        self.position_lr_final = 0.0000016
        self.position_lr_delay_mult = 0.01
        self.position_lr_max_steps = 30_000
        self.feature_lr = 0.0025
        self.opacity_lr = 0.05
        self.scaling_lr = 0.005
        self.rotation_lr = 0.001
        self.percent_dense = 0.01
        self.lambda_dssim = 0.2
        self.densification_interval = 100
        self.opacity_reset_interval = 3000
        # remove transparent splats after this many iterations
        self.densify_from_iter = 500
        # densify the splats from this iteration
        self.densify_until_iter = 15_000
        # densify the splats until this iteration
        self.densify_grad_threshold = 0.0002
        self.random_background = False
        # in the end we add all arguments to parser
        super().__init__(parser, "Optimization Parameters")

def get_combined_args(parser : ArgumentParser):
    cmdlne_string = sys.argv[1:]
    cfgfile_string = "Namespace()"
    args_cmdline = parser.parse_args(cmdlne_string)

    try:
        cfgfilepath = os.path.join(args_cmdline.model_path, "cfg_args")
        print("Looking for config file in", cfgfilepath)
        with open(cfgfilepath) as cfg_file:
            print("Config file found: {}".format(cfgfilepath))
            cfgfile_string = cfg_file.read()
    except TypeError:
        print("Config file not found at")
        pass
    args_cfgfile = eval(cfgfile_string)

    merged_dict = vars(args_cfgfile).copy()
    for k,v in vars(args_cmdline).items():
        if v != None:
            merged_dict[k] = v
    return Namespace(**merged_dict)
