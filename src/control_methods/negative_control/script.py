import pandas as pd
import anndata as ad
import sys
import numpy as np

## VIASH START
par = {
  "perturbation_data": "resources/grn-benchmark/perturbation_data.h5ad",
  "prediction": "output/negative_control.csv",
  "tf_all": "resources/prior/tf_all.csv"
}
## VIASH END
print(par)

print('Reading input data')
perturbation_data = ad.read_h5ad(par["perturbation_data"])
gene_names = perturbation_data.var_names.to_numpy()
tf_all = np.loadtxt(par['tf_all'], dtype=str)

n_tf = 400
tfs = tf_all[:n_tf]

def create_negative_control(gene_names) -> np.ndarray:
    ratio = [.98, .01, 0.01]
    
    net = np.random.choice([0, -1, 1], size=((len(gene_names), n_tf)),p=ratio)
    net = pd.DataFrame(net, index=gene_names, columns=tfs)
    return net
print('Inferring GRN')
net = create_negative_control(gene_names)

pivoted_net = net.reset_index().melt(id_vars='index', var_name='source', value_name='weight')

pivoted_net = pivoted_net.rename(columns={'index': 'target'})
pivoted_net = pivoted_net[pivoted_net['weight'] != 0]


print('Saving')
pivoted_net.to_csv(par["prediction"])

