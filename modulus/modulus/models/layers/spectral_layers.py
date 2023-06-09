from typing import List
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor


class SpectralConv1d(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, modes1: int):
        super().__init__()

        """
        1D Fourier layer. It does FFT, linear transform, and Inverse FFT.    
        """

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = (
            modes1  # Number of Fourier modes to multiply, at most floor(N/2) + 1
        )

        self.scale = 1 / (in_channels * out_channels)
        self.weights1 = nn.Parameter(
            torch.empty(in_channels, out_channels, self.modes1, 2)
        )
        self.reset_parameters()

    # Complex multiplication
    def compl_mul1d(
        self,
        input: Tensor,
        weights: Tensor,
    ) -> Tensor:
        # (batch, in_channel, x ), (in_channel, out_channel, x) -> (batch, out_channel, x)
        cweights = torch.view_as_complex(weights)
        return torch.einsum("bix,iox->box", input, cweights)

    def forward(self, x: Tensor) -> Tensor:
        bsize = x.shape[0]
        # Compute Fourier coeffcients up to factor of e^(- something constant)
        x_ft = torch.fft.rfft(x)

        # Multiply relevant Fourier modes
        out_ft = torch.zeros(
            bsize,
            self.out_channels,
            x.size(-1) // 2 + 1,
            device=x.device,
            dtype=torch.cfloat,
        )
        out_ft[:, :, : self.modes1] = self.compl_mul1d(
            x_ft[:, :, : self.modes1],
            self.weights1,
        )

        # Return to physical space
        x = torch.fft.irfft(out_ft, n=x.size(-1))
        return x

    def reset_parameters(self):
        self.weights1.data = self.scale * torch.rand(self.weights1.data.shape)


class SpectralConv2d(nn.Module):
    def __init__(self, in_channels, out_channels, modes1, modes2):
        super().__init__()

        """
        2D Fourier layer. It does FFT, linear transform, and Inverse FFT.    
        """

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = (
            modes1  # Number of Fourier modes to multiply, at most floor(N/2) + 1
        )
        self.modes2 = modes2

        self.scale = 1 / (in_channels * out_channels)
        self.weights1 = nn.Parameter(
            torch.empty(in_channels, out_channels, self.modes1, self.modes2, 2)
        )
        self.weights2 = nn.Parameter(
            torch.empty(in_channels, out_channels, self.modes1, self.modes2, 2)
        )
        self.reset_parameters()

    # Complex multiplication
    def compl_mul2d(self, input: Tensor, weights: Tensor) -> Tensor:
        # (batch, in_channel, x, y), (in_channel, out_channel, x, y) -> (batch, out_channel, x, y)
        cweights = torch.view_as_complex(weights)
        return torch.einsum("bixy,ioxy->boxy", input, cweights)

    def forward(self, x: Tensor) -> Tensor:
        batchsize = x.shape[0]
        # Compute Fourier coeffcients up to factor of e^(- something constant)
        x_ft = torch.fft.rfft2(x)

        # Multiply relevant Fourier modes
        out_ft = torch.zeros(
            batchsize,
            self.out_channels,
            x.size(-2),
            x.size(-1) // 2 + 1,
            dtype=torch.cfloat,
            device=x.device,
        )
        out_ft[:, :, : self.modes1, : self.modes2] = self.compl_mul2d(
            x_ft[:, :, : self.modes1, : self.modes2],
            self.weights1,
        )
        out_ft[:, :, -self.modes1 :, : self.modes2] = self.compl_mul2d(
            x_ft[:, :, -self.modes1 :, : self.modes2],
            self.weights2,
        )

        # Return to physical space
        x = torch.fft.irfft2(out_ft, s=(x.size(-2), x.size(-1)))
        return x

    def reset_parameters(self):
        self.weights1.data = self.scale * torch.rand(self.weights1.data.shape)
        self.weights2.data = self.scale * torch.rand(self.weights2.data.shape)


