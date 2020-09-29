from pytest_pilot import EasyMarker

envid = EasyMarker('envid', mode='hard_filter')
slow = EasyMarker('slow', has_arg=False, mode='extender')
