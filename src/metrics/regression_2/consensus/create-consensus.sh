viash build src/metrics/regression_2/consensus/config.vsh.yaml --platform docker -o bin/regression_2/consensus && bin/regression_2/consensus/consensus_for_regression_2 --perturbation_data resources/grn-benchmark/perturbation_data.h5ad --output resources/grn-benchmark/consensus-num-regulators.json --grn_folder resources/grn-benchmark/grn_models/ --grns ananse.csv,celloracle.csv,figr.csv,granie.csv,scenicplus.csv,scglue.csv