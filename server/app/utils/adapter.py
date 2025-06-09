import torch.nn as nn
import torch.cuda

device = "cuda" if torch.cuda.is_available() else "cpu"
embedding_dim = 512
adapter_hidden_dim = 256

class Adapter(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super(Adapter, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x):
        return self.net(x)

adapter = Adapter(embedding_dim, adapter_hidden_dim).to(device)