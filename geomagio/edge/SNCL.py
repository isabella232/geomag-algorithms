from __future__ import annotations
from typing import Dict, Optional

from pydantic import BaseModel

ELEMENT_CONVERSIONS = {
    # e-field
    "E-E": "QE",
    "E-N": "QN",
    # derived indicies
    "Dst3": "X3",
    "Dst4": "X4",
}

CHANNEL_CONVERSIONS = {
    ELEMENT_CONVERSIONS[key]: key for key in ELEMENT_CONVERSIONS.keys()
}


class SNCL(BaseModel):
    station: str = None
    network: str = "NT"
    channel: str = None
    location: str = None

    def get_sncl(
        self,
        station: str,
        data_type: str,
        interval: str,
        element: str,
    ) -> SNCL:
        from .SNCLFactory import SNCLFactory

        factory = SNCLFactory(data_format="miniseed")
        return SNCL(
            station=station,
            network=self.network,
            channel=factory.get_channel(element=element, interval=interval),
            location=factory.get_location(element=element, data_type=data_type),
        )

    def parse_sncl(self) -> Dict:
        return {
            "station": self.station,
            "network": self.network,
            "data_type": self.data_type,
            "element": self.element,
            "interval": self.interval,
        }

    @property
    def data_type(self) -> str:
        """Translates beginning of location code to data type"""
        location_start = self.location[0]
        if location_start == "R":
            return "variation"
        elif location_start == "A":
            return "adjusted"
        elif location_start == "Q":
            return "quasi-definitive"
        elif location_start == "D":
            return "definitive"
        raise ValueError(f"Unexpected location start: {location_start}")

    @property
    def element(self) -> str:
        predefined_element = self.__check_predefined_element()
        element = self.__get_element()
        return predefined_element or element

    @property
    def interval(self) -> str:
        """Translates beginning of channel to interval"""
        channel_start = self.channel[0]
        if channel_start == "B":
            return "tenhertz"
        elif channel_start == "L":
            return "second"
        elif channel_start == "U":
            return "minute"
        elif channel_start == "R":
            return "hour"
        elif channel_start == "P":
            return "day"
        raise ValueError(f"Unexcepted interval code: {channel_start}")

    def __get_element(self):
        """Translates channel/location to element"""
        element_start = self.channel[2]
        channel = self.channel
        channel_middle = channel[1]
        location_end = self.location[1]
        if channel_middle == "E":
            element_end = "_Volt"
        elif channel_middle == "Y":
            element_end = "_Bin"
        elif channel_middle == "K":
            element_end = "_Temp"
        elif location_end == "1":
            element_end = "_Sat"
        elif location_end == "D":
            element_end = "_Dist"
        elif location_end == "Q":
            element_end = "_SQ"
        elif location_end == "V":
            element_end = "_SV"
        else:
            element_end = ""
        return element_start + element_end

    def __check_predefined_element(self) -> Optional[str]:
        channel = self.channel
        channel_end = channel[1:]
        if channel_end in CHANNEL_CONVERSIONS:
            return CHANNEL_CONVERSIONS[channel_end]
        return None
