import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Scratchpad

    A notebook for exploration and disordered thinking
    """
    )
    return


@app.cell
def _():
    from pathlib import Path
    from typing import Optional
    from dataclasses import dataclass

    import pandas as pd
    import numpy as np
    import ROOT
    import matplotlib.pyplot as plt
    from scipy.optimize import curve_fit
    from scipy.stats import norm, ks_2samp

    return Optional, Path, ROOT, ks_2samp, np, pd, plt


@app.cell
def _(mo):
    benchmarks = ["B2ChamberTracker", "B4LayeredCalorimeter", "CaloChallenge"]
    benchmark_dropdown = mo.ui.dropdown(options = benchmarks, value="CaloChallenge", label="Benchmark: ")

    return (benchmark_dropdown,)


@app.cell
def _(Path, benchmark_dropdown, mo):
    benchmark_run_base = Path(benchmark_dropdown.value) / "test_runs"

    iteration_files = [iteration_folder.name for iteration_folder in sorted(benchmark_run_base.iterdir())]

    iteration_dropdown = mo.ui.dropdown(options=iteration_files, label="Iteration ID: ")
    return benchmark_run_base, iteration_dropdown


@app.cell
def _(benchmark_dropdown, iteration_dropdown, mo):
    mo.vstack([benchmark_dropdown, iteration_dropdown])
    return


@app.cell
def _(benchmark_run_base, iteration_dropdown):
    # Load your results file
    base_path = benchmark_run_base / iteration_dropdown.value

    base_path
    return (base_path,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Performance analysis

    In order to understand the performance impact, we get some graphs comparing performance of the simulations with and without AdePT
    """
    )
    return


@app.cell
def _(base_path, pd):
    results_path = base_path / "performance-results.csv"
    df = pd.read_csv(results_path)
    return (df,)


