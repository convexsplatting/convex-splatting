#
# The original code is under the following copyright:
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE_GS.md file.
#
# For inquiries contact george.drettakis@inria.fr
#
# The modifications of the code are under the following copyright:
# Copyright (C) 2024, University of Liege, KAUST and University of Oxford
# TELIM research group, http://www.telecom.ulg.ac.be/
# IVUL research group, https://ivul.kaust.edu.sa/
# VGG research group, https://www.robots.ox.ac.uk/~vgg/
# All rights reserved.
# The modifications are under the LICENSE.md file.
#
# For inquiries contact jan.held@uliege.be
#

from argparse import ArgumentParser, Namespace
import sys
import os

class GroupParams:
    pass

class ParamGroup:
    def __init__(self, parser: ArgumentParser, name : str, fill_none = False):
        group = parser.add_argument_group(name)
        for key, value in vars(self).items():
            shorthand = False
            if key.startswith("_"):
                shorthand = True
                key = key[1:]
            t = type(value)
            value = value if not fill_none else None
            if shorthand:
                if t == bool:
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, action="store_true")
                else:
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, type=t)
            else:
                if t == bool:
                    group.add_argument("--" + key, default=value, action="store_true")
                else:
                    group.add_argument("--" + key, default=value, type=t)

    def extract(self, args):
        group = GroupParams()
        for arg in vars(args).items():
            if arg[0] in vars(self) or ("_" + arg[0]) in vars(self):
                setattr(group, arg[0], arg[1])
        return group

class ModelParams(ParamGroup): 
    def __init__(self, parser, sentinel=False):
        self.sh_degree = 3
        self._source_path = ""
        self._model_path = ""
        self._images = "images"
        self._resolution = -1
        self._white_background = False
        self.data_device = "cuda"
        self.eval = False
        super().__init__(parser, "Loading Parameters", sentinel)

    def extract(self, args):
        g = super().extract(args)
        g.source_path = os.path.abspath(g.source_path)
        return g

class PipelineParams(ParamGroup):
    def __init__(self, parser):
        self.convert_SHs_python = False
        self.compute_cov3D_python = False
        self.depth_ratio = 1.0
        self.debug = False
        super().__init__(parser, "Pipeline Parameters")

class OptimizationParams(ParamGroup):
    def __init__(self, parser):
        self.iterations = 30_000
        self.position_lr_delay_mult = 0.01
        self.position_lr_max_steps = 30_000
        self.feature_lr = 0.0025
        self.opacity_lr = 0.01
        self.lambda_dssim = 0.2
        self.densification_interval = 200
        #self.opacity_reset_interval = 10000
        self.densify_from_iter = 500
        self.densify_until_iter = 15_000
        self.densify_grad_threshold = 0.000004
        self.random_background = False
        self.reset_opacity_until = 9000
        self.opacity_reset = 0.2
        self.opacity_reset_interval = 3000
        self.remove_size_threshold = 0.3
        self.min_opacity = 0.03
        self.mask_threshold = 0.01
        self.lr_mask = 0.01
        self.lr_delta = 0.005
        self.lr_sigma = 0.0045
        self.lr_convex_points_init = 0.0005
        self.lr_convex_points_final = 0.000005

        self.nb_points = 6
        self.convex_size = 1.2
        self.set_opacity = 0.1
        self.set_delta = 0.1

        self.opacity_cloning = 0.5
        self.delta_scaling_cloning = 1
        self.shifting_cloning = 1
        self.densify_grad_threshold = 0.000025
        self.set_sigma = 0.00095
        self.sigma_scaling_cloning = 0.88
        self.scaling_cloning = 0.63

        self.densify_until_iter = 9000
        self.reset_opacity_unil = 5000

        super().__init__(parser, "Optimization Parameters")

def adapt(opt, light, outdoor):
    if not light and outdoor:
        opt.set_sigma = 0.001 
        opt.densify_grad_threshold = 0.000001
        opt.lr_sigma = 0.004 
        opt.reset_opacity_unil = 18000
        opt.scaling_cloning = 0.6
    if not light and not outdoor:
        opt.sigma_scaling_cloning = 0.85 
        opt.set_sigma = 0.0009 
        opt.densify_grad_threshold = 0.000006 
        opt.mask_threshold = 0.02 
        opt.scaling_cloning = 0.7 
        opt.lr_convex_points_init = 0.0004 
        opt.lr_convex_points_final = 0.000004 
        opt.densify_until_iter = 9500 
    return opt



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