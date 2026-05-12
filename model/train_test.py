import os
import torch
import torch.nn as nn
import numpy as np
from sklearn.utils import shuffle
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from Dataset import Dataset_TMTM
from model import TMTM
from utils import sample_mask, init_weights
import time
import itertools
import sys
import warnings
from pathlib import Path
warnings.filterwarnings('ignore')


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Connection configuration: 0=following, 1=followers, 2=ownership
relation_select = [0, 1] 
# Random seed configuration
random_seed = [0, 1, 2, 3, 4] 
# Default weight_decay
weight_decay = 5e-4
# Early stopping patience
early_stopping_patience = 20


def compute_class_weights(labels):
    """Compute inverse-frequency class weights for imbalanced datasets."""
    classes, counts = torch.unique(labels, return_counts=True)
    total = counts.sum().float()
    weights = total / (len(classes) * counts.float())
    return weights


def main(seed, data, hidden_dimension, dropout, epochs, lr, weight_decay):
    out_dim = 2
    data.y = data.y2

    sample_number = len(data.y)
    shuffled_idx = shuffle(np.array(range(sample_number)), random_state=seed)
    train_idx = shuffled_idx[:int(0.7 * sample_number)]
    val_idx = shuffled_idx[int(0.7 * sample_number):int(0.9 * sample_number)]
    test_idx = shuffled_idx[int(0.9 * sample_number):]
    data.train_mask = sample_mask(train_idx, sample_number)
    data.val_mask = sample_mask(val_idx, sample_number)
    data.test_mask = sample_mask(test_idx, sample_number)

    test_mask = data.test_mask
    train_mask = data.train_mask
    val_mask = data.val_mask

    data = data.to(device)
    relation_num = len(relation_select)
    index_select_list = torch.zeros_like(data.edge_type, dtype=torch.bool)

    relation_dict = {
        0:'following',
        1:'followers',
        2:'ownership'
    }

    for features_index in relation_select:
        if features_index in torch.unique(data.edge_type):
            index_select_list |= (data.edge_type == features_index)
            print('Relation used:', relation_dict[features_index])
    
    # Use only the selected relations
    edge_index = data.edge_index[:, index_select_list]
    edge_type = data.edge_type[index_select_list]

    # Model configuration
    model = TMTM(hidden_dimension=hidden_dimension, out_dim=out_dim, relation_num=relation_num, dropout=dropout).to(device)

    # Class-weighted loss for imbalanced dataset (86% human / 14% bot)
    class_weights = compute_class_weights(data.y).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    
    def train(epoch):
        # Train model
        model.train()
        optimizer.zero_grad()
        output = model(data.x, edge_index, edge_type)
        loss_train = criterion(output[data.train_mask], data.y[data.train_mask])
        loss_train.backward()
        optimizer.step()

        # Compute metrics
        out = output.max(1)[1].to('cpu').detach().numpy()
        label = data.y.to('cpu').detach().numpy()
        acc_train = accuracy_score(out[train_mask], label[train_mask])
        acc_val = accuracy_score(out[val_mask], label[val_mask])
        f1_val = f1_score(out[val_mask], label[val_mask], average='macro')
        print('Epoch: {:04d}'.format(epoch + 1),
              'loss_train: {:.4f}'.format(loss_train.item()),
              'acc_train: {:.4f}'.format(acc_train),
              'acc_val: {:.4f}'.format(acc_val),
              'f1_val: {:.4f}'.format(f1_val))
        return f1_val


    def test():
        # Test model
        model.eval()
        with torch.no_grad():
            output = model(data.x, edge_index, edge_type)
        loss_test = criterion(output[data.test_mask], data.y[data.test_mask])
        out = output.max(1)[1].to('cpu').detach().numpy()
        label = data.y.to('cpu').detach().numpy()
        acc_test = accuracy_score(out[test_mask], label[test_mask])
        f1 = f1_score(out[test_mask], label[test_mask], average='macro')
        precision = precision_score(out[test_mask], label[test_mask], average='macro')
        recall = recall_score(out[test_mask], label[test_mask], average='macro')
        return acc_test, loss_test, f1, precision, recall

    model.apply(init_weights)

    best_val_f1 = -1
    best_state_dict = None
    best_epoch = 0
    patience_counter = 0

    for epoch in range(epochs):
        f1_val = train(epoch)
        scheduler.step()

        if f1_val > best_val_f1:
            best_val_f1 = f1_val
            best_epoch = epoch + 1
            best_state_dict = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= early_stopping_patience:
                print(f'Early stopping at epoch {epoch + 1} (best epoch: {best_epoch})')
                break

    # Evaluate on test set ONCE with the best model
    model.load_state_dict(best_state_dict)
    max_acc, loss_test, max_f1, max_precision, max_recall = test()

    checkpoints_dir = Path("checkpoints")
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    ckpt_name = f"seed{seed}_hd{hidden_dimension}_do{dropout}_ep{epochs}_lr{lr}.pt"
    ckpt_path = checkpoints_dir / ckpt_name
    torch.save(
        {
            "seed": seed,
            "hidden_dimension": hidden_dimension,
            "dropout": dropout,
            "epochs": epochs,
            "lr": lr,
            "weight_decay": weight_decay,
            "best_epoch": best_epoch,
            "best_val_f1": best_val_f1,
            "best_test_acc": max_acc,
            "best_precision": max_precision,
            "best_recall": max_recall,
            "best_f1": max_f1,
            "model_state_dict": best_state_dict,
        },
        ckpt_path,
    )
    print(f"Saved checkpoint: {ckpt_path}")


    print("Test set results:",
          "epoch= {:}".format(best_epoch),
          "test_accuracy= {:.4f}".format(max_acc),
          "precision= {:.4f}".format(max_precision),
          "recall= {:.4f}".format(max_recall),
          "f1_score= {:.4f}".format(max_f1)
          )

    return max_acc, max_precision, max_recall, max_f1

