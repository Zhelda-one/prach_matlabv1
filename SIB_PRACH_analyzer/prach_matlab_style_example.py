"""
MATLAB NewRadioPRACHConfigurationExample.m style workflow in Python.

This script emulates the same step-by-step flow:
1) Show supported SCS combinations
2) Build a PRACH configuration
3) Select configuration index by preferred preamble format
4) Check active PRACH slot combinations
5) Inspect PRACH configuration properties
6) Build a PRACH resource grid and map PRACH symbols
7) Print waveform-related timing information (approximation)

Note:
- This is a Python approximation for analysis/visualization.
- It does not generate 3GPP-compliant PRACH IQ waveform like MATLAB 5G Toolbox.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sib1_parser import SIB1Parser


SUPPORTED_SCS_COMBINATIONS = [
    {"LRA": 839, "PRACHSubcarrierSpacing": 1.25, "PUSCHSubcarrierSpacing": 15, "NRBAllocation": 6, "kbar": 7},
    {"LRA": 839, "PRACHSubcarrierSpacing": 5, "PUSCHSubcarrierSpacing": 15, "NRBAllocation": 24, "kbar": 12},
    {"LRA": 139, "PRACHSubcarrierSpacing": 15, "PUSCHSubcarrierSpacing": 15, "NRBAllocation": 12, "kbar": 2},
    {"LRA": 139, "PRACHSubcarrierSpacing": 30, "PUSCHSubcarrierSpacing": 15, "NRBAllocation": 24, "kbar": 2},
    {"LRA": 139, "PRACHSubcarrierSpacing": 30, "PUSCHSubcarrierSpacing": 30, "NRBAllocation": 12, "kbar": 2},
    {"LRA": 139, "PRACHSubcarrierSpacing": 60, "PUSCHSubcarrierSpacing": 60, "NRBAllocation": 12, "kbar": 2},
]

# A compact, practical profile table for this project. These values are used as
# analysis defaults and mirror the structure exposed by MATLAB example output.
FORMAT_PROFILES = {
    "0": {"format": "0", "lra": 839, "num_time_occasions": 1, "prach_duration": 1, "symbol_location": 0},
    "1": {"format": "1", "lra": 839, "num_time_occasions": 1, "prach_duration": 2, "symbol_location": 0},
    "2": {"format": "2", "lra": 839, "num_time_occasions": 1, "prach_duration": 4, "symbol_location": 0},
    "3": {"format": "3", "lra": 839, "num_time_occasions": 1, "prach_duration": 4, "symbol_location": 0},
    "A1": {"format": "A1", "lra": 139, "num_time_occasions": 1, "prach_duration": 2, "symbol_location": 0},
    "A2": {"format": "A2", "lra": 139, "num_time_occasions": 2, "prach_duration": 4, "symbol_location": 0},
    "A3": {"format": "A3", "lra": 139, "num_time_occasions": 2, "prach_duration": 4, "symbol_location": 0},
    "B1": {"format": "B1", "lra": 139, "num_time_occasions": 2, "prach_duration": 4, "symbol_location": 0},
    "B2": {"format": "A2/B2", "lra": 139, "num_time_occasions": 3, "prach_duration": 4, "symbol_location": 8},
    "B3": {"format": "A3/B3", "lra": 139, "num_time_occasions": 3, "prach_duration": 4, "symbol_location": 8},
    "B4": {"format": "B4", "lra": 139, "num_time_occasions": 2, "prach_duration": 4, "symbol_location": 0},
    "C0": {"format": "C0", "lra": 139, "num_time_occasions": 1, "prach_duration": 7, "symbol_location": 0},
    "C2": {"format": "C2", "lra": 139, "num_time_occasions": 2, "prach_duration": 4, "symbol_location": 0},
}


@dataclass
class CarrierConfig:
    subcarrier_spacing: int = 15


@dataclass
class PRACHConfig:
    frequency_range: str = "FR1"
    duplex_mode: str = "FDD"
    configuration_index: int = 14
    subcarrier_spacing: float = 15
    sequence_index: int = 0
    preamble_index: int = 0
    restricted_set: str = "UnrestrictedSet"
    zero_correlation_zone: int = 0
    rb_offset: int = 0
    frequency_start: int = 0
    frequency_index: int = 0
    time_index: int = 0
    active_prach_slot: int = 0
    n_prach_slot: int = 0
    lra: int = 139
    preferred_format: str = "B2"


class PRACHMatlabStyleExample:
    def __init__(self, carrier: CarrierConfig, prach: PRACHConfig):
        self.carrier = carrier
        self.prach = prach

    @staticmethod
    def supported_scs_combinations_table() -> pd.DataFrame:
        return pd.DataFrame(SUPPORTED_SCS_COMBINATIONS)

    def select_configuration_index_by_format(self, preferred_format: str) -> None:
        preferred_format = preferred_format.upper()
        self.prach.preferred_format = preferred_format

        # MATLAB example picks the last matching index and applies special handling.
        # Here we keep deterministic, practical indices for project use.
        if preferred_format in {"B2", "B3"}:
            self.prach.configuration_index = 146
            self.prach.time_index = max(FORMAT_PROFILES[preferred_format]["num_time_occasions"] - 1, 0)
        elif preferred_format in {"A1", "A2", "A3", "B1", "B4", "C0", "C2"}:
            self.prach.configuration_index = 64
            self.prach.time_index = 0
        else:
            self.prach.configuration_index = 14
            self.prach.time_index = 0

        profile = FORMAT_PROFILES.get(preferred_format, FORMAT_PROFILES["B2"])
        self.prach.lra = int(profile["lra"])

    def is_prach_active(self, n_prach_slot: int, active_prach_slot: int, prach_scs: float) -> bool:
        fmt = self.prach.preferred_format
        is_long = fmt in {"0", "1", "2", "3"}

        if prach_scs == 30:
            if is_long or self.prach.frequency_range.upper() != "FR1":
                return False
            # Pattern follows the MATLAB example activity table for short preamble case:
            # active when active_prach_slot == n_prach_slot % 2
            return active_prach_slot == (n_prach_slot % 2)

        # Typical 15 kHz case for FR1 in this project: active in each frame/slot pattern.
        return True

    def activity_table_case2(self) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for n_prach_slot in [0, 1, 2]:
            for active_slot in [0, 1]:
                rows.append(
                    {
                        "NPRACHSlot": n_prach_slot,
                        "ActivePRACHSlot": active_slot,
                        "active": self.is_prach_active(n_prach_slot, active_slot, 30),
                    }
                )
        return pd.DataFrame(rows)

    def inspect_configuration(self) -> Dict[str, Any]:
        profile = FORMAT_PROFILES.get(self.prach.preferred_format, FORMAT_PROFILES["B2"])

        read_only = {
            "Format": profile["format"],
            "NumTimeOccasions": int(profile["num_time_occasions"]),
            "PRACHDuration": int(profile["prach_duration"]),
            "SymbolLocation": int(profile["symbol_location"]),
            "SubframesPerPRACHSlot": 1,
            "PRACHSlotsPerPeriod": 10,
        }
        data = asdict(self.prach)
        data.update(read_only)
        return data

    def build_resource_grid(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Build an approximate PRACH resource grid and mapped indices.

        Returns:
            prach_grid: complex grid [subcarrier, symbol]
            prach_symbols: generated PRACH symbols vector
            prach_indices: linear indices in flattened grid where symbols are mapped
        """
        cfg = self.inspect_configuration()
        num_subcarriers = 624
        num_symbols = 14

        prach_grid = np.zeros((num_subcarriers, num_symbols), dtype=np.complex64)

        # Approximate PRACH occupied subcarriers using 6 RB (72 subcarriers)
        rb_start = self.prach.frequency_start
        sc_start = rb_start * 12
        sc_width = 72
        sc_end = min(sc_start + sc_width, num_subcarriers)

        symbol_start = int(cfg["SymbolLocation"])
        symbol_len = int(cfg["PRACHDuration"])
        symbol_end = min(symbol_start + symbol_len, num_symbols)

        active_subcarriers = max(sc_end - sc_start, 0)
        active_symbols = max(symbol_end - symbol_start, 0)

        if active_subcarriers == 0 or active_symbols == 0:
            return prach_grid, np.array([], dtype=np.complex64), np.array([], dtype=np.int64)

        # Deterministic synthetic PRACH symbols for analysis plotting.
        total_symbols = active_subcarriers * active_symbols
        phase = np.linspace(0, 2 * np.pi, total_symbols, endpoint=False)
        prach_symbols = np.exp(1j * phase).astype(np.complex64)

        idx = 0
        indices: List[int] = []
        for sym in range(symbol_start, symbol_end):
            for sc in range(sc_start, sc_end):
                prach_grid[sc, sym] = prach_symbols[idx]
                indices.append(sc * num_symbols + sym)
                idx += 1

        return prach_grid, prach_symbols, np.array(indices, dtype=np.int64)

    def waveform_info_table(self) -> pd.DataFrame:
        """
        Return approximate waveform timing info, inspired by MATLAB display.
        """
        cfg = self.inspect_configuration()
        symbol_location = int(cfg["SymbolLocation"])
        duration = int(cfg["PRACHDuration"])

        rows: List[Dict[str, Any]] = []
        for sym in range(14):
            if symbol_location <= sym < (symbol_location + duration):
                tcp = 180 if sym == symbol_location else 0
                tseq = 1024
                gp = 108 if sym == (symbol_location + duration - 1) else 0
                status = "active"
            elif sym < (symbol_location + duration):
                tcp = 296 if sym % duration == 0 else 0
                tseq = 1024
                gp = 0
                status = "unused_time_occasion"
            else:
                tcp = 0
                tseq = 1024
                gp = 0
                status = "not_used"

            rows.append({"Symbol": sym, "TCP": tcp, "TSEQ": tseq, "GP": gp, "Status": status})

        return pd.DataFrame(rows)

    def plot_resource_grid(self, prach_grid: np.ndarray, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        mask = (np.abs(prach_grid) > 0).astype(np.int32)
        plt.figure(figsize=(10, 5))
        plt.imshow(mask.T, aspect="auto", origin="lower", cmap="Blues")
        plt.xlabel("Subcarrier Index")
        plt.ylabel("OFDM Symbol")
        plt.title("Approximate PRACH Resource Grid (Mapped Area)")
        plt.colorbar(label="Mapped")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def run(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        print("\n=== Supported SCS Combinations (Table 6.3.3.2-1 style) ===")
        scs_df = self.supported_scs_combinations_table()
        print(scs_df.to_string(index=False))
        scs_df.to_csv(output_dir / "supported_scs_combinations.csv", index=False)

        print("\n=== Configure by Preferred Format ===")
        self.select_configuration_index_by_format(self.prach.preferred_format)
        print(f"Preferred format: {self.prach.preferred_format}")
        print(f"Selected configuration index: {self.prach.configuration_index}")
        print(f"Selected time index: {self.prach.time_index}")

        print("\n=== Active PRACH Check: Typical SCS Case (15 kHz) ===")
        active_15 = self.is_prach_active(
            n_prach_slot=self.prach.n_prach_slot,
            active_prach_slot=self.prach.active_prach_slot,
            prach_scs=15,
        )
        print(f"active: {int(active_15)}")

        print("\n=== Active PRACH Check: Alternative SCS Case (30 kHz) ===")
        act_df = self.activity_table_case2()
        print(act_df.to_string(index=False))
        act_df.to_csv(output_dir / "activity_table_30khz.csv", index=False)

        print("\n=== Inspect PRACH Configuration ===")
        cfg = self.inspect_configuration()
        cfg_df = pd.DataFrame(list(cfg.items()), columns=["Property", "Value"])
        print(cfg_df.to_string(index=False))
        cfg_df.to_csv(output_dir / "prach_configuration_inspect.csv", index=False)

        print("\n=== Generate and Map PRACH Symbols to Resource Grid ===")
        prach_grid, prach_symbols, prach_indices = self.build_resource_grid()
        print(f"Grid shape: {prach_grid.shape}")
        print(f"PRACH symbols: {len(prach_symbols)}")
        print(f"Mapped indices: {len(prach_indices)}")

        np.save(output_dir / "prach_grid.npy", prach_grid)
        np.save(output_dir / "prach_symbols.npy", prach_symbols)
        np.save(output_dir / "prach_indices.npy", prach_indices)
        self.plot_resource_grid(prach_grid, output_dir / "prach_resource_grid.png")

        print("\n=== Waveform Timing Info (Approximate) ===")
        info_df = self.waveform_info_table()
        print(info_df.to_string(index=False))
        info_df.to_csv(output_dir / "waveform_info_approx.csv", index=False)

        print(f"\nOutput directory: {output_dir}")


def build_from_sib1(sib1_path: Path, preferred_format: str = "B2") -> PRACHMatlabStyleExample:
    parser = SIB1Parser(str(sib1_path))
    parsed = parser.parse()
    prach_cfg = parsed.get("prach_config", {})

    carrier = CarrierConfig(subcarrier_spacing=15)
    prach = PRACHConfig(
        frequency_range="FR1",
        duplex_mode="FDD",
        configuration_index=int(prach_cfg.get("prach_configuration_index") or 14),
        subcarrier_spacing=15,
        sequence_index=int(prach_cfg.get("prach_root_sequence_index") or 0),
        preamble_index=0,
        restricted_set=str(prach_cfg.get("restricted_set_config") or "UnrestrictedSet"),
        zero_correlation_zone=int(prach_cfg.get("zero_correlation_zone_config") or 0),
        rb_offset=0,
        frequency_start=int(prach_cfg.get("msg1_frequency_start") or 0),
        frequency_index=0,
        time_index=0,
        active_prach_slot=0,
        n_prach_slot=0,
        lra=139,
        preferred_format=preferred_format,
    )

    return PRACHMatlabStyleExample(carrier, prach)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    sib1_path = root / "SIB1.txt"
    output_dir = root / "matlab_style_results"

    runner = build_from_sib1(sib1_path=sib1_path, preferred_format="B2")
    runner.run(output_dir=output_dir)
