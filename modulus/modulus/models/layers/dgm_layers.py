from typing import Callable
from typing import Optional
from typing import Union

import torch
import torch.nn as nn
from torch import Tensor

from .weight_norm import WeightNormLinear
from .activation import Activation, get_activation_fn


class DGMLayer(nn.Module):
    def __init__(
        self,
        in_features_1: int,
        in_features_2: int,
        out_features: int,
        activation_fn: Union[
            Activation, Callable[[Tensor], Tensor]
        ] = Activation.IDENTITY,
        weight_norm: bool = False,
        activation_par: Optional[nn.Parameter] = None,
    ) -> None:
        super().__init__()

        self.activation_fn = activation_fn
        self.callable_activation_fn = get_activation_fn(activation_fn)
        self.weight_norm = weight_norm
        self.activation_par = activation_par

        if weight_norm:
            self.linear_1 = WeightNormLinear(in_features_1, out_features, bias=False)
            self.linear_2 = WeightNormLinear(in_features_2, out_features, bias=False)
        else:
            self.linear_1 = nn.Linear(in_features_1, out_features, bias=False)
            self.linear_2 = nn.Linear(in_features_2, out_features, bias=False)
        self.bias = nn.Parameter(torch.empty(out_features))
        self.reset_parameters()

    def exec_activation_fn(self, x: Tensor) -> Tensor:
        return self.callable_activation_fn(x)

    def reset_parameters(self) -> None:
        nn.init.xavier_uniform_(self.linear_1.weight)
        nn.init.xavier_uniform_(self.linear_2.weight)
        nn.init.constant_(self.bias, 0)
        if self.weight_norm:
            nn.init.constant_(self.linear_1.weight_g, 1.0)
            nn.init.constant_(self.linear_2.weight_g, 1.0)

    def forward(self, input_1: Tensor, input_2: Tensor) -> Tensor:
        x = self.linear_1(input_1) + self.linear_2(input_2) + self.bias
        if self.activation_fn is not Activation.IDENTITY:
            if self.activation_par is None:
                x = self.exec_activation_fn(x)
            else:
                x = self.exec_activation_fn(self.activation_par * x)
        return x
