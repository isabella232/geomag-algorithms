from typing import Optional

import typer

from ..algorithm import Algorithm, FilterAlgorithm
from ..edge import EdgeFactory, MiniSeedFactory
from ..Controller import (
    Controller,
    get_realtime_interval,
)
from ..TimeseriesFactory import TimeseriesFactory
from .factory import get_edge_factory, get_miniseed_factory


def main():
    typer.run(obsrio_filter)


def obsrio_filter(
    interval: str,
    observatory: str,
    input_factory: Optional[str] = None,
    host: str = "127.0.0.1",
    port: str = 2061,
    output_factory: Optional[str] = None,
    output_port: int = typer.Option(
        2061, help="Port where output factory writes data."
    ),
    output_read_port: int = typer.Option(
        2061, help="Port where output factory reads data"
    ),
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    if interval == "realtime":
        filter_realtime(
            observatory=observatory,
            input_factory=input_factory,
            host=host,
            port=port,
            output_factory=output_factory,
            output_port=output_port,
            output_read_port=output_read_port,
            realtime_interval=realtime_interval,
            update_limit=update_limit,
        )
    elif interval in ["hour", "day"]:
        input_factory = EdgeFactory(host=host, port=port)
        output_factory = MiniSeedFactory(
            host=host, port=output_read_port, write_port=output_port
        )
        if interval == "hour":
            obsrio_hour(
                observatory=observatory,
                input_factory=input_factory,
                output_factory=output_factory,
                realtime_interval=realtime_interval,
                update_limit=update_limit,
            )
        elif interval == "days":
            obsrio_day(
                observatory=observatory,
                input_factory=input_factory,
                output_factory=output_factory,
                realtime_interval=realtime_interval,
                update_limit=update_limit,
            )
    else:
        raise ValueError("Invalid interval")


def filter_realtime(
    observatory: str,
    input_factory: Optional[str] = None,
    host: str = "127.0.0.1",
    port: str = 2061,
    output_factory: Optional[str] = None,
    output_port: int = typer.Option(
        2061, help="Port where output factory writes data."
    ),
    output_read_port: int = typer.Option(
        2061, help="Port where output factory reads data"
    ),
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter 10Hz miniseed, 1 second, one minute, and temperature data.
    Defaults set for realtime processing; can also be implemented to update legacy data"""
    if input_factory == "miniseed":
        input_factory = MiniSeedFactory(host=host, port=port)
    elif input_factory == "edge":
        input_factory = EdgeFactory(host=host, port=port)
    if output_factory == "miniseed":
        output_factory = MiniSeedFactory(
            host=host, port=output_read_port, write_port=output_port
        )
    elif output_factory == "edge":
        output_factory = EdgeFactory(
            host=host, port=output_read_port, write_port=output_port
        )

    obsrio_tenhertz(
        observatory=observatory,
        input_factory=input_factory,
        output_factory=output_factory,
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )
    obsrio_second(
        observatory=observatory,
        input_factory=input_factory,
        output_factory=output_factory,
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )
    obsrio_minute(
        observatory=observatory,
        input_factory=input_factory,
        output_factory=output_factory,
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )
    obsrio_temperatures(
        observatory=observatory,
        input_factory=input_factory,
        output_factory=output_factory,
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )


def obsrio_day(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 86400,
    update_limit: int = 7,
):
    """Filter 1 second edge H,E,Z,F to 1 day miniseed U,V,W,F."""
    starttime, endtime = get_realtime_interval(realtime_interval)
    # filter 10Hz U,V,W to H,E,Z
    controller = Controller(
        inputFactory=input_factory or get_edge_factory(data_type="variation"),
        inputInterval="minute",
        outputFactory=output_factory or get_miniseed_factory(data_type="variation"),
        outputInterval="day",
    )
    renames = {"H": "U", "E": "V", "Z": "W", "F": "F"}
    for input_channel in renames.keys():
        output_channel = renames[input_channel]
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=60.0,
                output_sample_period=86400.0,
                inchannels=(input_channel,),
                outchannels=(output_channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(input_channel,),
            output_channels=(output_channel,),
            realtime=realtime_interval,
            rename_output_channel=((input_channel, output_channel),),
            update_limit=update_limit,
        )


def obsrio_hour(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter 1 second edge H,E,Z,F to 1 hour miniseed U,V,W,F."""
    starttime, endtime = get_realtime_interval(realtime_interval)
    # filter 10Hz U,V,W to H,E,Z
    controller = Controller(
        inputFactory=input_factory or get_edge_factory(data_type="variation"),
        inputInterval="minute",
        outputFactory=output_factory or get_miniseed_factory(data_type="variation"),
        outputInterval="hour",
    )
    renames = {"H": "U", "E": "V", "Z": "W", "F": "F"}
    for input_channel in renames.keys():
        output_channel = renames[input_channel]
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=60.0,
                output_sample_period=3600.0,
                inchannels=(input_channel,),
                outchannels=(output_channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(input_channel,),
            output_channels=(output_channel,),
            realtime=realtime_interval,
            rename_output_channel=((input_channel, output_channel),),
            update_limit=update_limit,
        )


def obsrio_minute(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter 1Hz legacy H,E,Z,F to 1 minute legacy.

    Should be called after obsrio_second() and obsrio_tenhertz(),
    which populate 1Hz legacy H,E,Z,F.
    """
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        inputFactory=input_factory or get_edge_factory(data_type="variation"),
        inputInterval="second",
        outputFactory=output_factory or get_edge_factory(data_type="variation"),
        outputInterval="minute",
    )
    for channel in ["H", "E", "Z", "F"]:
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=1,
                output_sample_period=60,
                inchannels=(channel,),
                outchannels=(channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(channel,),
            output_channels=(channel,),
            realtime=realtime_interval,
            update_limit=update_limit,
        )


def obsrio_second(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Copy 1Hz miniseed F to 1Hz legacy F."""
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        algorithm=Algorithm(inchannels=("F",), outchannels=("F",)),
        inputFactory=input_factory or get_miniseed_factory(data_type="variation"),
        inputInterval="second",
        outputFactory=output_factory or get_edge_factory(data_type="variation"),
        outputInterval="second",
    )
    controller.run_as_update(
        observatory=(observatory,),
        output_observatory=(observatory,),
        starttime=starttime,
        endtime=endtime,
        input_channels=("F",),
        output_channels=("F",),
        realtime=realtime_interval,
        update_limit=update_limit,
    )


def obsrio_temperatures(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter temperatures 1Hz miniseed (LK1-4) to 1 minute legacy (UK1-4)."""
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        inputFactory=input_factory or get_miniseed_factory(data_type="variation"),
        inputInterval="second",
        outputFactory=output_factory or get_edge_factory(data_type="variation"),
        outputInterval="minute",
    )
    renames = {"LK1": "UK1", "LK2": "UK2", "LK3": "UK3", "LK4": "UK4"}
    for input_channel in renames.keys():
        output_channel = renames[input_channel]
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=1,
                output_sample_period=60,
                inchannels=(input_channel,),
                outchannels=(output_channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(input_channel,),
            output_channels=(output_channel,),
            realtime=realtime_interval,
            rename_output_channel=((input_channel, output_channel),),
            update_limit=update_limit,
        )


def obsrio_tenhertz(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter 10Hz miniseed U,V,W to 1Hz legacy H,E,Z."""
    starttime, endtime = get_realtime_interval(realtime_interval)
    # filter 10Hz U,V,W to H,E,Z
    controller = Controller(
        inputFactory=input_factory or get_miniseed_factory(data_type="variation"),
        inputInterval="tenhertz",
        outputFactory=output_factory or get_edge_factory(data_type="variation"),
        outputInterval="second",
    )
    renames = {"U": "H", "V": "E", "W": "Z"}
    for input_channel in renames.keys():
        output_channel = renames[input_channel]
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=0.1,
                output_sample_period=1,
                inchannels=(input_channel,),
                outchannels=(output_channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(input_channel,),
            output_channels=(output_channel,),
            realtime=realtime_interval,
            rename_output_channel=((input_channel, output_channel),),
            update_limit=update_limit,
        )
