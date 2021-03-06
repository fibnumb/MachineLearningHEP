#############################################################################
##  © Copyright CERN 2018. All rights not expressly granted are reserved.  ##
##                 Author: Gian.Michele.Innocenti@cern.ch                  ##
## This program is free software: you can redistribute it and/or modify it ##
##  under the terms of the GNU General Public License as published by the  ##
## Free Software Foundation, either version 3 of the License, or (at your  ##
## option) any later version. This program is distributed in the hope that ##
##  it will be useful, but WITHOUT ANY WARRANTY; without even the implied  ##
##     warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    ##
##           See the GNU General Public License for more details.          ##
##    You should have received a copy of the GNU General Public License    ##
##   along with this program. if not, see <https://www.gnu.org/licenses/>. ##
#############################################################################

"""
Methods to: study expected significance
"""
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from ROOT import TH1F, TF1, TFile, gROOT  # pylint: disable=import-error,no-name-in-module
from machine_learning_hep.logger import get_logger
from machine_learning_hep.general import get_database_ml_parameters
from machine_learning_hep.general import filterdataframe_singlevar, filter_df_cand
from machine_learning_hep.efficiency import calc_eff, calc_eff_acc

def calc_bkg(df_bkg, name, num_steps, fit_region, bin_width, sig_region, save_fit, out_dir):
    """
    Estimate the number of background candidates under the signal peak. This is obtained
    from real data with a fit of the sidebands of the invariant mass distribution.
    """
    logger = get_logger()
    ns_left = int(num_steps / 10) - 1
    ns_right = num_steps - ns_left
    x_axis_left = np.linspace(0., 0.49, ns_left)
    x_axis_right = np.linspace(0.5, 1.0, ns_right)
    x_axis = np.concatenate((x_axis_left, x_axis_right))
    bkg_array = []
    bkg_err_array = []
    num_bins = (fit_region[1] - fit_region[0]) / bin_width
    num_bins = int(round(num_bins))
    bin_width = (fit_region[1] - fit_region[0]) / num_bins

    if save_fit:
        logger.debug("Saving bkg fits to file")
        out_file = TFile(f'{out_dir}/bkg_fits_{name}.root', 'recreate')
        out_file.cd()

    logger.debug("To fit the bkg a pol2 function is used")
    for thr in x_axis:
        bkg = 0.
        bkg_err = 0.
        hmass = TH1F(f'hmass_{thr:.5f}', '', num_bins, fit_region[0], fit_region[1])
        bkg_sel_mask = df_bkg['y_test_prob' + name].values >= thr
        sel_mass_array = df_bkg[bkg_sel_mask]['inv_mass'].values

        if len(sel_mass_array) > 5:
            for mass_value in np.nditer(sel_mass_array):
                hmass.Fill(mass_value)
            fit = hmass.Fit('pol2', 'Q', '', fit_region[0], fit_region[1])
            if save_fit:
                hmass.Write()
            if int(fit) == 0:
                fit_func = hmass.GetFunction('pol2')
                bkg = fit_func.Integral(sig_region[0], sig_region[1]) / bin_width
                bkg_err = fit_func.IntegralError(sig_region[0], sig_region[1]) / bin_width
                del fit_func
        elif save_fit:
            hmass.Write()

        bkg_array.append(bkg)
        bkg_err_array.append(bkg_err)
        del hmass

    out_file.Close()
    return bkg_array, bkg_err_array, x_axis


def calc_peak_sigma(df_mc_reco, sel_opt, main_dict, mass, fit_region, bin_width):
    """
    Estimate the width of the signal peak from MC.
    """
    logger = get_logger()
    df_signal = filter_df_cand(df_mc_reco, main_dict, sel_opt)
    num_bins = (fit_region[1] - fit_region[0]) / bin_width
    num_bins = int(round(num_bins))

    hmass = TH1F('hmass', '', num_bins, fit_region[0], fit_region[1])
    mass_array = df_signal['inv_mass'].values
    for mass_value in np.nditer(mass_array):
        hmass.Fill(mass_value)

    gaus_fit = TF1("gaus_fit", "gaus", fit_region[0], fit_region[1])
    gaus_fit.SetParameters(0, hmass.Integral())
    gaus_fit.SetParameters(1, mass)
    gaus_fit.SetParameters(2, 0.02)
    logger.debug("To fit the signal a gaussian function is used")
    fit = hmass.Fit("gaus_fit", "RQ")

    if int(fit) != 0:
        logger.error("Problem in signal peak fit")
        sigma = 0.
        return sigma

    sigma = gaus_fit.GetParameter(2)
    logger.debug("Mean of the gaussian: %f", gaus_fit.GetParameter(1))
    logger.debug("Sigma of the gaussian: %f", sigma)
    del hmass
    del gaus_fit

    return sigma