class SpectralConv3d(nn.Module):
    def __init__(self, in_channels, out_channels, modes1, modes2, modes3):
        super().__init__()

        """
        3D Fourier layer. It does FFT, linear transform, and Inverse FFT.    
        """

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = (
            modes1  # Number of Fourier modes to multiply, at most floor(N/2) + 1
        )
        self.modes2 = modes2
        self.modes3 = modes3

        self.scale = 1 / (in_channels * out_channels)
        self.weights1 = nn.Parameter(
            torch.empty(
                in_channels, out_channels, self.modes1, self.modes2, self.modes3, 2
            )
        )
        self.weights2 = nn.Parameter(
            torch.empty(
                in_channels, out_channels, self.modes1, self.modes2, self.modes3, 2
            )
        )
        self.weights3 = nn.Parameter(
            torch.empty(
                in_channels, out_channels, self.modes1, self.modes2, self.modes3, 2
            )
        )
        self.weights4 = nn.Parameter(
            torch.empty(
                in_channels, out_channels, self.modes1, self.modes2, self.modes3, 2
            )
        )
        self.reset_parameters()

    # Complex multiplication
    def compl_mul3d(
        self,
        input: Tensor,
        weights: Tensor,
    ) -> Tensor:
        # (batch, in_channel, x, y, z), (in_channel, out_channel, x, y, z) -> (batch, out_channel, x, y, z)
        cweights = torch.view_as_complex(weights)
        return torch.einsum("bixyz,ioxyz->boxyz", input, cweights)

    def forward(self, x: Tensor) -> Tensor:
        batchsize = x.shape[0]
        # Compute Fourier coeffcients up to factor of e^(- something constant)
        x_ft = torch.fft.rfftn(x, dim=[-3, -2, -1])

        # Multiply relevant Fourier modes
        out_ft = torch.zeros(
            batchsize,
            self.out_channels,
            x.size(-3),
            x.size(-2),
            x.size(-1) // 2 + 1,
            dtype=torch.cfloat,
            device=x.device,
        )
        out_ft[:, :, : self.modes1, : self.modes2, : self.modes3] = self.compl_mul3d(
            x_ft[:, :, : self.modes1, : self.modes2, : self.modes3], self.weights1
        )
        out_ft[:, :, -self.modes1 :, : self.modes2, : self.modes3] = self.compl_mul3d(
            x_ft[:, :, -self.modes1 :, : self.modes2, : self.modes3], self.weights2
        )
        out_ft[:, :, : self.modes1, -self.modes2 :, : self.modes3] = self.compl_mul3d(
            x_ft[:, :, : self.modes1, -self.modes2 :, : self.modes3], self.weights3
        )
        out_ft[:, :, -self.modes1 :, -self.modes2 :, : self.modes3] = self.compl_mul3d(
            x_ft[:, :, -self.modes1 :, -self.modes2 :, : self.modes3], self.weights4
        )

        # Return to physical space
        x = torch.fft.irfftn(out_ft, s=(x.size(-3), x.size(-2), x.size(-1)))
        return x

    def reset_parameters(self):
        self.weights1.data = self.scale * torch.rand(self.weights1.data.shape)
        self.weights2.data = self.scale * torch.rand(self.weights2.data.shape)
        self.weights3.data = self.scale * torch.rand(self.weights3.data.shape)
        self.weights4.data = self.scale * torch.rand(self.weights4.data.shape)


