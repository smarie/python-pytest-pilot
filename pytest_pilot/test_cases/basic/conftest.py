from pytest_pilot import EasyMarker

flavourmarker = EasyMarker('flavour', allowed_values=('red', 'yellow'))
envmarker = EasyMarker('envid', 'environment', not_filtering_skips_marked=True)