def calc_signif(sig_array, sig_err_array, bkg_array, bkg_err_array):
    """
    Calculate the expected signal significance as a function of the treshold on the
    ML model output.
    """
    signif_array = []
    signif_err_array = []

    for sig, bkg, sig_err, bkg_err in zip(sig_array, bkg_array, sig_err_array, bkg_err_array):
        signif = 0.
        signif_err = 0.

        if sig > 0 and (sig + bkg) > 0:
            signif = sig / np.sqrt(sig + bkg)
            signif_err = signif * np.sqrt((sig_err**2 + bkg_err**2) / (4 * (sig + bkg)**2) + \
                         (bkg / (sig + bkg)) * sig_err**2 / sig**2)

        signif_array.append(signif)
        signif_err_array.append(signif_err)

    return signif_array, signif_err_array


#pylint: disable=too-many-arguments
def calc_sig_dmeson(filename, fonll_pred, frag_frac, branch_ratio, sigma_mb, taa, f_prompt,
                    ptmin, ptmax, eff_acc):
    """
    Estimate the expected signal yield per event before the ML model selections,
    this approach is valid for all D-meson with the proper parameter configuration.
    """
    logger = get_logger()
    df = pd.read_csv(filename)
    df_in_pt = df.query('(pt >= @ptmin) and (pt < @ptmax)')[fonll_pred]
    prod_cross = df_in_pt.sum() * frag_frac * 1e-12 / len(df_in_pt)
    delta_pt = ptmax - ptmin
    signal_yield = 2. * prod_cross * delta_pt * branch_ratio * eff_acc * taa \
                   / (sigma_mb * f_prompt)
    logger.debug("Expected signal yield: %f", signal_yield)

    return signal_yield


def plot_fonll(filename, fonll_pred, frag_frac, part_label, suffix, plot_dir):
    """
    Plot the FONLL prediction for the current particle.
    """
    df = pd.read_csv(filename)
    plt.figure(figsize=(20, 15))
    plt.subplot(111)
    plt.plot(df['pt'], df[fonll_pred] * frag_frac, linewidth=4.0)
    plt.xlabel('P_t [GeV/c]', fontsize=20)
    plt.ylabel('Cross Section [pb/GeV]', fontsize=20)
    plt.title("FONLL cross section " + part_label, fontsize=20)
    plt.semilogy()
    plt.savefig(f'{plot_dir}/FONLL_curve_{suffix}.png')

