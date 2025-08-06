import marimo

__generated_with = "0.14.16"
app = marimo.App(width="full")


@app.cell
def _(mo):
    mo.md(r"""# B4 benchmark analysis""")
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    from pathlib import Path
    from typing import Optional
    from dataclasses import dataclass

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.optimize import curve_fit
    from scipy.stats import norm, ks_2samp
    return Optional, Path, curve_fit, dataclass, ks_2samp, norm, np, pd, plt


@app.cell
def _(Path):
    # Load your results file
    base_path = Path("B4LayeredCalorimeter/test_runs/011_2025-07-14")
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
    threads_dropdown = mo.ui.dropdown.from_series(df["NUMBER_OF_THREADS"], value=1)
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
        f"Performance Comparison and Speedup (Threads: {_number_of_threads})",
        fontsize=16
    )

    # Customize the first subplot (comparison)
    ax1.set_xlabel("Number of Particles")
    ax1.set_ylabel(f"{_variable}")
    ax1.set_title("Performance with vs. without Adept")

    # Customize the second subplot (ratios)
    ax2.set_xlabel("Number of Particles")
    ax2.set_ylabel(f"{_variable} Speedup (Without / With Adept)")
    ax2.set_title("Performance Speedup Ratio")

    # Add a horizontal line at y=1 on the ratio plot for reference
    ax2.axhline(y=1, color='red', linestyle='--', linewidth=1, label='Break-even')

    # --- 7. Final layout adjustments and show the plot ---
    plt.tight_layout(rect=[0, 0, 1, 0.96]) # rect leaves space for suptitle
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Physics""")
    return


@app.cell
def _(base_path, pd):
    physics_path = base_path / "physics-results.csv"

    physics_df = pd.read_csv(physics_path)
    physics_df.head()
    return (physics_df,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Clean the data

    In order for comparisons to make sense, we need values to be in the same unit. We normalize energy deposition values to be in MeV and track length to be in meters.
    """
    )
    return


