from footprint_model.constants.units import u
from footprint_model.constants.explainable_quantities import ExplainableQuantity

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict


class EmissionPlotter:
    def __init__(self, ax, formatted_input_dicts__old: List[Dict[str, ExplainableQuantity]],
                 formatted_input_dicts__new: List[Dict[str, ExplainableQuantity]], title: str, rounding_value: int,
                 timespan: ExplainableQuantity,
                 legend_labels: List[str] = ("Electricity consumption", "Fabrication")):
        self.ax = ax
        self.formatted_input_dicts__old = formatted_input_dicts__old
        self.formatted_input_dicts__new = formatted_input_dicts__new
        self.title = title
        self.rounding_value = rounding_value
        self.timespan = timespan
        self.legend_labels = legend_labels
        self.elements = ["Servers", "Storage", "Network", "Devices"]
        self.index = np.arange(len(self.elements))
        self.bar_width = 0.4
        self.total_emissions_in_kg__new = self.calculate_total_emissions(formatted_input_dicts__new)
        self.total_emissions_in_kg__old = self.calculate_total_emissions(formatted_input_dicts__old)
        self.colors = ["#1f77b4", "#ff7f0e"]

    def calculate_total_emissions(self, formatted_input_dicts):
        total_emissions_in_kg = 0
        for input_dict in formatted_input_dicts:
            total_emissions_in_kg += (sum(input_dict.values()) * self.timespan).to(u.kg).magnitude
        return total_emissions_in_kg

    def get_values(self, input_dict):
        return [(input_dict.get(element, 0 * u.kg / u.year) * self.timespan).to(u.kg).magnitude for element in self.elements]

    def plot_common_values(self, common_values, i, color):
        return self.ax.bar(self.index + i * self.bar_width, common_values, self.bar_width, color=color, alpha=1.0)

    def plot_difference_values(self, diff_values, common_values, i, color):
        return self.ax.bar(
            self.index + i * self.bar_width, diff_values, self.bar_width, bottom=common_values, color=color, alpha=0.1)

    def plot_positive_diff(self, positive_diffs, common_values, i, color):
        return self.ax.bar(
            self.index + i * self.bar_width, positive_diffs, self.bar_width, bottom=common_values, color=color,
            alpha=0.9)

    def add_annotations_and_text(self, rects_common, diffs, values_old, values_new):
        arrowprops = dict(facecolor='black', shrink=0.05, width=2, headwidth=8)

        for rect, diff, value_old, value_new in zip(rects_common, diffs, values_old, values_new):
            if value_old != value_new:
                if diff < -0.5:
                    self.ax.annotate("", xy=(rect.get_x() + rect.get_width() / 2 - 0.06, min(value_old, value_new)),
                                xytext=(rect.get_x() + rect.get_width() / 2 - 0.06, max(value_old, value_new)),
                                arrowprops=arrowprops)
                    self.ax.text(rect.get_x() + rect.get_width() / 2 + 0.06, (value_old + value_new) / 2, f"{diff:.0f}%",
                            ha="center", va="center")
                elif diff > 0.5:
                    self.ax.annotate("", xy=(rect.get_x() + rect.get_width() / 2 - 0.06, max(value_old, value_new)),
                                xytext=(rect.get_x() + rect.get_width() / 2 - 0.06, min(value_old, value_new)),
                                arrowprops=arrowprops)
                    self.ax.text(rect.get_x() + rect.get_width() / 2 + 0.06, (value_old + value_new) / 2, f"+{diff:.0f}%",
                            ha="center", va="center")

            proportion = (value_new / self.total_emissions_in_kg__new) * 100
            self.ax.text(rect.get_x() + rect.get_width() / 2, value_new, f"{proportion:.0f}%", ha="center", va="bottom")

    # A function to handle titles and labels
    def set_axes_labels(self):
        self.ax.set_xlabel("Physical Elements")
        self.ax.set_ylabel(f"kg CO2 emissions / {self.timespan.value}")
        self.ax.set_title(self.title, fontsize=24, fontweight="bold", y=1.12)

        self.ax.set_xticks(self.index + self.bar_width / 2)
        self.ax.set_xticklabels(self.elements, rotation=45, ha="right")

        ax2 = self.ax.twinx()
        max_value = max(
            [max(input_dict.values()) * self.timespan
             for input_dict in self.formatted_input_dicts__new + self.formatted_input_dicts__old]).to(u.kg).magnitude

        max_value_margin = 1.1
        ax2.set_ylim(0, 100 * max_value_margin * (max_value / self.total_emissions_in_kg__new))
        ax2.set_ylabel("Proportions (%)")

        self.ax.set_ylim(0, max_value_margin * max_value)

    def set_titles(self):
        self.ax.set_title(self.title, fontsize=24, fontweight="bold", y=1.1)
        if self.total_emissions_in_kg__new < 501:
            unit = "kg"
            dividing_number = 1
        else:
            unit = "ton"
            dividing_number = 1000
        rounded_total__new = round(self.total_emissions_in_kg__new / dividing_number, self.rounding_value)
        if self.rounding_value == 0:
            rounded_total__new = int(rounded_total__new)

        total_emissions_in_kg__old = 0
        for input_dict in self.formatted_input_dicts__old:
            total_emissions_in_kg__old += (sum(input_dict.values()) * self.timespan).to(u.kg).magnitude

        rounded_total__old = round(total_emissions_in_kg__old / dividing_number, self.rounding_value)
        if self.rounding_value == 0:
            rounded_total__old = int(rounded_total__old)

        if rounded_total__old != rounded_total__new:
            subtitle_text = f"From {rounded_total__old} to {rounded_total__new} {unit}s of CO2 emissions in" \
                            f" {self.timespan.value} " \
                            f"({int(100 * (rounded_total__new - rounded_total__old) / rounded_total__old)}%)"
        else:
            subtitle_text = f"{rounded_total__new} {unit}s of CO2 emissions in {self.timespan.value}"

        self.ax.text(
            0.5, 1.1, subtitle_text,
            transform=self.ax.transAxes, fontsize=22, va="top", ha="center")

    def plot_emission_diffs(self):
        for i, (input_dict_old, input_dict_new) in enumerate(
                zip(self.formatted_input_dicts__old, self.formatted_input_dicts__new)):
            values_old = self.get_values(input_dict_old)
            values_new = self.get_values(input_dict_new)

            diffs = [(new - old) / old * 100 if old != 0 else 0 for old, new in zip(values_old, values_new)]
            common_values = [min(old, new) for old, new in zip(values_old, values_new)]
            diff_values = [abs(new - old) for old, new in zip(values_old, values_new)]

            rects_common = self.plot_common_values(common_values, i, self.colors[i])
            self.plot_difference_values(diff_values, common_values, i, self.colors[i])
            self.plot_positive_diff(
                [max(new - old, 0) for old, new in zip(values_old, values_new)], common_values, i, self.colors[i])

            self.add_annotations_and_text(rects_common, diffs, values_old, values_new)
            self.set_axes_labels()
            self.add_legend()
            self.set_titles()

    def add_legend(self):
        handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in self.colors]
        self.ax.legend(handles, self.legend_labels)


