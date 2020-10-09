from pytest_pilot import EasyMarker


silo = EasyMarker("silo", cmdoption_short="-Z", mode="silos", has_arg=False)


# note : using a name different from the command name is not really a good practice...
hardfilter = EasyMarker("hf", mode="hard_filter", has_arg=False)


envid = EasyMarker("envid",
                   full_name="environment",
                   mode="extender")

flavour = EasyMarker("flavour",
                     allowed_values=("red", "yellow"),
                     mode="soft_filter")
