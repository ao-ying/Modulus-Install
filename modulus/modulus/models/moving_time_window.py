from typing import Optional, Dict, Tuple
from modulus.key import Key
import copy

import torch
import torch.nn as nn
from torch import Tensor

import modulus.models.layers as layers
from .interpolation import smooth_step_1, smooth_step_2
from modulus.models.arch import Arch

from typing import List


class MovingTimeWindowArch(Arch):
    """
    Moving time window model the keeps track of
    current time window and previous window.

    Parameters
    ----------
    arch : Arch
        Modulus architecture to use for moving time window.
    window_size : float
        Size of the time window. This will be used to slide
        the window forward every iteration.
    """

    def __init__(
        self,
        arch: Arch,
        window_size: float,
    ) -> None:
        output_keys = (
            arch.output_keys
            + [Key(x.name + "_prev_step") for x in arch.output_keys]
            + [Key(x.name + "_prev_step_diff") for x in arch.output_keys]
        )
        super().__init__(
            input_keys=arch.input_keys,
            output_keys=output_keys,
            periodicity=arch.periodicity,
        )

        # set networks for current and prev time window
        self.arch_prev_step = arch
        self.arch = copy.deepcopy(arch)

        # store time window parameters
        self.window_size = window_size
        self.window_location = nn.Parameter(torch.empty(1), requires_grad=False)
        self.reset_parameters()

    def forward(self, in_vars: Dict[str, Tensor]) -> Dict[str, Tensor]:
        with torch.no_grad():
            in_vars["t"] += self.window_location
        y_prev_step = self.arch_prev_step.forward(in_vars)
        y = self.arch.forward(in_vars)
        y_keys = list(y.keys())
        for key in y_keys:
            y_prev = y_prev_step[key]
            y[key + "_prev_step"] = y_prev
            y[key + "_prev_step_diff"] = y[key] - y_prev
        return y

    def move_window(self):
        self.window_location.data += self.window_size
        for param, param_prev_step in zip(
            self.arch.parameters(), self.arch_prev_step.parameters()
        ):
            param_prev_step.data = param.detach().clone().data
            param_prev_step.requires_grad = False

    def reset_parameters(self) -> None:
        nn.init.constant_(self.window_location, 0)
