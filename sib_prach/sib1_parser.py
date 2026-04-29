"""
SIB1 로그 파일 파서
5G NR 시스템 정보 블록1 텍스트 형식을 파싱합니다.
"""

import re
from typing import Dict, Any, Optional


class SIB1Parser:
    """SIB1 로그 파일 또는 원문 문자열을 파싱하는 클래스."""

    def __init__(self, file_path: Optional[str] = None, *, text: Optional[str] = None):
        if (not file_path) and text is None:
            raise TypeError("file_path 또는 text= 인자 중 하나는 필수입니다.")
        self.file_path = file_path or ""
        self.content: Optional[str] = text
        self.data: Dict[str, Any] = {}

    def read_file(self) -> str:
        if self.content is not None:
            return self.content
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.content = f.read()
        return self.content

    def parse(self) -> Dict[str, Any]:
        if self.content is None:
            self.read_file()

        self.data = {
            "basic_info": self._parse_basic_info(),
            "prach_config": self._parse_prach_config(),
            "timing_info": self._parse_timing_info(),
            "cell_info": self._parse_cell_info(),
            "dl_config": self._parse_dl_config(),
            "ul_config": self._parse_ul_config(),
        }

        return self.data

    def _extract_value(self, pattern: str, default=None, flags: int = re.IGNORECASE) -> Optional[str]:
        assert self.content is not None
        match = re.search(pattern, self.content, flags)
        if match:
            return match.group(1)
        return default

    def _parse_basic_info(self) -> Dict[str, Any]:
        return {
            "timestamp": self._extract_value(r"\[\s*(\d+\s+\w+\s+\d+\s+[\d:\.]+)\s*\]"),
            "message_type": self._extract_value(r"(systemInformationBlockType1)"),
            "rrc_release": self._extract_value(r"RRC_REL\s*:\s*(\d+)"),
            "sim_index": self._extract_value(r"SIM Index\s*:\s*(\d+)"),
        }

    def _parse_timing_info(self) -> Dict[str, Any]:
        assert self.content is not None
        return {
            "slot_n": self._parse_hex_value(r"Slot_n\s*:\s*(0x[\dA-Fa-f]+)\(\d+\)", self.content),
            "sub_fn": self._parse_hex_value(r"sub_fn\s*:\s*(0x[\dA-Fa-f]+)\(\d+\)", self.content),
            "sfn": self._parse_hex_value(r"sfn\s*:\s*(0x[\dA-Fa-f]+)\(\d+\)", self.content),
        }

    def _parse_cell_info(self) -> Dict[str, Any]:
        return {
            "physical_cell_id": self._extract_value(r"physical_cell_id\s*:\s*(\d+)"),
            "frequency": self._extract_value(r"frequency\s*:\s*(\d+)"),
        }

    def _parse_dl_config(self) -> Dict[str, Any]:
        return {
            "freq_band": self._extract_value(r"freqBandIndicatorNR\s*=\s*(\d+)"),
            "offset_to_point_a": self._extract_value(r"offsetToPointA\s*=\s*(\d+)"),
            "scs": self._extract_value(r"subcarrierSpacing\s*=\s*(kHz\d+)"),
            "carrier_bandwidth": self._extract_value(r"carrierBandwidth\s*=\s*(\d+)"),
        }

    def _parse_ul_config(self) -> Dict[str, Any]:
        return {
            "freq_band_ul": self._extract_value(
                r"frequencyBandList\[0\].*?freqBandIndicatorNR\s*=\s*(\d+)",
                flags=re.IGNORECASE | re.DOTALL,
            ),
            "absolute_freq_point_a": self._extract_value(r"absoluteFrequencyPointA\s*=\s*(\d+)"),
        }

    def _parse_prach_config(self) -> Dict[str, Any]:
        assert self.content is not None
        config: Dict[str, Any] = {}

        prach_idx = self._extract_value(r"prach_ConfigurationIndex\s*=\s*(\d+)")
        config["prach_configuration_index"] = int(prach_idx) if prach_idx else None

        msg1_fdm = self._extract_value(r"msg1_FDM\s*=\s*(\w+)")
        config["msg1_fdm"] = msg1_fdm
        config["msg1_fdm_value"] = self._fdm_to_value(msg1_fdm)

        msg1_freq_start = self._extract_value(r"msg1_FrequencyStart\s*=\s*(\d+)")
        config["msg1_frequency_start"] = int(msg1_freq_start) if msg1_freq_start else None

        zcz = self._extract_value(r"zeroCorrelationZoneConfig\s*=\s*(\d+)")
        config["zero_correlation_zone_config"] = int(zcz) if zcz else None

        preamble_power = self._extract_value(r"preambleReceivedTargetPower\s*=\s*([-\d]+)")
        config["preamble_received_target_power"] = int(preamble_power) if preamble_power else None

        preamble_max = self._extract_value(r"preambleTransMax\s*=\s*(\w+)")
        config["preamble_trans_max"] = preamble_max
        config["preamble_trans_max_value"] = self._preamble_trans_max_to_value(preamble_max)

        power_step = self._extract_value(r"powerRampingStep\s*=\s*(\w+)")
        config["power_ramping_step"] = power_step
        config["power_ramping_step_db"] = self._power_ramping_to_db(power_step)

        ra_window = self._extract_value(r"ra_ResponseWindow\s*=\s*(\w+)")
        config["ra_response_window"] = ra_window
        config["ra_response_window_slots"] = self._ra_window_to_slots(ra_window)

        rsi = self._extract_value(r"prach_RootSequenceIndex\s*=\s*(\d+)")
        if rsi:
            config["prach_root_sequence_index"] = int(rsi)
        else:
            m839 = re.search(
                r"prach_RootSequenceIndex\s*\n\s*l839\s*=\s*(\d+)",
                self.content,
                re.IGNORECASE | re.MULTILINE,
            )
            m139 = re.search(
                r"prach_RootSequenceIndex\s*\n\s*l139\s*=\s*(\d+)",
                self.content,
                re.IGNORECASE | re.MULTILINE,
            )
            if m839:
                config["prach_root_sequence_index"] = int(m839.group(1))
            elif m139:
                config["prach_root_sequence_index"] = int(m139.group(1))
            else:
                config["prach_root_sequence_index"] = None

        restricted = self._extract_value(r"restrictedSetConfig\s*=\s*(\w+)")
        config["restricted_set_config"] = restricted

        return config

    @staticmethod
    def _parse_hex_value(pattern: str, content: str) -> Optional[int]:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return int(match.group(1), 16)
        return None

    @staticmethod
    def _fdm_to_value(fdm_str: str) -> Optional[int]:
        fdm_map = {"one": 1, "two": 2, "four": 4, "eight": 8}
        return fdm_map.get(fdm_str.lower()) if fdm_str else None

    @staticmethod
    def _preamble_trans_max_to_value(preamble_str: str) -> Optional[int]:
        preamble_map = {
            "n3": 3,
            "n4": 4,
            "n5": 5,
            "n6": 6,
            "n7": 7,
            "n8": 8,
            "n10": 10,
            "n20": 20,
            "n50": 50,
            "n100": 100,
            "n200": 200,
        }
        return preamble_map.get(preamble_str.lower()) if preamble_str else None

    @staticmethod
    def _power_ramping_to_db(power_str: str) -> Optional[float]:
        power_map = {"db2": 2.0, "db4": 4.0, "db6": 6.0, "db8": 8.0}
        return power_map.get(power_str.lower()) if power_str else None

    @staticmethod
    def _ra_window_to_slots(window_str: str) -> Optional[int]:
        window_map = {
            "sl1": 1,
            "sl2": 2,
            "sl4": 4,
            "sl8": 8,
            "sl10": 10,
            "sl20": 20,
            "sl40": 40,
            "sl80": 80,
            "sl160": 160,
        }
        return window_map.get(window_str.lower()) if window_str else None

    def get_prach_config(self) -> Dict[str, Any]:
        if not self.data:
            self.parse()
        return self.data.get("prach_config", {})

    def get_timing_info(self) -> Dict[str, Any]:
        if not self.data:
            self.parse()
        return self.data.get("timing_info", {})
