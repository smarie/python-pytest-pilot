from pytest_pilot import EasyMarker


silomarker = EasyMarker("silo", cmdoption_short="-Z", mode="silos", has_arg=False)


hardfilter = EasyMarker("hf", mode="hard_filter", has_arg=False)


envmarker = EasyMarker("envid",
                       full_name="environment",
                       mode="extender")

flavourmarker = EasyMarker("flavour",
                           allowed_values=("red", "yellow"),
                           mode="soft_filter")