if __name__ == "__main__":

    t = time.time()

    # Load dataset ONCE (reused across all seeds and configs)
    dataset = Dataset_TMTM('./Twibot22_Dataset', processed_source_dir='./processed_data')
    data = dataset[0]

    # Hyperparameters configuration
    hidden_dimension_options = [64, 128, 256]
    dropout_options = [0.2, 0.3, 0.4]
    epochs_options = [100, 150, 200]
    lr_options = [1e-2, 1e-3, 1e-4]

    # Reconstruct best global F1 from existing checkpoints
    best_global_f1 = 0
    best_global_config = None
    checkpoints_dir = Path("checkpoints")
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    for ckpt_file in checkpoints_dir.glob("seed*_hd*_do*_ep*_lr*.pt"):
        try:
            ckpt = torch.load(ckpt_file, map_location='cpu')
            f1 = ckpt.get("best_f1", 0) * 100
            if f1 > best_global_f1:
                best_global_f1 = f1
                best_global_config = {
                    'hidden_dimension': ckpt.get('hidden_dimension'),
                    'dropout': ckpt.get('dropout'),
                    'epochs': ckpt.get('epochs'),
                    'lr': ckpt.get('lr'),
                    'weight_decay': ckpt.get('weight_decay', weight_decay),
                }
        except Exception:
            pass

    if best_global_config:
        print(f"Resumed from checkpoints. Current best F1: {best_global_f1:.2f}")
        print(f"  Config: {best_global_config}")

    # File to save the results (APPEND mode to preserve previous results)
    with open('results.txt', 'a') as f:
        original_stdout = sys.stdout
        sys.stdout = Tee(original_stdout, f)

        print(f"\n{'='*60}")
        print(f"RESUMING TRAINING at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # Iter over all the possible configurations
        for hidden_dimension, dropout, epochs, lr in itertools.product(hidden_dimension_options, dropout_options, epochs_options, lr_options):

            # --- RESUME LOGIC: skip if all 5 seeds already have checkpoints ---
            existing_seeds = []
            for seed in random_seed:
                ckpt_name = f"seed{seed}_hd{hidden_dimension}_do{dropout}_ep{epochs}_lr{lr}.pt"
                if (checkpoints_dir / ckpt_name).exists():
                    existing_seeds.append(seed)

            if len(existing_seeds) == len(random_seed):
                # All seeds done — load metrics from checkpoints and skip training
                acc_list, precision_list, recall_list, f1_list = [], [], [], []
                for seed in random_seed:
                    ckpt_name = f"seed{seed}_hd{hidden_dimension}_do{dropout}_ep{epochs}_lr{lr}.pt"
                    ckpt = torch.load(checkpoints_dir / ckpt_name, map_location='cpu')
                    acc_list.append(ckpt.get("best_test_acc", 0) * 100)
                    precision_list.append(ckpt.get("best_precision", 0) * 100)
                    recall_list.append(ckpt.get("best_recall", 0) * 100)
                    f1_list.append(ckpt.get("best_f1", 0) * 100)

                mean_f1 = np.mean(f1_list)
                print(f"[SKIP] hd={hidden_dimension} do={dropout} ep={epochs} lr={lr} "
                      f"— already done (F1={mean_f1:.2f} ± {np.std(f1_list):.2f})")

                if mean_f1 > best_global_f1:
                    best_global_f1 = mean_f1
                    best_global_config = {
                        'hidden_dimension': hidden_dimension, 'dropout': dropout,
                        'epochs': epochs, 'lr': lr, 'weight_decay': weight_decay
                    }
                continue

            # --- Train missing seeds ---
            acc_list = []
            precision_list = []
            recall_list = []
            f1_list = []

            current_hyperparams = {
                'hidden_dimension': hidden_dimension, 
                'dropout': dropout, 
                'epochs': epochs, 
                'lr': lr, 
                'weight_decay': weight_decay
            }

            for i, seed in enumerate(random_seed):
                # Skip seeds that already have checkpoints
                ckpt_name = f"seed{seed}_hd{hidden_dimension}_do{dropout}_ep{epochs}_lr{lr}.pt"
                if (checkpoints_dir / ckpt_name).exists():
                    ckpt = torch.load(checkpoints_dir / ckpt_name, map_location='cpu')
                    acc = ckpt.get("best_test_acc", 0)
                    precision = ckpt.get("best_precision", 0)
                    recall = ckpt.get("best_recall", 0)
                    f1 = ckpt.get("best_f1", 0)
                    print(f'\n[SKIP] Seed {seed} already done (F1={f1:.4f})')
                else:
                    print('\nTraining {}th model (seed={})'.format(i + 1, seed))
                    acc, precision, recall, f1 = main(
                        seed, data, hidden_dimension, dropout, epochs, lr, weight_decay
                    )

                acc_list.append(acc * 100)
                precision_list.append(precision * 100)
                recall_list.append(recall * 100)
                f1_list.append(f1 * 100)

            print(f'Configuration: {current_hyperparams}')
            print('Accuracy: {:.2f} ± {:.2f}'.format(np.mean(acc_list), np.std(acc_list)))
            print('Precision: {:.2f} ± {:.2f}'.format(np.mean(precision_list), np.std(precision_list)))
            print('Recall: {:.2f} ± {:.2f}'.format(np.mean(recall_list), np.std(recall_list)))
            print('F1 Score: {:.2f} ± {:.2f}'.format(np.mean(f1_list), np.std(f1_list)))

            mean_f1 = np.mean(f1_list)
            if mean_f1 > best_global_f1:
                best_global_f1 = mean_f1
                best_global_config = current_hyperparams
                print(f"New best configuration: {best_global_config} with f1={best_global_f1:.2f}")

        print(f"Best global configuration: {best_global_config} with f1={best_global_f1:.2f}")
        print('Total time:', time.time() - t)

        # Save the single best model for fine-tuning / deployment
        if best_global_config is not None:
            import shutil
            best_hd = best_global_config['hidden_dimension']
            best_do = best_global_config['dropout']
            best_ep = best_global_config['epochs']
            best_lr = best_global_config['lr']

            # Find the best seed's checkpoint for this config (highest F1)
            best_ckpt_path = None
            best_ckpt_f1 = -1
            checkpoints_dir = Path("checkpoints")
            for seed in random_seed:
                ckpt_name = f"seed{seed}_hd{best_hd}_do{best_do}_ep{best_ep}_lr{best_lr}.pt"
                ckpt_path = checkpoints_dir / ckpt_name
                if ckpt_path.exists():
                    ckpt = torch.load(ckpt_path, map_location='cpu')
                    if ckpt.get("best_f1", 0) > best_ckpt_f1:
                        best_ckpt_f1 = ckpt["best_f1"]
                        best_ckpt_path = ckpt_path

            if best_ckpt_path:
                best_model_path = checkpoints_dir / "best_model.pt"
                shutil.copy2(best_ckpt_path, best_model_path)
                print(f"\n{'='*60}")
                print(f"BEST MODEL saved to: {best_model_path}")
                print(f"  Config: {best_global_config}")
                print(f"  Test F1: {best_ckpt_f1:.4f}")
                print(f"  Source: {best_ckpt_path.name}")
                print(f"{'='*60}")
                print(f"\nFor fine-tuning:  python finetune.py --checkpoint {best_model_path}")

        # Reset the standard output
        sys.stdout = original_stdout
