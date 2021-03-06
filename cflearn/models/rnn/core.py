import torch

from typing import *
from cfdata.tabular import TabularData

from .rnns import rnn_dict
from ..fcnn import FCNN
from ...misc.toolkit import tensor_dict_type


@FCNN.register("rnn")
class RNN(FCNN):
    def __init__(
        self,
        config: Dict[str, Any],
        tr_data: TabularData,
        device: torch.device,
    ):
        super(FCNN, self).__init__(config, tr_data, device)
        input_dimensions = [self.tr_data.processed_dim]
        rnn_hidden_dim = self._rnn_config["hidden_size"]
        input_dimensions += [rnn_hidden_dim] * (self._rnn_num_layers - 1)
        self.rnn_list = torch.nn.ModuleList(
            [self._rnn_base(dim, **self._rnn_config) for dim in input_dimensions]
        )
        self.config["fc_in_dim"] = rnn_hidden_dim
        self._init_fcnn()

    def _init_config(self, tr_data: TabularData):
        super()._init_config(tr_data)
        self._rnn_base = rnn_dict[self.config.setdefault("type", "GRU")]
        self._rnn_config = self.config.setdefault("rnn_config", {})
        self._rnn_config["batch_first"] = True
        self._rnn_num_layers = self._rnn_config.pop("num_layers", 1)
        self._rnn_config["num_layers"] = 1
        self._rnn_config.setdefault("hidden_size", 256)
        self._rnn_config.setdefault("bidirectional", False)

    def forward(self, batch: tensor_dict_type, **kwargs) -> tensor_dict_type:
        x_batch = batch["x_batch"]
        net = self._split_features(x_batch).merge()
        for rnn in self.rnn_list:
            net, final_state = rnn(net, None)
        net = self.mlp(net[..., -1, :])
        return {"predictions": net}


__all__ = ["RNN"]
