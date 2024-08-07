from typing import Dict, List, Tuple, Any, Union
import random

import tqdm
import numpy as np
import lightgbm
import pandas as pd
import anndata as ad
from sklearn.preprocessing import LabelEncoder, RobustScaler, StandardScaler
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error


SEED = 0xCAFE
N_POINTS_TO_ESTIMATE_BACKGROUND = 20


def load_grn(filepath: str, gene_names: np.ndarray) -> np.ndarray:
    gene_dict = {gene_name: i for i, gene_name in enumerate(gene_names)}
    A = np.zeros((len(gene_names), len(gene_names)), dtype=float)
    df = pd.read_csv(filepath, sep=',', header='infer', index_col=0)
    for source, target, weight in zip(df['source'], df['target'], df['weight']):
        if (source not in gene_dict) or (target not in gene_dict):
            continue
        i = gene_dict[source]
        j = gene_dict[target]
        A[i, j] = float(weight)
    return A


def fill_zeros_in_grn(A: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    A = np.copy(A)
    A[A > 0] = A[A > 0] + eps
    A[A < 0] = A[A < 0] - eps
    A[A == 0] = np.random.rand(*A[A == 0].shape) * 2 * eps - eps
    A += np.random.rand(*A.shape) * eps
    return A


def cross_validate_gene(
        estimator_t: str,
        X: np.ndarray,
        groups: np.ndarray,
        grn: np.ndarray,
        j: int,
        n_features: int = 10,
        random_state: int = 0xCAFE
) -> Dict[str, float]:
    
    results = {'r2': np.nan, 'mse': np.nan, 'avg-r2': np.nan}
    
    if n_features == 0:
        return results
    
    # Feature selection
    scores = np.abs(grn[:, j])
    scores[j] = -1
    selected_features = np.argsort(scores)[-n_features:]
    assert j not in selected_features
    X_ = X[:, selected_features]

    # Define labels
    y_ = X[:, j]

    y_pred, y_target, r2s = [], [], []
    for t, (train_index, test_index) in enumerate(LeaveOneGroupOut().split(X_, y_, groups)):

        if estimator_t == 'ridge':
            model = Ridge(random_state=random_state)
        elif estimator_t == 'GB':
            model = lightgbm.LGBMRegressor(verbosity=-1, n_estimators=100, n_jobs=4, random_state=random_state)
        else:
            raise NotImplementedError(f'Unknown model "{estimator_t}"')

        X_train = X_[train_index, :]
        X_test = X_[test_index, :]
        y_train = y_[train_index]
        y_test = y_[test_index]
        
        model.fit(X_train, y_train)

        y_pred.append(model.predict(X_test))
        y_target.append(y_test)
        r2s.append(r2_score(y_target[-1], y_pred[-1]))

    y_pred = np.concatenate(y_pred, axis=0)
    y_target = np.concatenate(y_target, axis=0)
    
    results['r2'] = float(r2_score(y_target, y_pred))
    results['mse'] = float(mean_squared_error(y_target, y_pred))
    results['avg-r2'] = float(np.mean(r2s))
    
    return results


def learn_background_distribution(
        estimator_t: str,
        X: np.ndarray,
        groups: np.ndarray,
        max_n_regulators: int,
        random_state: int = 0xCAFE
) -> Dict[int, Tuple[float, float]]:

    rng = np.random.default_rng(seed=random_state)

    n_genes = X.shape[1]
    random_grn = rng.random(size=(n_genes, n_genes))

    background = {}
    for n_features in tqdm.tqdm(range(1, max_n_regulators + 1), desc='Estimating background dist'):
        scores = []
        for _ in range(N_POINTS_TO_ESTIMATE_BACKGROUND):
            j = rng.integers(low=0, high=n_genes)
            random_grn[:, j] = rng.random(size=n_genes)
            res = cross_validate_gene(
                estimator_t,
                X,
                groups,
                random_grn,
                j,
                n_features=n_features,
                random_state=random_state
            )
            scores.append(res['avg-r2'])
        background[n_features] = (np.mean(scores), max(0.001, np.std(scores)))
    background['max'] = background[max_n_regulators]
    return background


def cross_validate(
        estimator_t: str,
        gene_names: np.ndarray,
        X: np.ndarray,
        groups: np.ndarray,
        grn: np.ndarray,
        n_features: np.ndarray
) -> List[Dict[str, float]]:
    n_genes = len(grn)
    
    grn = fill_zeros_in_grn(grn)
    
    results = []
    for j in tqdm.tqdm(range(n_genes), desc=f'{estimator_t} CV'):
        res = cross_validate_gene(estimator_t, X, groups, grn, j, n_features=int(n_features[j]))
        results.append(res)
    
    return {
        'gene_names': list(gene_names),
        'scores': list(results)
    }


def main(par: Dict[str, Any]) -> pd.DataFrame:

    # Set global seed for reproducibility purposes
    random_state = SEED
    np.random.seed(random_state)
    random.seed(random_state)
    lightgbm.LGBMRegressor().set_params(random_state=random_state)

    print('Reading input files', flush=True)
    
    # Load perturbation data
    perturbation_data = ad.read_h5ad(par['perturbation_data'])
    gene_names = perturbation_data.var.index.to_numpy()
    n_genes = len(gene_names)
    groups = LabelEncoder().fit_transform(perturbation_data.obs.plate_name)
    
    # Load inferred GRN
    grn = load_grn(par['prediction'], gene_names)
    
    results = []
    layer = 'pearson'
    print(f'Compute metrics for layer: {layer}', flush=True)

    # Load and standardize perturbation data
    X = perturbation_data.layers[layer]
    X = RobustScaler().fit_transform(X)

    # Determine maximum number of input features
    max_n_regulators = min(100, int(0.5 * n_genes))

    # Learn background distribution for each value of `n_features`:
    # r2 scores using random genes as features.
    background = learn_background_distribution(par['reg_type'], X, groups, max_n_regulators, random_state=random_state)

    # Cross-validate each gene using the inferred GRN to define select input features
    res = cross_validate(
        par['reg_type'],
        gene_names,
        X,
        groups,
        grn,
        np.clip(np.sum(grn != 0, axis=0), 0, max_n_regulators)
    )

    # Compute z-scores from r2 scores to take into account the fact
    # that random network can still perform well when the number of features is large
    scores = []
    for j in range(n_genes):
        if np.isnan(res['scores'][j]['avg-r2']):
            continue
        n_features = int(np.sum(grn[:, j] != 0))
        if n_features in background:
            mu, sigma = background[n_features]
        else:
            mu, sigma = background['max']
        z_score = (res['scores'][j]['avg-r2'] - mu) / sigma
        z_score = max(0, z_score)
        scores.append(z_score)

    total_score = np.mean(scores)
    print(f'Score on {layer}: {total_score}')

    # Convert results to DataFrame
    df_results = pd.DataFrame(results, index=layers)
    
    return df_results
