# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

from data_utils.data_utils import read_all_data
from data_utils.preprocessing_utils import (
    get_static_vars, get_dynamic_vars, add_icds_to_static_vars, get_drugs_timeseries_df,
    split_treat_covariates, append_more_covariates
)


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
def main(input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')

    logger.info('reading raw data')
    inpatients_records, drugs, clinical_vars, labs, labs_v2, codes_emergency, codes_inpatient =\
        read_all_data(input_filepath)

    labs = labs_v2 # temporariliy only use labs_v2 in downstream steps

    logger.info('drugs_df')
    drugs_timeseries_df = get_drugs_timeseries_df(inpatients_records, drugs, clinical_vars, labs,
                                                  output_filepath,
                                                  max_num_drugs=100, logger=logger)

    # in this dataset, the treatment variable is in the drugs_df, so remove it from the drugs_df
    # drugs_treatments in this case is all the HIBOR, drugs_covariates is the rest to merge with dynamic df
    logger.info('splitting drugs df into treatment and other covariateds')
    drugs_treatments, drugs_covariates = split_treat_covariates(
        drugs_timeseries_df, 'HIBOR')

    static_df = get_static_vars(inpatients_records,clinical_vars, labs, output_filepath)
    
    logger.info('processnig labs and clinical variables')
    labs_clinicalvars_df = get_dynamic_vars(clinical_vars, labs, output_filepath)
    
    dynamic_df = append_more_covariates(labs_clinicalvars_df, drugs_covariates)

    logger.info('getting icd data')
    static_df_icds = add_icds_to_static_vars(
        static_df, codes_emergency, codes_inpatient)

    # add column for binary treatment indicator

    logger.info('saving')
    dynamic_df.to_csv(output_filepath + 'dynamic_vars.csv')
    static_df_icds.to_csv(output_filepath + 'static_vars.csv')
    drugs_treatments.to_csv(output_filepath + 'treatment_vars.csv')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]
    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())
    main()
