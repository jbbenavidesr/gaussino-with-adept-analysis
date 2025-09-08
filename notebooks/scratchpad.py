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
    import matplotlib.pyplot as plt
    from scipy.optimize import curve_fit
    from scipy.stats import norm, ks_2samp
    return Optional, Path, pd, plt


@app.cell
def _(mo):
    benchmarks = ["B2ChamberTracker", "B4LayeredCalorimeter", "CaloChallenge"]
    benchmark_dropdown = mo.ui.dropdown(options = benchmarks, value="B2ChamberTracker", label="Benchmark: ")

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
def _(ratio_df):
    ratio_df[ratio_df["PARTICLES_PER_EVENT"] == 1000]
    return


if __name__ == "__main__":
    app.run()
