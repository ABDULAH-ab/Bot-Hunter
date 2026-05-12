from pathlib import Path

import torch
from torch_geometric.data import Data
from torch_geometric.data import InMemoryDataset

from utils import sample_mask


class Dataset_TMTM(InMemoryDataset):
    def __init__(self, root, processed_source_dir="processed_data", transform=None, pre_transform=None):
        self.processed_source_dir = Path(processed_source_dir)
        super().__init__(root, transform, pre_transform)
        self.data, self.slices = torch.load(self.processed_paths[0], weights_only=False)
        self.root = root

    @property
    def raw_file_names(self):
        return ['some_file_1', 'some_file_2', ...]

    @property
    def processed_file_names(self):
        return ['data.pt']


    def process(self):
        source_dir = self.processed_source_dir

        edge_index = torch.load(source_dir / "edge_index.pt")
        edge_index = torch.tensor(edge_index, dtype = torch.int64)
        edge_type = torch.load(source_dir / "edge_type.pt")
        bot_label = torch.load(source_dir / "labels.pt")
        features = torch.load(source_dir / "features.pt")
        features = features.to(torch.float32)

        # Load tweet-level behavioral features (7 dims) and append
        tweet_feat_path = source_dir / "tweet_features.pt"
        if tweet_feat_path.exists():
            tweet_feat = torch.load(tweet_feat_path)
            tweet_feat = tweet_feat.to(torch.float32)
            features = torch.cat([features, tweet_feat], dim=1)
            print(f"Loaded tweet features: {tweet_feat.shape[1]} additional columns")

        num_idx = [0,1,2,3,4,5,9,12,17,18,19,20,22,23,24,25,26,28,29,30,31,32,33,34,35,36,37,39,40,41,42,43,44,45,46,47,48,49,50,51,52]
        cat_idx = [6,7,8,10,11,13,14,15,16,21,27,38]

        def gather_with_zero_fill(feat_tensor, indices):
            cols = []
            feature_dim = feat_tensor.size(1)
            for idx in indices:
                if idx < feature_dim:
                    cols.append(feat_tensor[:, idx:idx + 1])
                else:
                    cols.append(torch.zeros((feat_tensor.size(0), 1), dtype=feat_tensor.dtype))
            return torch.cat(cols, dim=1)

        num_prop = gather_with_zero_fill(features, num_idx)
        cat_prop = gather_with_zero_fill(features, cat_idx)
        des_tensor = torch.load(source_dir / "des_tensor.pt")
        tweets_tensor = torch.load(source_dir / "tweets_tensor.pt")


        print("Dimensions of numerical properties:", num_prop.shape)
        print("Dimensions of categorical properties:", cat_prop.shape)
        print("Dimensions of description tensor:", des_tensor.shape)
        print("Dimensions of tweets tensor:", tweets_tensor.shape)


        features = torch.cat([cat_prop, num_prop, des_tensor, tweets_tensor], axis=1)
        data = Data(x=features, y =bot_label, edge_index=edge_index)
        data.edge_type = edge_type

        data.y2 = bot_label
        sample_number = len(data.y2)

        train_idx = range(int(0.7*sample_number))
        val_idx = range(int(0.7*sample_number), int(0.9*sample_number))
        test_idx = range(int(0.9*sample_number), int(sample_number))

        data.train_mask = sample_mask(train_idx, sample_number)
        data.val_mask = sample_mask(val_idx, sample_number)
        data.test_mask = sample_mask(test_idx, sample_number)

        data_list = [data]

        if self.pre_filter is not None:
            data_list = [data for data in data_list if self.pre_filter(data)]

        if self.pre_transform is not None:
            data_list = [self.pre_transform(data) for data in data_list]

        data, slices = self.collate(data_list)
        torch.save((data, slices), self.processed_paths[0])