@app.cell
def _(physics_df):
    from analysis.units import convert_unit

    physics_df["edep_MeV"] = physics_df.apply(
        lambda row: convert_unit(
            row["edep_value"], row["edep_unit"], "MeV", base="eV"
        ),
        axis=1,
    )
    physics_df["track_length_m"] = physics_df.apply(
        lambda row: convert_unit(
            row["track_length_value"], row["track_length_unit"], "m", base="m"
        ),
        axis=1,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    phys_variable_dropdown = mo.ui.dropdown(
        options=["track_length_m", "edep_MeV"],
        value="edep_MeV",
        label="Variable a medir: ",
    )

    phys_particles_per_event_dropdown = mo.ui.dropdown(
        options=[1, 10, 100, 1000], value=100, label="Particulas por evento: "
    )

    layer_options = {str(i): i for i in range(7)}
    layer_options["Total"] = -1

    phys_layer_dropdown = mo.ui.dropdown(
        options=layer_options, value="Total", label="Layer: "
    )

    phys_detector_dropdown = mo.ui.dropdown(
        options=[
            "B4Calorimeter_Layer_AbsorberSDet",
            "B4Calorimeter_Layer_GapSDet",
        ],
        value="B4Calorimeter_Layer_AbsorberSDet",
        label="Detector: ",
    )
    return (
        phys_detector_dropdown,
        phys_layer_dropdown,
        phys_particles_per_event_dropdown,
        phys_variable_dropdown,
    )


@app.cell(hide_code=True)
def _(curve_fit, dataclass, norm, np):
    @dataclass
    class FitData:
        hist: np.array
        bins: np.array
        fit_curve: np.array
        mu: float
        mu_err: float
        std: float
        std_err: float


    def fit_gaussian(values: np.ndarray, bins: np.ndarray) -> FitData:
        """
        Computes a histogram and fits it to a Gaussian distribution.

        Args:
            values: The array of data points to be binned and fitted.
            bins: The histogram bin edges.

        Returns:
            A dictionary containing the histogram data and fit parameters with errors.
        """
        hist, _ = np.histogram(values, bins=bins)
        bin_centers = (bins[:-1] + bins[1:]) / 2

        # Gaussian function to fit
        def gaussian(x, amp, mu, sigma):
            return amp * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

        # Initial guesses
        initial_mu, initial_std = norm.fit(values)
        initial_amplitude = len(values) * np.diff(bins)[0]
        p0 = [initial_amplitude, initial_mu, initial_std]

        try:
            popt, pcov = curve_fit(gaussian, bin_centers, hist, p0=p0)
            perr = np.sqrt(np.diag(pcov))
            fit_curve = gaussian(bin_centers, *popt)
            return FitData(
                hist=hist,
                bins=bins,
                fit_curve=fit_curve,
                mu=popt[1],
                mu_err=perr[1],
                std=popt[2],
                std_err=perr[2],
            )
        except RuntimeError as e:
            print(f"Error fitting data: {e}")
            return FitData(
                hist=hist,
                bins=bins,
                fit_curve=np.zeros_like(bin_centers),
                mu=np.nan,
                mu_err=np.nan,
                std=np.nan,
                std_err=np.nan,
            )
    return (fit_gaussian,)


@app.cell(hide_code=True)
def _(fit_gaussian, np, pd, split_data):
    PlotData = dict


    def get_histogram_and_fit_data(
        data: pd.DataFrame,
        variable: str,
        particles_per_event: int,
        layer_number: int,
        detector: str,
        bins: int | str | list[float] = "auto",
    ) -> PlotData:
        """
        Filters data, computes histograms, and fits them to Gaussians for Adept and Geant4.

        Args:
            data: The full DataFrame.
            variable: The variable to analyze (e.g., 'edep_MeV').
            particles_per_event: The number of particles per event to filter by.
            layer_number: The layer number to filter by.
            detector: The detector name to filter by.
            bins: Number of bins for the histogram (e.g., 'auto', 50, or an array of bin edges).

        Returns:
            A dictionary containing all histogram and fit data for plotting.
        """
        filtered = data[
            (data["PARTICLES_PER_EVENT"] == particles_per_event)
            & (data["layer_number"] == layer_number)
            & (data["detector"] == detector)
        ]
        adept_df, geant4_df = split_data(filtered)

        if adept_df.empty or geant4_df.empty:
            raise ValueError(
                "One of the datasets (Adept or Geant4) is empty after filtering."
            )

        adept_values = adept_df[variable].values
        geant4_values = geant4_df[variable].values

        # Determine bins from combined data to ensure alignment
        if isinstance(bins, (int, str)):
            combined_bins = np.histogram_bin_edges(
                np.concatenate([adept_values, geant4_values]), bins=bins
            )
        else:
            combined_bins = bins

        adept_fit_data = fit_gaussian(adept_values, combined_bins)
        geant4_fit_data = fit_gaussian(geant4_values, combined_bins)

        return {
            "adept": adept_fit_data,
            "geant4": geant4_fit_data,
            "variable": variable,
            "values_adept": adept_values,
            "values_geant4": geant4_values,
        }


    def get_longitudinal_profiles(
        data: pd.DataFrame,
        particles_per_event: int,
        edep_variable: str = "edep_MeV",
    ) -> dict[str, pd.Series]:
        """
        Computes mean energy deposition profiles per layer for different detectors and Adept/Geant4.

        Args:
            data: The full DataFrame.
            particles_per_event: The number of particles per event to filter by.
            edep_variable: The name of the energy deposition variable.

        Returns:
            A dictionary of pandas Series, with keys like 'absorber_adept', 'gap_geant4', etc.
        """
        test_case_layers = data[
            (data["PARTICLES_PER_EVENT"] == particles_per_event)
            & (data["layer_number"] != -1)
        ]

        absorber_layers = test_case_layers[
            test_case_layers["detector"] == "B4Calorimeter_Layer_AbsorberSDet"
        ]
        gap_layers = test_case_layers[
            test_case_layers["detector"] == "B4Calorimeter_Layer_GapSDet"
        ]

        absorber_adept, absorber_geant4 = split_data(absorber_layers)
        gap_adept, gap_geant4 = split_data(gap_layers)

        return {
            "absorber_adept": absorber_adept.groupby("layer_number")[
                edep_variable
            ].mean(),
            "absorber_geant4": absorber_geant4.groupby("layer_number")[
                edep_variable
            ].mean(),
            "gap_adept": gap_adept.groupby("layer_number")[edep_variable].mean(),
            "gap_geant4": gap_geant4.groupby("layer_number")[edep_variable].mean(),
        }
    return PlotData, get_histogram_and_fit_data, get_longitudinal_profiles


@app.cell
def _(ks_2samp, np):
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

    return (get_ks_statistic,)


@app.cell(hide_code=True)
def _(Optional, PlotData, pd, plt):
    def plot_histogram_with_fits(
        plot_data: PlotData,
        ax: Optional[plt.Axes] = None
    ) -> plt.Axes:
        """
        Plots the histograms and their Gaussian fits.

        Args:
            plot_data: The dictionary returned by `get_histogram_and_fit_data`.
            ax: An optional Matplotlib Axes object to plot on. If None, a new figure is created.

        Returns:
            The Matplotlib Axes object with the plot.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=(10, 6))

        adept_data = plot_data["adept"]
        geant4_data = plot_data["geant4"]
        variable = plot_data["variable"]

        # Plot histograms
        ax.hist(
            plot_data["values_adept"], bins=adept_data.bins, histtype="step", color="blue", label="AdePT"
        )
        ax.hist(
            plot_data["values_geant4"], bins=geant4_data.bins, histtype="step", color="orange", label="Geant4"
        )

        # Plot fits
        ax.plot(
            (adept_data.bins[:-1] + adept_data.bins[1:]) / 2,
            adept_data.fit_curve,
            color="blue",
            linestyle="--",
            label=rf"AdePT fit ($\mu={adept_data.mu:.3g} \pm {adept_data.mu_err:.3g}$, $\sigma={adept_data.std:.3g} \pm {adept_data.std_err:.3g}$)",
        )
        ax.plot(
            (geant4_data.bins[:-1] + geant4_data.bins[1:]) / 2,
            geant4_data.fit_curve,
            color="orange",
            linestyle="--",
            label=rf"Geant4 fit ($\mu={geant4_data.mu:.3g} \pm {geant4_data.mu_err:.3g}$, $\sigma={geant4_data.std:.3g} \pm {geant4_data.std_err:.3g}$)",
        )

        ax.set_xlabel(variable)
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(True)
        return ax

    def plot_longitudinal_profile(
        profiles: dict[str, pd.Series],
        ax: Optional[plt.Axes] = None,
        profile_type: str = "absorber"
    ) -> plt.Axes:
        """
        Plots a longitudinal energy deposition profile for Adept and Geant4.

        Args:
            profiles: The dictionary returned by `get_longitudinal_profiles`.
            ax: An optional Matplotlib Axes object to plot on.
            profile_type: 'absorber' or 'gap' to select which profile to plot.

        Returns:
            The Matplotlib Axes object with the plot.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=(10, 6))

        adept_profile = profiles[f"{profile_type}_adept"]
        geant4_profile = profiles[f"{profile_type}_geant4"]

        ax.plot(
            adept_profile.index,
            adept_profile.values,
            label=f"{profile_type.capitalize()} (AdePT)",
            color="blue",
            marker="o",
        )
        ax.plot(
            geant4_profile.index,
            geant4_profile.values,
            label=f"{profile_type.capitalize()} (Geant4)",
            color="orange",
            linestyle="--",
            marker="x",
        )

        ax.set_xlabel("Layer Number (Depth)")
        ax.set_ylabel("Mean Energy Deposition per Event (MeV)")
        ax.legend()
        ax.grid(True)
        return ax
    return plot_histogram_with_fits, plot_longitudinal_profile


