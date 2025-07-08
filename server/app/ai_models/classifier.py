import os
import joblib
import numpy as np
import open_clip
import torch
from app.constants.device import device


class Classifier:
    def __init__(self):
        model, _, self.preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k"
        )
        self.model = model.to(device).eval()

        self.knn_clip = joblib.load(
            os.path.join(os.path.dirname(__file__), "../../knn_clip.pkl")
        )
        self.prompt_embs = joblib.load(
            os.path.join(os.path.dirname(__file__), "../../prompt_embs.pkl")
        )

    def prompt_ensemble_score(self, img_emb):
        return {
            cls: float(np.mean([img_emb.dot(te) for te in tes]))
            for cls, tes in self.prompt_embs.items()
        }

    def prompt_ensemble_top_10(self, emb):
        sims = self.prompt_ensemble_score(emb)

        # sort classes by descending similarity and take only to 10
        ranked = sorted(sims.items(), key=lambda kv: -kv[1])[:10]

        # unzip into two lists
        labels_sorted, scores_sorted = zip(*ranked)
        return list(labels_sorted), list(scores_sorted)

    def get_clip_embedding(self, image):
        image_tensor = self.preprocess(image).unsqueeze(0).to(device)
        with torch.no_grad():
            img_feat = self.model.encode_image(image_tensor)
            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
        return img_feat.cpu().numpy().flatten()

    def knn_top_10(self, emb):
        # fetch the 10 nearest neighbours
        dists, idxs = self.knn_clip.kneighbors([emb], n_neighbors=10)
        dists = dists[0]
        idxs = idxs[0]

        # map to labels
        labels = [self.knn_clip.classes_[self.knn_clip._y[i]] for i in idxs]

        # compute inverse-distance weights
        eps = 1e-6
        weights = 1.0 / (dists + eps)

        # sort all four lists by descending weight
        order = np.argsort(-weights)
        labels_sorted = [labels[i] for i in order]
        raw_distances_sorted = [dists[i] for i in order]
        weighted_distances_sorted = [weights[i] for i in order]

        return labels_sorted, raw_distances_sorted, weighted_distances_sorted

    def hybrid_classify(
        self,
        image,
        knn_weight_threshold,
        knn_raw_threshold,
        prompt_threshold,
        prompt_threshold_fault,
    ):
        emb = self.get_clip_embedding(image)

        knn_labels, knn_raw_distances, knn_weighted_distances_sorted = self.knn_top_10(
            emb
        )
        ensPrompt_labels, ensPrompt_scores = self.prompt_ensemble_top_10(emb)

        if knn_labels[0] == "coin" and ensPrompt_labels[0] == "coin":
            print("Both KNN and Prompt Ensemble predicted 'coin'")
            pred = "coin"
        elif (
            knn_weighted_distances_sorted[0] > knn_weight_threshold
            or knn_raw_distances[0] < knn_raw_threshold
        ):
            print("KNN predicted")
            pred = knn_labels[0]
        elif (
            ensPrompt_scores[0] > prompt_threshold
            and knn_weighted_distances_sorted[0]
            > (knn_weight_threshold - prompt_threshold_fault)
            and knn_raw_distances[0] < (knn_raw_threshold + prompt_threshold_fault)
        ):
            print("Prompt Ensemble predicted")
            pred = ensPrompt_labels[0]
        else:
            pred = "unknown"

        print(f"CLIP predicted → '{pred}'")

        knn_res = list(
            zip(knn_labels, knn_raw_distances, knn_weighted_distances_sorted)
        )
        ens_res = list(zip(ensPrompt_labels, ensPrompt_scores))

        print("KNN results")
        for i, (lbl, d, w) in enumerate(knn_res, 1):
            print(f"{i}. {lbl} → dist {d:.4f}, weight dist {w:.4f}")

        print("Prompt Ensemble results")
        for i, (lbl, s) in enumerate(ens_res, 1):
            print(f"{i + 1}. {lbl} → score {s:.4f}")

        return pred, knn_res, ens_res