if __name__ == "__main__":
    from footprint_model.constants.explainable_quantities import ExplainableQuantity
    from footprint_model.constants.sources import SourceValue, Sources
    from footprint_model.core.user_journey import UserJourney, UserJourneyStep
    from footprint_model.core.server import Servers
    from footprint_model.core.storage import Storage
    from footprint_model.core.service import Service, Request
    from footprint_model.core.device_population import DevicePopulation, Devices
    from footprint_model.core.usage_pattern import UsagePattern
    from footprint_model.core.network import Networks
    from footprint_model.core.system import System
    from footprint_model.constants.countries import Countries

    from copy import deepcopy

    server = Servers.SERVER
    storage = Storage(
        "Default SSD storage",
        carbon_footprint_fabrication=SourceValue(160 * u.kg, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        power=SourceValue(1.3 * u.W, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        lifespan=SourceValue(6 * u.years, Sources.HYPOTHESIS),
        idle_power=SourceValue(0 * u.W, Sources.HYPOTHESIS),
        storage_capacity=SourceValue(1 * u.To, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        power_usage_effectiveness=1.2,
        country=Countries.GERMANY,
        data_replication_factor=3,
        data_storage_duration=10 * u.year
    )
    service = Service("Youtube", server, storage, base_ram_consumption=300 * u.Mo,
                              base_cpu_consumption=2 * u.core)

    streaming_request = Request(
        "20 min streaming on Youtube", service, 50 * u.ko, (2.5 / 3) * u.Go, duration=4 * u.min)
    streaming_step = UserJourneyStep("20 min streaming on Youtube", streaming_request, 20 * u.min)
    upload_request = Request(
        "0.4 s of upload", service, 300 * u.ko, 0 * u.Go, duration=1 * u.s)
    upload_step = UserJourneyStep("0.4s of upload", upload_request, 0.1 * u.s)

    default_uj = UserJourney("Daily Youtube usage", uj_steps=[streaming_step, upload_step])

    default_device_pop = DevicePopulation(
        "French Youtube users on laptop", 4e7 * 0.3, Countries.FRANCE, [Devices.LAPTOP])

    dp_uj = deepcopy(default_uj)
    dp_device_pop = deepcopy(default_device_pop)
    dp_device_pop.country = Countries.GERMANY

    default_network = Networks.WIFI_NETWORK
    dp_default_network = deepcopy(default_network)

    system_1 = System("system 1", [UsagePattern(
        "Average daily Youtube usage in France on laptop", default_uj, default_device_pop,
        default_network, 365 * u.user_journey / (u.user * u.year), [[7, 23]])])

    system_2 = System("system 2", [UsagePattern(
        "Average daily Youtube usage in France on laptop 2", dp_uj, dp_device_pop, dp_default_network,
        250 * u.user_journey / (u.user * u.year), [[7, 23]])])

    emissions_dict__old = [system_1.energy_footprints(), system_1.fabrication_footprints()]
    emissions_dict__new = [system_2.energy_footprints(), system_2.fabrication_footprints()]

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12, 8))

    EmissionPlotter(
        ax, emissions_dict__old, emissions_dict__new, title=system_1.name, rounding_value=1,
        timespan=ExplainableQuantity(1 * u.year, "one year")).plot_emission_diffs()

    plt.show()
