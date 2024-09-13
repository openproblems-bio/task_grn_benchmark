echo  "negative control"
viash run src/control_methods/negative_control/config.vsh.yaml -- --multiomics_rna resources/grn-benchmark/multiomics_rna.h5ad \
  --perturbation_data resources/grn-benchmark/perturbation_data.h5ad \
  --tf_all resources/prior/tf_all.csv \
  --prediction resources/grn_models/baselines/negative_control.csv 


echo  "baseline pearson"
viash run src/control_methods/baseline_corr/config.vsh.yaml -- --multiomics_rna resources/grn-benchmark/multiomics_rna.h5ad \
  --tf_all resources/prior/tf_all.csv \
  --causal false \
  --corr_method pearson \
  --cell_type_specific  false \
  --metacell  false \
  --impute false \
  --prediction resources/grn_models/baselines/baseline_pearson.csv 

echo  "baseline pearson causal"
viash run src/control_methods/baseline_corr/config.vsh.yaml -- --multiomics_rna resources/grn-benchmark/multiomics_rna.h5ad \
  --tf_all resources/prior/tf_all.csv \
  --causal true \
  --corr_method pearson \
  --cell_type_specific  false \
  --metacell  false \
  --impute false \
  --prediction resources/grn_models/baselines/baseline_pearson_causal.csv 


echo  "baseline causal cell type"
viash run src/control_methods/baseline_corr/config.vsh.yaml -- --multiomics_rna resources/grn-benchmark/multiomics_rna.h5ad \
  --tf_all resources/prior/tf_all.csv \
  --causal true \
  --corr_method pearson \
  --cell_type_specific  true \
  --metacell  false \
  --impute false \
  --prediction resources/grn_models/baselines/baseline_pearson_causal_celltype.csv 

echo  "baseline pearson causal metacell"
viash run src/control_methods/baseline_corr/config.vsh.yaml -- --multiomics_rna resources/grn-benchmark/multiomics_rna.h5ad \
  --tf_all resources/prior/tf_all.csv \
  --causal true \
  --corr_method pearson \
  --cell_type_specific  false \
  --metacell  true \
  --impute false \
  --prediction resources/grn_models/baselines/baseline_pearson_causal_metacell.csv 

echo  "positive control"
viash run src/control_methods/positive_control/config.vsh.yaml -- --multiomics_rna resources/grn-benchmark/multiomics_rna.h5ad \
  --perturbation_data resources/grn-benchmark/perturbation_data.h5ad \
  --tf_all resources/prior/tf_all.csv \
  --prediction resources/grn_models/baselines/positive_control.csv 