@app.cell
def _(
    mo,
    phys_detector_dropdown,
    phys_layer_dropdown,
    phys_particles_per_event_dropdown,
    phys_variable_dropdown,
):
    mo.vstack(
        [
            phys_layer_dropdown,
            phys_particles_per_event_dropdown,
            phys_variable_dropdown,
            phys_detector_dropdown,
        ]
    )
    return


@app.cell
def _(
    get_histogram_and_fit_data,
    phys_detector_dropdown,
    phys_layer_dropdown,
    phys_particles_per_event_dropdown,
    phys_variable_dropdown,
    physics_df,
    plot_histogram_with_fits,
    plt,
):
    histogram_data = get_histogram_and_fit_data(
        physics_df,
        variable=phys_variable_dropdown.value,
        particles_per_event=phys_particles_per_event_dropdown.value,
        layer_number=phys_layer_dropdown.value,
        detector=phys_detector_dropdown.value,
    )

    # 2. Plot the data and customize the figure
    _fig, ax = plt.subplots(figsize=(10, 6))
    plot_histogram_with_fits(histogram_data, ax=ax)

    # Add custom title and labels
    ax.set_title(
        f"{phys_variable_dropdown.value} Distribution in {phys_detector_dropdown.value}, Layer {phys_layer_dropdown.selected_key} ({phys_particles_per_event_dropdown.value} particles/event)"
    )

    plt.tight_layout()
    plt.show()

    return (histogram_data,)


@app.cell
def _(get_ks_statistic, histogram_data):
    # Calculate the Kolmogorov-Smirnov statistic
    ks_statistic, ks_pvalue = get_ks_statistic(histogram_data["values_adept"], histogram_data["values_geant4"])

    # Print the K-S results for statistical comparison
    print(
        f"Kolmogorov-Smirnov Test Results for {histogram_data['variable']}:"
    )
    print(f"  D-statistic: {ks_statistic:.4f}")
    print(f"  p-value: {ks_pvalue:.4e}")

    # Interpret the p-value
    if ks_pvalue < 0.05:
        print("  Conclusion: The two distributions are statistically different.")
    else:
        print("  Conclusion: There is no significant evidence that the distributions are different.")
    return


@app.cell
def _(
    get_longitudinal_profiles,
    phys_particles_per_event_dropdown,
    physics_df,
    plot_longitudinal_profile,
    plt,
):
    # 1. Get all profiles for both detectors and both simulators
    profiles = get_longitudinal_profiles(physics_df, particles_per_event=phys_particles_per_event_dropdown.value)

    # --- Example 3: Multiple plots in one figure ---
    # Create a figure with two subplots side-by-side
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(18, 6))

    # Plot absorber profile on the first subplot
    plot_longitudinal_profile(profiles, ax=_ax1, profile_type="absorber")
    _ax1.set_title("Absorber Profile")

    # Plot gap profile on the second subplot
    plot_longitudinal_profile(profiles, ax=_ax2, profile_type="gap")
    _ax2.set_title("Gap Profile")

    _fig.suptitle(
        f"Longitudinal Energy Deposition Profiles ({phys_particles_per_event_dropdown.value} particles/event)",
        fontsize=16
    )
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
    return


if __name__ == "__main__":
    app.run()