@app.cell
def _(pd):
    def split_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Helper function to split the DataFrame into two based on the 'with_adept' column.

        Args:
            df: The input DataFrame containing performance data.

        Returns:
            A tuple containing two DataFrames: (with_adept_df, without_adept_df).
        """
        with_adept = df[df["with_adept"]]
        without_adept = df[~df["with_adept"]]
        return with_adept, without_adept

    def get_performance_data(df: pd.DataFrame, number_of_threads: int) -> pd.DataFrame:
        """
        Filters and prepares performance data for plotting.

        Args:
            df: The original DataFrame containing all simulation data.
            number_of_threads: The number of threads to filter the data by.

        Returns:
            A DataFrame filtered by the specified number of threads.
        """
        return df[df["NUMBER_OF_THREADS"] == number_of_threads]

    def get_performance_ratio_data(
        df: pd.DataFrame, number_of_threads: int, variable: str = "time_per_event"
    ) -> pd.DataFrame:
        """
        Calculates the performance ratio (speedup) between simulations
        with and without adept for a given number of threads.

        Args:
            df: The original DataFrame containing all simulation data.
            number_of_threads: The number of threads to filter the data by.
            variable: The performance variable to calculate the ratio for (e.g., "time_per_event").

        Returns:
            A merged DataFrame with the ratio calculated, ready for plotting.
        """
        filtered = get_performance_data(df, number_of_threads)

        with_adept, without_adept = split_data(filtered)

        merged = pd.merge(
            with_adept,
            without_adept,
            on=["NUMBER_OF_THREADS", "PARTICLES_PER_EVENT"],
            suffixes=("_with_adept", "_without_adept"),
        )

        merged[f"{variable}_ratio"] = (
            merged[f"{variable}_without_adept"] / merged[f"{variable}_with_adept"]
        )

        return merged
    return get_performance_data, get_performance_ratio_data, split_data


@app.cell
def _(Optional, pd, plt, split_data):
    def plot_performance_by_particle_num(
        df: pd.DataFrame, variable: str = "time_per_event", ax: Optional[plt.Axes] = None
    ) -> plt.Axes:
        """
        Plots performance data for simulations with and without adept.

        Args:
            df: A DataFrame containing the performance data for a specific thread count.
            variable: The performance variable to plot.
            ax: An optional Matplotlib Axes object to plot on. If None, a new figure is created.

        Returns:
            The Matplotlib Axes object with the plot drawn on it.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))

        with_adept, without_adept = split_data(df)

        ax.plot(
            with_adept["PARTICLES_PER_EVENT"],
            with_adept[variable],
            marker="o",
            label="With Adept",
            color="blue",
        )
        ax.plot(
            without_adept["PARTICLES_PER_EVENT"],
            without_adept[variable],
            marker="o",
            label="Without Adept",
            color="orange",
        )

        ax.set_xscale("log")
        ax.grid(True)
        ax.legend()

        return ax

    def plot_performance_ratios(
        df: pd.DataFrame, variable: str = "time_per_event", ax: Optional[plt.Axes] = None
    ) -> plt.Axes:
        """
        Plots the performance ratio (speedup).

        Args:
            df: A DataFrame with the performance ratios already calculated.
            variable: The performance variable used to calculate the ratio.
            ax: An optional Matplotlib Axes object to plot on. If None, a new figure is created.

        Returns:
            The Matplotlib Axes object with the plot drawn on it.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))

        ratio_column = f"{variable}_ratio"
        ax.plot(
            df["PARTICLES_PER_EVENT"],
            df[ratio_column],
            marker="o",
            label="Speedup",
            color="blue",
        )

        ax.set_xscale("log")
        ax.grid(True)
        ax.legend()

        return ax
    return plot_performance_by_particle_num, plot_performance_ratios


@app.cell(hide_code=True)
def _(df, mo):
    threads_dropdown = mo.ui.dropdown.from_series(df["NUMBER_OF_THREADS"])
    variable_dropdown = mo.ui.dropdown(
        options=[
            "time_per_event",
            "execution_time",
            "throughput",
            "event_loop_time",
        ],
        value="time_per_event",
        label="Variable: ",
    )
    return threads_dropdown, variable_dropdown


@app.cell
def _(mo, threads_dropdown, variable_dropdown):
    mo.vstack([threads_dropdown, variable_dropdown])
    return


@app.cell(hide_code=True)
def _(
    df,
    get_performance_data,
    get_performance_ratio_data,
    plot_performance_by_particle_num,
    plot_performance_ratios,
    plt,
    threads_dropdown,
    variable_dropdown,
):
    _number_of_threads = threads_dropdown.value
    _variable = variable_dropdown.value

    # --- Prepare the data using the modular functions ---
    performance_df = get_performance_data(df, _number_of_threads)
    ratio_df = get_performance_ratio_data(df, _number_of_threads, variable=_variable)

    # --- Create the plot with two subplots ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6)) # 1 row, 2 columns

    # --- Call the plotting functions, passing the respective axes ---
    plot_performance_by_particle_num(performance_df, variable=_variable, ax=ax1)
    plot_performance_ratios(ratio_df, variable=_variable, ax=ax2)

    # --- Customize the plots (titles, labels, etc.) ---
    fig.suptitle(
        f"Performance Comparison and Speed-up Factor for CaloChallenge (Threads: {_number_of_threads})",
        fontsize=16
    )

    # Customize the first subplot (comparison)
    ax1.set_xlabel("Number of Particles")
    ax1.set_ylabel(f"{_variable}")
    ax1.set_title("Performance with vs. without Adept")
    ax1.set_yscale("log")

    # Customize the second subplot (ratios)
    ax2.set_xlabel("Number of Particles")
    ax2.set_ylabel(f"{_variable} Speedup (Without / With Adept)")
    ax2.set_title("Performance Speedup Ratio")

    # Add a horizontal line at y=1 on the ratio plot for reference
    ax2.axhline(y=1, color='red', linestyle='--', linewidth=1, label='Break-even')

    # --- 7. Final layout adjustments and show the plot ---
    plt.tight_layout(rect=[0, 0, 1, 0.96]) # rect leaves space for suptitle
    plt.show()
    return (ratio_df,)


@app.cell
def _(ratio_df, variable_dropdown):
    _variable = variable_dropdown.value
    ratio_df[ratio_df["PARTICLES_PER_EVENT"] == 1000][[f"{_variable}_with_adept", f"{_variable}_without_adept", f"{_variable}_ratio"]]
    return


@app.cell
def _(mo):
    hist_name_dropdown = mo.ui.dropdown(
        options=[
            "cellEnergy",
            "energyDeposited",
            "energyParticle",
            "energyRatio",
            "hitType",
            "longFirstMoment",
            "longProfile",
            "longSecondMoment",
            "numHits",
            "phiProfile",
            "transFirstMoment",
            "transProfile",
            "transSecondMoment",
        ],
        value="phiProfile",
        label="histogram: ",
    )
    return (hist_name_dropdown,)


@app.cell
def _(hist_name_dropdown):
    hist_name_dropdown
    return


@app.cell(hide_code=True)
def _(ROOT, base_path, hist_name_dropdown, np, plt):

    # --- User Inputs ---
    file_adept =  base_path / "adept_simulation_PARTICLES_PER_EVENT=1000_PARTICLE_TYPE=electron_NUMBER_OF_THREADS=32_NUMBER_OF_EVENTS=5000.root"  # Replace with your AdePT ROOT file
    file_g4    = base_path / "geant4_simulation_PARTICLES_PER_EVENT=1000_PARTICLE_TYPE=electron_NUMBER_OF_THREADS=32_NUMBER_OF_EVENTS=5000.root"      # Replace with your G4 ROOT file
    hist_name  = f"CaloChallengeMonitoring/{hist_name_dropdown.value}"        # Replace with the histogram name

    # --- Open ROOT files ---
    f_adept = ROOT.TFile.Open(str(file_adept))
    f_g4    = ROOT.TFile.Open(str(file_g4))

    # --- Retrieve histograms ---
    h_adept = f_adept.Get(hist_name)
    h_g4    = f_g4.Get(hist_name)

    if not h_adept or not h_g4:
        raise RuntimeError("Histogram not found in one or both files!")

    # --- Extract bin data ---
    def extract_hist_data(h):
        nbins = h.GetNbinsX()
        centers = np.array([h.GetBinCenter(i) for i in range(1, nbins+1)])
        counts  = np.array([h.GetBinContent(i) for i in range(1, nbins+1)])
        errors  = np.array([h.GetBinError(i)   for i in range(1, nbins+1)])
        x_title = h.GetXaxis().GetTitle()
        y_title = h.GetYaxis().GetTitle()
        title = h.GetTitle()
        return centers, counts, errors, x_title, y_title, title

    centers, counts_adept, errors_adept, x_title, y_title, title = extract_hist_data(h_adept)
    _,      counts_g4,    errors_g4, *_    = extract_hist_data(h_g4)

    # --- Plotting ---
    # _fig, (ax_main, ax_ratio) = plt.subplots(2, 1, figsize=(10, 8),
    #                                         gridspec_kw={'height_ratios': [3, 1]},
    #                                         constrained_layout=True)

    _fig, ax_main = plt.subplots(figsize=(10, 6))

    # Main panel: overlayed histograms with error bars
    ax_main.errorbar(centers, counts_adept, yerr=errors_adept, fmt='o', label='AdePT', alpha=0.8)
    ax_main.errorbar(centers, counts_g4,    yerr=errors_g4,    fmt='s', label='G4',    alpha=0.8)
    ax_main.set_xlabel(x_title)
    ax_main.set_ylabel(y_title)
    ax_main.set_title(title)

    ax_main.set_xlabel(r"$<\lambda^2> (mm^2) $")



    ax_main.legend()
    ax_main.grid(True, alpha=0.3)

    # Ratio panel: AdePT / G4 with error propagation
    counts_adept = counts_adept.astype(float)
    counts_g4    = counts_g4.astype(float)
    errors_adept = errors_adept.astype(float)
    errors_g4    = errors_g4.astype(float)

    # ratio = np.divide(counts_adept, counts_g4, out=np.zeros_like(counts_adept), where=counts_g4!=0)
    # ratio_err = np.zeros_like(ratio)
    # mask = counts_g4 > 0
    # ratio_err[mask] = np.sqrt(
    #     (errors_adept[mask] / counts_g4[mask])**2 +
    #     (counts_adept[mask] * errors_g4[mask] / counts_g4[mask]**2)**2
    # )

    # ax_ratio.errorbar(centers, ratio, yerr=ratio_err, fmt='ko-', markersize=3, alpha=0.8)
    # ax_ratio.axhline(1, color='red', linestyle='--', alpha=0.7, label='Unity')
    # ax_ratio.set_xlabel('Variable')
    # ax_ratio.set_ylabel('AdePT / G4')
    # ax_ratio.grid(True, alpha=0.3)
    # ax_ratio.legend()

    # plt.savefig("adept_vs_g4_comparison.png", dpi=300, bbox_inches='tight')
    plt.show()

    # --- Clean up ---
    # f_adept.Close()
    # f_g4.Close()

    return (
        centers,
        counts_adept,
        counts_g4,
        errors_adept,
        errors_g4,
        f_adept,
        f_g4,
        h_adept,
        h_g4,
    )


@app.cell
def _(
    counts_adept,
    counts_g4,
    errors_adept,
    errors_g4,
    f_adept,
    f_g4,
    h_adept,
    h_g4,
    np,
):

    # 1. Diferencia de medias y desviaciones estándar
    mean_adept = h_adept.GetMean()
    mean_g4 = h_g4.GetMean()
    std_adept = h_adept.GetStdDev()
    std_g4 = h_g4.GetStdDev()
    print(f"AdePT mean: {mean_adept:.3f}, std: {std_adept:.3f}")
    print(f"G4 mean: {mean_g4:.3f}, std: {std_g4:.3f}")

    # 2. Chi-cuadrado y p-valor
    chi2 = h_adept.Chi2Test(h_g4, "UU CHI2/NDF")
    pval = h_adept.Chi2Test(h_g4, "UU P")
    print(f"Chi2/NDF: {chi2:.2f}, p-value: {pval:.4f}")

    # 3. Test de Kolmogorov-Smirnov
    ks_pval = h_adept.KolmogorovTest(h_g4)
    print(f"KS p-value: {ks_pval:.4f}")

    # 4. RMSE (Root Mean Square Error)
    rmse = np.sqrt(np.mean((counts_adept - counts_g4)**2))
    print(f"RMSE: {rmse:.4f}")

    # 5. Diferencia y ratio bin a bin
    diff = counts_adept - counts_g4
    avg_values = (counts_adept + counts_g4) / 2
    ratio = np.divide(counts_adept, counts_g4, out=np.zeros_like(counts_adept), where=counts_g4!=0)
    percent_diff = np.abs(np.divide(diff, avg_values, out=np.zeros_like(diff), where=avg_values!=0))
    print(f"Mean diff: {np.mean(diff):.3f}, Mean Ratio: {np.mean(ratio):.3f}, Mean error: {np.mean(percent_diff)}")

    # 6. Significancia bin a bin
    significance = np.zeros_like(diff)
    mask = (errors_adept**2 + errors_g4**2) > 0
    significance[mask] = diff[mask] / np.sqrt(errors_adept[mask]**2 + errors_g4[mask]**2)

    # --- Clean up ---
    f_adept.Close()
    f_g4.Close()

    return (significance,)


@app.cell
def _(counts_adept, counts_g4, ks_2samp, np):
    def get_ks_statistic(
        adept_values: np.ndarray, geant4_values: np.ndarray
    ) -> tuple[float, float]:
        """
        Performs the two-sample Kolmogorov-Smirnov test on two sets of data.

        Args:
            adept_values: An array of numerical values from the Adept simulation.
            geant4_values: An array of numerical values from the Geant4 simulation.

        Returns:
            A tuple containing the D-statistic and the p-value.
        """
        if adept_values.size == 0 or geant4_values.size == 0:
            return np.nan, np.nan

        ks_result = ks_2samp(adept_values, geant4_values)
        return ks_result.statistic, ks_result.pvalue

    _ks_statistic, _ks_pvalue = get_ks_statistic(counts_adept, counts_g4)

    print(f"K-S test:\n\tD: {_ks_statistic:.3g}\n\tP: {_ks_pvalue:.3g}")
    return


@app.cell
def _(
    centers,
    counts_adept,
    counts_g4,
    diffcod,
    errors_adept,
    errors_g4,
    plt,
    significance,
):
    # --- Visualización ---
    _fig, _axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    _axs[0].errorbar(centers, counts_adept, yerr=errors_adept, fmt='o', label='AdePT')
    _axs[0].errorbar(centers, counts_g4, yerr=errors_g4, fmt='s', label='G4')
    _axs[0].set_ylabel("Entries")
    _axs[0].legend()
    _axs[0].set_title("Overlay")

    _axs[1].plot(centers, diffcod, label="AdePT - G4")
    _axs[1].set_ylabel("Difference")
    _axs[1].legend()

    _axs[2].plot(centers, significance, label="Significance (bin-by-bin)")
    _axs[2].axhline(0, color='gray', linestyle='--')
    _axs[2].set_ylabel("Significance")
    _axs[2].set_xlabel("Variable")
    _axs[2].legend()

    plt.tight_layout()
    plt.show()
    return


if __name__ == "__main__":
    app.run()