#pylint: disable=too-many-statements, too-many-locals
def study_signif(case, names, bin_lim, file_mc_gen, file_data_evt_ml, file_data_evt_tot,
                 df_mc_reco, df_ml_test, df_data_dec, suffix, plot_dir):
    """
    Study the efficiency and the expected signal significance as a function of
    the threshold value on a ML model output.
    """
    logger = get_logger()
    gROOT.SetBatch(True)
    gROOT.ProcessLine("gErrorIgnoreLevel = kWarning;")

    gen_dict = get_database_ml_parameters()[case]
    mass = gen_dict["mass"]
    mass_fit_lim = gen_dict['mass_fit_lim']
    bin_width = gen_dict['bin_width']
    var_bin = gen_dict['variables']['var_binning']
    sopt_dict = gen_dict['signif_opt']
    bkg_fract = sopt_dict['bkg_data_fraction']
    save_fit = sopt_dict['save_fit']

    df_mc_gen = pd.read_pickle(file_mc_gen)
    df_mc_gen = df_mc_gen.query(gen_dict['presel_gen'])
    df_mc_gen = filterdataframe_singlevar(df_mc_gen, var_bin, bin_lim[0], bin_lim[1])
    df_evt_ml = pd.read_pickle(file_data_evt_ml) # portion of data events used for ML
    n_events_ml = len(df_evt_ml.query(sopt_dict['sel_event']))
    logger.debug("Number of data events used for ML: %d", n_events_ml)
    df_evt_tot = pd.read_pickle(file_data_evt_tot) # total data events
    n_events_tot = len(df_evt_tot.query(sopt_dict['sel_event']))
    logger.debug("Total number of data events: %d", n_events_tot)

    # The uncertainty on the pre-selection efficiency times acceptance is neglected as
    # that on the expected signal yield
    eff_acc, _ = calc_eff_acc(df_mc_gen, df_mc_reco, 'mc_signal_prompt', gen_dict)
    exp_signal = calc_sig_dmeson(sopt_dict['filename_fonll'], sopt_dict['fonll_pred'],
                                 sopt_dict['FF'], sopt_dict['BR'], sopt_dict['sigma_MB'],
                                 sopt_dict['Taa'], sopt_dict['f_prompt'], bin_lim[0], bin_lim[1],
                                 eff_acc)
    plot_fonll(sopt_dict['filename_fonll'], sopt_dict['fonll_pred'],
               sopt_dict['FF'], case, suffix, plot_dir)

    fig_signif_pevt = plt.figure(figsize=(20, 15))
    plt.xlabel('Threshold', fontsize=20)
    plt.ylabel(r'Significance Per Event ($3 \sigma$)', fontsize=20)
    plt.title("Significance Per Event vs Threshold", fontsize=20)

    fig_signif = plt.figure(figsize=(20, 15))
    plt.xlabel('Threshold', fontsize=20)
    plt.ylabel(r'Significance ($3 \sigma$)', fontsize=20)
    plt.title("Significance vs Threshold", fontsize=20)

    df_data_dec = df_data_dec.tail(round(len(df_data_dec) * bkg_fract))
    sigma = calc_peak_sigma(df_mc_reco, 'mc_signal', gen_dict, mass, mass_fit_lim, bin_width)
    sig_region = [mass - 3 * sigma, mass + 3 * sigma]

    for name in names:

        #significance per event
        eff_array, eff_err_array, x_axis = calc_eff(df_ml_test, 'mc_signal_prompt', gen_dict, name,
                                                    sopt_dict['num_steps'])
        sig_array = [eff * exp_signal for eff in eff_array]
        sig_err_array = [eff_err * exp_signal for eff_err in eff_err_array]
        bkg_array, bkg_err_array, _ = calc_bkg(df_data_dec, name, sopt_dict['num_steps'],
                                               mass_fit_lim, bin_width, sig_region, save_fit,
                                               plot_dir)
        bkg_array = [bkg / (bkg_fract * n_events_ml) for bkg in bkg_array]
        bkg_err_array = [bkg_err / (bkg_fract * n_events_ml) for bkg_err in bkg_err_array]
        signif_array, signif_err_array = calc_signif(sig_array, sig_err_array, bkg_array,
                                                     bkg_err_array)
        plt.figure(fig_signif_pevt.number)
        plt.errorbar(x_axis, signif_array, yerr=signif_err_array, alpha=0.3, label=f'{name}',
                     elinewidth=2.5, linewidth=4.0)

        #significance ML dataset and total dataset
        signif_array_ml = [sig * sqrt(n_events_ml) for sig in signif_array]
        signif_err_array_ml = [sig_err * sqrt(n_events_ml) for sig_err in signif_err_array]
        plt.figure(fig_signif.number)
        plt.errorbar(x_axis, signif_array_ml, yerr=signif_err_array_ml, alpha=0.3,
                     label=f'{name}_ML_dataset', elinewidth=2.5, linewidth=4.0)

        signif_array_tot = [sig * sqrt(n_events_tot) for sig in signif_array]
        signif_err_array_tot = [sig_err * sqrt(n_events_tot) for sig_err in signif_err_array]
        plt.figure(fig_signif.number)
        plt.errorbar(x_axis, signif_array_tot, yerr=signif_err_array_tot, alpha=0.3,
                     label=f'{name}_Tot', elinewidth=2.5, linewidth=4.0)

    plt.figure(fig_signif_pevt.number)
    plt.legend(loc="lower left", prop={'size': 18})
    plt.savefig(f'{plot_dir}/Significance_PerEvent_{suffix}.png')

    plt.figure(fig_signif.number)
    plt.legend(loc="lower left", prop={'size': 18})
    plt.savefig(f'{plot_dir}/Significance_{suffix}.png')