# ==========================================
# Utils for PINO exact gradients
# ==========================================
def fourier_derivatives(x: Tensor, l: List[float]) -> Tuple[Tensor, Tensor]:
    # check that input shape maches domain length
    assert len(x.shape) - 2 == len(l), "input shape doesn't match domain dims"

    # set pi from numpy
    pi = float(np.pi)

    # get needed dims
    batchsize = x.size(0)
    n = x.shape[2:]
    dim = len(l)

    # get device
    device = x.device

    # compute fourier transform
    x_h = torch.fft.fftn(x, dim=list(range(2, dim + 2)))

    # make wavenumbers
    k_x = []
    for i, nx in enumerate(n):
        k_x.append(
            torch.cat(
                (
                    torch.arange(start=0, end=nx // 2, step=1, device=device),
                    torch.arange(start=-nx // 2, end=0, step=1, device=device),
                ),
                0,
            ).reshape((i + 2) * [1] + [nx] + (dim - i - 1) * [1])
        )

    # compute laplacian in fourier space
    j = torch.complex(
        torch.tensor([0.0], device=device), torch.tensor([1.0], device=device)
    )  # Cuda graphs does not work here
    wx_h = [j * k_x_i * x_h * (2 * pi / l[i]) for i, k_x_i in enumerate(k_x)]
    wxx_h = [
        j * k_x_i * wx_h_i * (2 * pi / l[i])
        for i, (wx_h_i, k_x_i) in enumerate(zip(wx_h, k_x))
    ]

    # inverse fourier transform out
    wx = torch.cat(
        [torch.fft.ifftn(wx_h_i, dim=list(range(2, dim + 2))).real for wx_h_i in wx_h],
        dim=1,
    )
    wxx = torch.cat(
        [
            torch.fft.ifftn(wxx_h_i, dim=list(range(2, dim + 2))).real
            for wxx_h_i in wxx_h
        ],
        dim=1,
    )
    return (wx, wxx)


@torch.jit.ignore
def calc_latent_derivatives(
    x: Tensor, domain_length: List[int] = 2
) -> Tuple[List[Tensor], List[Tensor]]:

    dim = len(x.shape) - 2
    # Compute derivatives of latent variables via fourier methods
    # Padd domain by factor of 2 for non-periodic domains
    padd = [(i - 1) // 2 for i in list(x.shape[2:])]
    # Scale domain length by padding amount
    domain_length = [
        domain_length[i] * (2 * padd[i] + x.shape[i + 2]) / x.shape[i + 2]
        for i in range(dim)
    ]
    padding = padd + padd
    x_p = F.pad(x, padding, mode="replicate")
    dx, ddx = fourier_derivatives(x_p, domain_length)
    # Trim padded domain
    if len(x.shape) == 3:
        dx = dx[..., padd[0] : -padd[0]]
        ddx = ddx[..., padd[0] : -padd[0]]
        dx_list = torch.split(dx, x.shape[1], dim=1)
        ddx_list = torch.split(ddx, x.shape[1], dim=1)
    elif len(x.shape) == 4:
        dx = dx[..., padd[0] : -padd[0], padd[1] : -padd[1]]
        ddx = ddx[..., padd[0] : -padd[0], padd[1] : -padd[1]]
        dx_list = torch.split(dx, x.shape[1], dim=1)
        ddx_list = torch.split(ddx, x.shape[1], dim=1)
    else:
        dx = dx[..., padd[0] : -padd[0], padd[1] : -padd[1], padd[2] : -padd[2]]
        ddx = ddx[..., padd[0] : -padd[0], padd[1] : -padd[1], padd[2] : -padd[2]]
        dx_list = torch.split(dx, x.shape[1], dim=1)
        ddx_list = torch.split(ddx, x.shape[1], dim=1)

    return dx_list, ddx_list


def first_order_pino_grads(
    u: Tensor,
    ux: List[Tensor],
    weights_1: Tensor,
    weights_2: Tensor,
    bias_1: Tensor,
) -> Tuple[Tensor]:
    # dim for einsum
    dim = len(u.shape) - 2
    dim_str = "xyz"[:dim]

    # compute first order derivatives of input
    # compute first layer
    if dim == 1:
        u_hidden = F.conv1d(u, weights_1, bias_1)
    elif dim == 2:
        weights_1 = weights_1.unsqueeze(-1)
        weights_2 = weights_2.unsqueeze(-1)
        u_hidden = F.conv2d(u, weights_1, bias_1)
    elif dim == 3:
        weights_1 = weights_1.unsqueeze(-1).unsqueeze(-1)
        weights_2 = weights_2.unsqueeze(-1).unsqueeze(-1)
        u_hidden = F.conv3d(u, weights_1, bias_1)

    # compute derivative hidden layer
    diff_tanh = 1 / torch.cosh(u_hidden) ** 2

    # compute diff(f(g))
    diff_fg = torch.einsum(
        "mi" + dim_str + ",bm" + dim_str + ",km" + dim_str + "->bi" + dim_str,
        weights_1,
        diff_tanh,
        weights_2,
    )

    # compute diff(f(g)) * diff(g)
    vx = [
        torch.einsum("bi" + dim_str + ",bi" + dim_str + "->b" + dim_str, diff_fg, w)
        for w in ux
    ]
    vx = [torch.unsqueeze(w, dim=1) for w in vx]

    return vx


def second_order_pino_grads(
    u: Tensor,
    ux: Tensor,
    uxx: Tensor,
    weights_1: Tensor,
    weights_2: Tensor,
    bias_1: Tensor,
) -> Tuple[Tensor]:
    # dim for einsum
    dim = len(u.shape) - 2
    dim_str = "xyz"[:dim]

    # compute first order derivatives of input
    # compute first layer
    if dim == 1:
        u_hidden = F.conv1d(u, weights_1, bias_1)
    elif dim == 2:
        weights_1 = weights_1.unsqueeze(-1)
        weights_2 = weights_2.unsqueeze(-1)
        u_hidden = F.conv2d(u, weights_1, bias_1)
    elif dim == 3:
        weights_1 = weights_1.unsqueeze(-1).unsqueeze(-1)
        weights_2 = weights_2.unsqueeze(-1).unsqueeze(-1)
        u_hidden = F.conv3d(u, weights_1, bias_1)

    # compute derivative hidden layer
    diff_tanh = 1 / torch.cosh(u_hidden) ** 2

    # compute diff(f(g))
    diff_fg = torch.einsum(
        "mi" + dim_str + ",bm" + dim_str + ",km" + dim_str + "->bi" + dim_str,
        weights_1,
        diff_tanh,
        weights_2,
    )

    # compute diagonal of hessian
    # double derivative of hidden layer
    diff_diff_tanh = -2 * diff_tanh * torch.tanh(u_hidden)

    # compute diff(g) * hessian(f) * diff(g)
    vxx1 = [
        torch.einsum(
            "bi"
            + dim_str
            + ",mi"
            + dim_str
            + ",bm"
            + dim_str
            + ",mj"
            + dim_str
            + ",bj"
            + dim_str
            + "->b"
            + dim_str,
            w,
            weights_1,
            weights_2 * diff_diff_tanh,
            weights_1,
            w,
        )
        for w in ux
    ]  # (b,x,y,t)

    # compute diff(f) * hessian(g)
    vxx2 = [
        torch.einsum("bi" + dim_str + ",bi" + dim_str + "->b" + dim_str, diff_fg, w)
        for w in uxx
    ]
    vxx = [torch.unsqueeze(a + b, dim=1) for a, b in zip(vxx1, vxx2)]

    return vxx

    # @torch.jit.ignore
    # def calc_derivatives(
    #     self,
    #     x: Tensor, # Latent variables
    #     y: Dict[str, Tensor], # Output vars
    #     x_list: List[Tensor],
    #     dx_list: List[Tensor],
    #     ddx_list: List[Tensor],
    #     dim: int = 2,
    # ) -> Dict[str, Tensor]:

    #     # Loop through output variables independently
    #     y_out: Dict[str, Tensor] = {}
    #     for key in self.output_key_dict.keys():
    #         # First-order grads with back-prop
    #         outputs: List[torch.Tensor] = [y[key]]
    #         inputs: List[torch.Tensor] = [x]
    #         grad_outputs: List[Optional[torch.Tensor]] = [
    #             torch.ones_like(y[key], device=y[key].device)
    #         ]
    #         dydzeta = torch.autograd.grad(
    #             outputs,
    #             inputs,
    #             grad_outputs=grad_outputs,
    #             create_graph=True,
    #             retain_graph=True,
    #         )[0]
    #         for i, axis in enumerate(["x", "y", "z"]):
    #             if f"{key}__{axis}" in self.derivative_key_dict:
    #                 # Chain rule: g'(x)*f'(g(x))
    #                 y_out[f"{key}__{axis}"] = torch.sum(
    #                     dx_list[i] * dydzeta, dim=1, keepdim=True
    #                 )

    #         # Calc second order if needed
    #         if self.calc_ddx:
    #             y_ddx = self.calc_second_order_derivatives(
    #                 x, key, x_list, dx_list, ddx_list, dydzeta, dim
    #             )
    #             y_out.update(y_ddx)

    #     return y_out

    # @torch.jit.ignore
    # def calc_second_order_derivatives(
    #     self,
    #     x: Tensor,
    #     key: str,
    #     x_list: List[Tensor],
    #     dx_list: List[Tensor],
    #     ddx_list: List[Tensor],
    #     dydzeta: Tensor,
    #     dim: int = 2,
    # ) -> Dict[str, Tensor]:

    #     # Brute force Hessian calc with auto-diff
    #     hessian = torch.zeros(
    #         dydzeta.shape[0],
    #         dydzeta.shape[1],
    #         dydzeta.shape[1],
    #         dydzeta.shape[2],
    #         dydzeta.shape[3],
    #     ).to(x.device)
    #     grad_outputs: List[Optional[torch.Tensor]] = [
    #         torch.ones_like(dydzeta[:, :1], device=dydzeta.device)
    #     ]
    #     for i in range(dydzeta.shape[1]):
    #         for j in range(i, dydzeta.shape[1]):
    #             dyydzeta = torch.autograd.grad(
    #                 dydzeta[:, j : j + 1],
    #                 x_list[i],
    #                 grad_outputs=grad_outputs,
    #                 retain_graph=True,
    #                 allow_unused=True,
    #             )[0]
    #             if dyydzeta is not None:
    #                 hessian[:, i, j] = dyydzeta.squeeze(1)
    #                 hessian[:, j, i] = dyydzeta.squeeze(1)

    #     # Loop through output variables independently
    #     y_out: Dict[str, Tensor] = {}
    #     # Add needed derivatives
    #     for i, axis in enumerate(["x", "y", "z"]):
    #         if f"{key}__{axis}__{axis}" in self.derivative_key_dict:
    #             dim_str = "ijk"[:dim]
    #             # Chain rule: g''(x)*f'(g(x)) + g'(x)*f''(g(x))*g'(x)
    #             y_out[f"{key}__{axis}__{axis}"] = torch.sum(
    #                 ddx_list[i] * dydzeta, dim=1, keepdim=True
    #             ) + torch.einsum(
    #                 f"bm{dim_str},bmn{dim_str},bn{dim_str}->b{dim_str}",
    #                 dx_list[i],
    #                 hessian,
    #                 dx_list[i],
    #             ).unsqueeze(
    #                 1
    #             )

    #     return y_out
