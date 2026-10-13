"""
deep_models.py
Deep Sequence Baseline: Bi-directional GRU Recurrent Neural Network in PyTorch.

Used to benchmark deep sequence learning against LightGBM tabular models
on the 45-participant CGMacros dataset.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class MetabolicSequenceDataset(Dataset):
    """
    Constructs 2-hour past rolling sequence windows (24 steps x features)
    to predict future glucose targets at +30m (6 steps), +60m (12 steps), and +120m (24 steps).
    """
    def __init__(self, sequences: np.ndarray, targets: np.ndarray):
        self.sequences = torch.tensor(sequences, dtype=torch.float32)
        self.targets = torch.tensor(targets, dtype=torch.float32)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]

class BiGRUMetabolicForecaster(nn.Module):
    """
    Bi-directional Gated Recurrent Unit (BiGRU) with attention pooling
    for sequential multi-horizon glycemic forecasting.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 32, num_layers: int = 2, output_dim: int = 3):
        super(BiGRUMetabolicForecaster, self).__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.15 if num_layers > 1 else 0.0
        )
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, 16),
            nn.Tanh(),
            nn.Linear(16, 1)
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, output_dim)
        )

    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        gru_out, _ = self.gru(x)  # (batch_size, seq_len, hidden_dim * 2)
        
        # Temporal attention pooling
        attn_weights = torch.softmax(self.attention(gru_out), dim=1)  # (batch_size, seq_len, 1)
        context = torch.sum(attn_weights * gru_out, dim=1)  # (batch_size, hidden_dim * 2)
        
        out = self.fc(context)  # (batch_size, output_dim)
        return out

class DeepBaselineTrainer:
    """
    Trains and evaluates the PyTorch BiGRU sequential baseline.
    """
    def __init__(self, input_dim: int = 5, hidden_dim: int = 32, lr: float = 0.003, epochs: int = 25):
        self.device = torch.device("cpu")
        self.model = BiGRUMetabolicForecaster(input_dim=input_dim, hidden_dim=hidden_dim).to(self.device)
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        self.epochs = epochs

    def train_epoch(self, dataloader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        for seqs, targets in dataloader:
            seqs, targets = seqs.to(self.device), targets.to(self.device)
            self.optimizer.zero_grad()
            preds = self.model(seqs)
            loss = self.criterion(preds, targets)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item() * len(seqs)
        return total_loss / len(dataloader.dataset)

    def evaluate(self, dataloader: DataLoader) -> Tuple[float, np.ndarray, np.ndarray]:
        self.model.eval()
        all_preds = []
        all_targets = []
        with torch.no_grad():
            for seqs, targets in dataloader:
                seqs = seqs.to(self.device)
                preds = self.model(seqs)
                all_preds.append(preds.cpu().numpy())
                all_targets.append(targets.numpy())
                
        preds_arr = np.vstack(all_preds)
        targets_arr = np.vstack(all_targets)
        # RMSE across horizons (+30m, +60m, +120m)
        rmse_overall = np.sqrt(np.mean((preds_arr - targets_arr) ** 2))
        return float(rmse_overall), preds_arr, targets_arr
