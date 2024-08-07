import pandas as pd
import anndata as ad
import sys
import numpy as np
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm


## VIASH START
par = {
  "perturbation_data": "resources/grn-benchmark/perturbation_data.h5ad",
  "layer": "scgen_pearson",
  "tf_all":  "resources/grn-benchmark/tf_all.txt",
  "prediction": "output/positive_control.csv",
}
## VIASH END
print('Reading input data')
perturbation_data = ad.read_h5ad(par["perturbation_data"])
gene_names = perturbation_data.var_names.to_numpy()
tf_all = np.loadtxt(par['tf_all'], dtype=str)
groups = perturbation_data.obs.cell_type

# def create_positive_control(X: np.ndarray) -> np.ndarray:
#     X = StandardScaler().fit_transform(X) 
#     return np.dot(X.T, X) / X.shape[0]
def create_positive_control(X: np.ndarray, groups: np.ndarray):
    grns = []
    for group in tqdm(np.unique(groups), desc="Processing groups"):
        X_sub = X[groups == group, :]
        X_sub = StandardScaler().fit_transform(X_sub)
        grn = np.dot(X_sub.T, X_sub) / X_sub.shape[0]
        grns.append(grn)
    return np.mean(grns, axis=0)
print('Inferring GRN')
net = create_positive_control(perturbation_data.layers[par["layer"]], groups)

net = pd.DataFrame(net, index=gene_names, columns=gene_names)
net = net.loc[:, net.columns.isin(tf_all)]

pivoted_net = net.reset_index().melt(id_vars='index', var_name='source', value_name='weight')

pivoted_net = pivoted_net.rename(columns={'index': 'target'})
pivoted_net = pivoted_net[pivoted_net['weight'] != 0]
print('Saving')
pivoted_net.to_csv(par["prediction"])

