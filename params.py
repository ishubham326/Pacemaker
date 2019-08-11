"""
USAGE
-----
from params import params as p

MODULE PURPOSE
--------------
The module provides means to set and get parameter values.

It also stores information about what values a parameter may have, and what 
the nominal value is for each parameter.

The parameters are described in the following places in the documentation:
    1.  SRS 3.1 (minimal set)
    2.  PACEMAKER page 28 (showing in which mode each parameter is used)
    3.  PACEMAKER Appendix A (all parameters, values, increment, nominal, 
        tolerance)

MODULE SECRETS
--------------
    - The parameters are divided into numeric and non-numeric types.
        - each parameter has a set of allowed values
            - numeric allowed values are described with ranges or individual
              integers
                - those described with ranges have an increment size
                - these are ordered from minimum to maximum 
                - ranges and individual integers do not overlap 
            - non-numeric allowed values are described with an ordered
              collection (list) of strings
        - numeric values must be integers or None (Off)
        - non-numeric values must be strings

    - The file is partially data, and contains two classes, one for numeric and
      one for non-numeric parameters.
        - on module load, instances of the classes are initialized with data
          from the PACEMAKER document Table 7 in Appendix A.
        - the classes are stored in a dictionary (params) and accessed by key.
        - the dictionary keys are the parameter names

NOTES
-----
    - The value returned by the get method must be transmittable over serial 
      in the required format.

    - for numeric types, write ranges in order from lowest to highest range
        - more readable

    - we could have used range() function to generate ranges
        - this would have saved a lot of design time
        - makes code less readable and reduces speed

TODO
----
    - store param_data inputs to classes as self.__param_data in order to
      make it more clear to programmers that this data is meant to be private.
    - some ppm values have tolerances in ms
        - ignore tolerances for now
        - do we have to send tolerances to the pacemaker or track it?

    - did I interpret the meaning of the increment properly?
        - how much you can increment parameters by using the GUI buttons?
"""

class NonNumericParam():
    """ Verify that the inputs are correct and initialize instance. """
    def __init__(self, param_data):
        self.programmable_values = param_data["programmable_values"]

        for v in self.programmable_values:
            assert isinstance(v, str)
        
        assert self.is_valid(param_data["nominal"])

        self.nominal = param_data["nominal"]
        self.value = self.nominal

    """ Check if value is a valid value for parameter. """
    def is_valid(self, value):
        return (value in self.programmable_values)

    """ We will send the index when doing serial communication. """
    def get(self):
        return self.programmable_values.index(self.value)

    """ Return current value as a string. """
    def get_str(self):
        return self.value

    """ Return valid values as a list of strings. """
    def get_strings(self):
        return self.programmable_values

    """ Return the max number of bytes required to represent self.value."""
    def get_max_value_size_in_bytes(self):
        return ((len(self.programmable_values).bit_length() - 1) // 8) + 1

    """ If value is correct, set parameter to that value. """
    def set(self, value):
        is_set = False

        if self.is_valid(value):
            self.value = value
            is_set = True

        return is_set

class NumericParam():
    """ 
    Verify that the inputs are correct and initialize instance. 
    Correct programmable_values lists have the following features:
        - composed of dictionaries, integers, and None
        - at least two entries
        - if None is included, it must be the first entry
        - each dictionary must have a min, max, and increment
        - the dictionary 
    """
    def __init__(self, param_data):
        self.programmable_values = param_data["programmable_values"]

        # check types, existence of keys, and position of None (if included)
        includes_dictionary = False
        for idx,v in enumerate(self.programmable_values):
            assert (v is None) or isinstance(v, dict) or isinstance(v, int)
            if isinstance(v, dict):
                assert "max" in v and isinstance(v["max"], int)
                assert "min" in v and isinstance(v["min"], int)
                assert "increment" in v and isinstance(v["increment"], int)
                includes_dictionary = True

            if v is None:
                assert idx == 0
        
        if not includes_dictionary:
            assert len(self.programmable_values) > 1
        
        # choose initial value for variable previous
        if self.programmable_values[0] is not None:
            if isinstance(self.programmable_values[0], dict):
                previous = self.programmable_values[0]["min"] - 1
            elif isinstance(self.programmable_values[0], int):
                previous = self.programmable_values[0] - 1
            else:
                assert False    # this should not happen
        else:
            if isinstance(self.programmable_values[1], dict):
                previous = self.programmable_values[1]["min"] - 1
            elif isinstance(self.programmable_values[1], int):
                previous = self.programmable_values[1] - 1
            else:
                assert False    # this should not happen

        # check order of programmable values
        for idx,v in enumerate(self.programmable_values):
            if isinstance(v, dict):
                assert v["min"] < v["max"]
                assert ((v["max"] - v["min"]) % v["increment"]) == 0
                assert v["min"] > previous
                previous = v["max"]
            elif isinstance(v, int):
                assert v > previous
                previous = v

        # make sure the nominal value fits
        assert self.is_valid(param_data["nominal"])

        # TODO... hide these a little by keeping them in the dictionary or by
        # name mangling?
        self.nominal = param_data["nominal"]
        self.unit = param_data["unit"]
        self.value = self.nominal
    
    """ Check if value is valid using the programmable_values list. """
    def is_valid(self, value):
        return_value = False

        for r in self.programmable_values:
            if value is not None and not isinstance(value, int):
                break
            elif value is None:
                return_value = (r is None)  # this depends on None being first in the list
                break
            elif isinstance(r, dict) and (r["min"] <= value) and (value <= r["max"]):
                return_value = ((value - r["min"]) % r["increment"] == 0)
                break
            elif r == value:
                return_value = True
                break
        
        return return_value

    """ Get current parameter value. """
    def get(self):
        return self.value

    """ 
    Return the max number of bytes required to represent self.value.
    Currently this won't work properly for signed values.
    TODO: make it work for signed values too.
    """
    def get_max_value_size_in_bytes(self):
        max_prog_val = self.programmable_values[-1]

        if isinstance(max_prog_val, dict):
            max_value = max_prog_val["max"]
        else:
            max_value = max_prog_val

        num_bits = max_value.bit_length()
        return ((num_bits - 1) // 8) + 1

    """ Set parameter value to input if the input is valid. """
    def set(self, value):
        is_set = False

        if self.is_valid(value):
            self.value = value
            is_set = True

        return is_set

    """ Assumes that the first entry is None. Call this to get the minimum value. 
    TODO: fix this so that it checks for None"""
    def set_to_min_value(self):
        value = self.programmable_values[1]

        if isinstance(value, dict):
            self.value = value["min"]
        elif isinstance(value, int):
            self.value = value

    """ Increment current value of the parameter. If it is max, do nothing. """
    def increment(self):
        if self.value is None:
            self.set_to_min_value()
        else:
            found_value = False

            for r in self.programmable_values:
                if found_value:
                    if isinstance(r, dict):
                        self.value = r["min"]
                    elif isinstance(r, int):
                        self.value = r
                    break
                else:
                    if isinstance(r, dict) and (r["min"] <= self.value) and (self.value <= r["max"]):
                        tentative = self.value + r["increment"]
                        if r["min"] <= tentative and tentative <= r["max"]:
                            self.value = tentative
                        else:
                            found_value = True
                    elif isinstance(r, int) and r == self.value:
                        found_value = True

    """ Decrement current value of the parameter. If it is min, do nothing. """
    def decrement(self):
        if self.value is None:
            self.set_to_min_value()
        else:
            found_value = False

            for r in reversed(self.programmable_values):
                if found_value:
                    if isinstance(r, dict):
                        self.value = r["max"]
                    elif isinstance(r, int):
                        self.value = r
                    break
                else:
                    if isinstance(r, dict) and (r["min"] <= self.value) and (self.value <= r["max"]):
                        tentative = self.value - r["increment"]
                        if r["min"] <= tentative and tentative <= r["max"]:
                            self.value = tentative
                        else:
                            found_value = True
                    elif isinstance(r, int) and r == self.value:
                        found_value = True

""" 
Build the module datastructure.
Each parameter name is a key in params. The value assigned to the key is an 
object. On initialization of the module, each object's constructer is called 
and passed in a list of possible values, a nominal value, and if numeric, a 
unit.
""" 
params = {
    "mode":NonNumericParam({
        "programmable_values":["Off", "DDD", "VDD", "DDI", "DOO", "AOO", "AAI",
                               "VOO", "VVI", "AAT", "VVT", "DDDR", "VDDR", 
                               "DDIR", "DOOR", "AOOR", "AAIR", "VOOR", "VVIR"],
        "nominal":"DDD",
    }),
    "lower_rate_limit":NumericParam({
        "programmable_values":[{"min":30, "max":50, "increment":5},
                               {"min":51, "max":90, "increment":1},
                               {"min":95, "max":175, "increment":5}],
        "nominal":60,
        "unit":"ppm",
    }),
    "upper_rate_limit":NumericParam({
        "programmable_values":[{"min":50, "max":175, "increment":5}],
        "nominal":120,
        "unit":"ppm",
    }),
    "max_sensor_rate":NumericParam({
        "programmable_values":[{"min":50, "max":175, "increment":5}],
        "nominal":120,
        "unit":"ppm",
    }),
    "fixed_av_delay":NumericParam({
        "programmable_values":[{"min":70, "max":300, "increment":10}],
        "nominal":150,
        "unit":"ms",
    }),
    "dynamic_av_delay":NonNumericParam({
        "programmable_values":["Off", "On"],
        "nominal":"Off",
    }),
    "min_dynamic_av_delay":NumericParam({
        "programmable_values":[{"min":30, "max":100, "increment":10}],
        "nominal":50,
        "unit":"ms",
    }),
    "sensed_av_delay_offset":NumericParam({
        "programmable_values":[None, {"min":-100, "max":-10, "increment":-10}],
        "nominal":None,
        "unit":"ms",
    }),
    "a_pulse_amplitude_regulated":NumericParam({
        "programmable_values":[None, {"min":500, "max":3200, "increment":100},
                                     {"min":3500, "max":7000, "increment":500}],
        "nominal":3500,
        "unit":"mV",
    }),
    "v_pulse_amplitude_regulated":NumericParam({
        "programmable_values":[None, {"min":500, "max":3200, "increment":100},
                                     {"min":3500, "max":7000, "increment":500}],
        "nominal":3500,
        "unit":"mV",
    }),
    "a_pulse_amplitude_unregulated":NumericParam({
        "programmable_values":[None, {"min":1250, "max": 5000, "increment": 1250}],
        "nominal":3750,
        "unit":"mV",
    }),
    "v_pulse_amplitude_unregulated":NumericParam({
        "programmable_values":[None, {"min":1250, "max": 5000, "increment": 1250}],
        "nominal":3750,
        "unit":"mV",
    }),
    "a_pulse_width":NumericParam({
        "programmable_values":[50, {"min":100, "max":1900, "increment":100}],
        "nominal":400,
        "unit":"us",
    }),
    "v_pulse_width":NumericParam({
        "programmable_values":[50, {"min":100, "max":1900, "increment":100}],
        "nominal":400,
        "unit":"us",
    }),
    "a_sensitivity":NumericParam({
        "programmable_values":[250, 500, 750, {"min":1000, "max":10000, "increment":500}],
        "nominal":750,
        "unit":"uV",
    }),
    "v_sensitivity":NumericParam({
        "programmable_values":[250, 500, 750, {"min":1000, "max":10000, "increment":500}],
        "nominal":2500,
        "unit":"uV",
    }),
    "v_refractory_period":NumericParam({
        "programmable_values":[{"min":150, "max":500, "increment":10}],
        "nominal":320,
        "unit":"ms",
    }),
    "a_refractory_period":NumericParam({
        "programmable_values":[{"min":150, "max":500, "increment":10}],
        "nominal":250,
        "unit":"ms",
    }),
    "pvarp":NumericParam({
        "programmable_values":[{"min":150, "max":500, "increment":10}],
        "nominal":250,
        "unit":"ms",
    }),
    "pvarp_extension":NumericParam({
        "programmable_values":[None, {"min":50, "max":400, "increment":50}],
        "nominal":None,
        "unit":"ms",
    }),
    "hysteresis_rate_limit":NumericParam({
        "programmable_values":[None, {"min":30, "max":50, "increment":5},
                                     {"min":51, "max":90, "increment":1},
                                     {"min":95, "max":175, "increment":5}],
        "nominal":None,
        "unit":"ppm",
    }),
    "rate_smoothing":NumericParam({
        "programmable_values":[None, {"min":3, "max":21, "increment":3}, 25],
        "nominal":None,
        "unit":"%",
    }),
    "atr_mode":NonNumericParam({
        "programmable_values":["Off", "On"],
        "nominal":"Off",
    }),
    "atr_duration":NumericParam({
        "programmable_values":[10, {"min":20, "max":80, "increment":20},
                                   {"min":100, "max":2000, "increment":100}],
        "nominal":20,
        "unit":"cc",
    }),
    "atr_fallback_time":NumericParam({
        "programmable_values":[{"min":1, "max":5, "increment":1}],
        "nominal":1,
        "unit":"min",
    }),
    "ventricular_blanking":NumericParam({
        "programmable_values":[{"min":30, "max":60, "increment":10}],
        "nominal":40,
        "unit":"ms",
    }),
    "activity_threshold":NonNumericParam({
        "programmable_values":["V-Low", "Low", "Med-Low", "Med", "Med-High", 
                               "High", "V-High"],
        "nominal":"Med",
    }),
    "reaction_time":NumericParam({
        "programmable_values":[{"min":10, "max":50, "increment":10}],
        "nominal":30,
        "unit":"sec",
    }),
    "response_factor":NumericParam({
        "programmable_values":[{"min":1, "max":16, "increment":1}],
        "nominal":8,
        "unit":"",
    }),
    "recovery_time":NumericParam({
        "programmable_values":[{"min":2, "max":16, "increment":1}],
        "nominal":5,
        "unit":"min",
    }),
}

"""
It doesn't matter if we use a lot of memory here.
Allows the user to check what parameters are meaningful for a given mode.

Test by checking for typos (for each key, are the list elements in params?)
"""
params_by_pacing_mode = {
    "VOO":["lower_rate_limit", 
           "upper_rate_limit",
           "v_pulse_amplitude_unregulated", # is regulated for the xxxR modes?
           "v_pulse_width",
          ],
    "AOO":["lower_rate_limit", 
           "upper_rate_limit",
           "a_pulse_amplitude_unregulated",
           "a_pulse_width",
          ],
    "VVI":["lower_rate_limit",
           "upper_rate_limit",              # not asked for in srsVVI
           "v_pulse_amplitude_unregulated",
           "v_pulse_width",
           "v_sensitivity",
           "v_refractory_period",
           "hysteresis_rate_limit",
           "rate_smoothing",
          ],
    "AAI":["lower_rate_limit", 
           "upper_rate_limit",
           "a_pulse_amplitude_unregulated",
           "a_pulse_width",
           "a_sensitivity",
           "a_refractory_period",
           "pvarp",
           "hysteresis_rate_limit",
           "rate_smoothing",
          ],
    "AAT":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",
            "a_pulse_amplitude_unregulated",
            "a_pulse_width",
            "a_sensitivity",
            "a_refractory_period",
            "pvarp",
            ],
    "VVT":["lower_rate_limit",
            "upper_rate_limit",
            "v_pulse_amplitude_unregulated",
            "v_pulse_width",
            "v_sensitivity",
            "v_refractory_period",
            ],
    "VVD":["lower_rate_limit",
            "upper_rate_limit",
            "fixed_av_delay",
            "dynamic_av_delay",           
            "v_pulse_width",           
            "v_sensitivity",
            "v_refractory_period",          
            "pvarp_extension",
            "hysteresis_rate_limit",
            "rate_smoothing",
            "atr_mode",
            "atr_duration",
            "atr_fallback_time",            
            ],
    "DOO":["lower_rate_limit",
            "upper_rate_limit",
            "fixed_av_delay",
            "a_pulse_amplitude_unregulated",
            "v_pulse_amplitude_unregulated",
            "a_pulse_width",
            "v_pulse_width",
            ],
    "DDI":["lower_rate_limit",
            "upper_rate_limit",            
            "fixed_av_delay",
            "a_pulse_amplitude_unregulated",
            "v_pulse_amplitude_unregulated",
            "a_pulse_width",
            "v_pulse_width",
            "a_sensitivity",
            "v_sensitivity",
            "v_refractory_period",
            "a_refractory_period",
            "pvarp",           
            ],
    "DDD":["lower_rate_limit",
            "upper_rate_limit",
            "fixed_av_delay",
            "dynamic_av_delay",
            "min_dynamic_av_delay",
            "sensed_av_delay_offset",
            "a_pulse_amplitude_unregulated",
            "v_pulse_amplitude_unregulated",
            "a_pulse_width",
            "v_pulse_width",
            "a_sensitivity",
            "v_sensitivity",
            "v_refractory_period",
            "a_refractory_period",
            "pvarp",
            "pvarp_extension",
            "hysteresis_rate_limit",
            "rate_smoothing",
            "atr_mode",
            "atr_duration",
            "atr_fallback_time",
            "ventricular_blanking",
            "activity_threshold",
            ],
    "AOOR":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",            
            "a_pulse_amplitude_regulated",            
            "a_pulse_width",
            "activity_threshold",
            "reaction_time",
            "response_factor",
            "recovery_time",
            ],
    "AAIR":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",            
            "a_pulse_amplitude_regulated",           
            "a_pulse_width",            
            "a_sensitivity",
            "a_refractory_period",
            "pvarp",           
            "hysteresis_rate_limit",
            "rate_smoothing",          
            "activity_threshold",
            "reaction_time",
            "response_factor",
            "recovery_time",
            ],
    "VOOR":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",            
            "v_pulse_amplitude_regulated",
            "v_pulse_width",          
            "activity_threshold",
            "reaction_time",
            "response_factor",
            "recovery_time",
            ],
    "VVIR":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",            
            "v_pulse_amplitude_regulated",
            "v_pulse_width",          
            "v_sensitivity",
            "v_refractory_period",
            "hysteresis_rate_limit",
            "rate_smoothing",
            "activity_threshold",
            "reaction_time",
            "response_factor",
            "recovery_time",
            ],
    "VDDR":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",
            "fixed_av_delay",
            "dynamic_av_delay",
            "min_dynamic_av_delay",            
            "v_pulse_amplitude_regulated",            
            "v_pulse_width",        
            "v_sensitivity",
            "v_refractory_period",
            "pvarp_extension",
            "rate_smoothing",
            "atr_mode",
            "atr_duration",
            "atr_fallback_time",
            "ventricular_blanking",
            "activity_threshold",
            "reaction_time",
            "response_factor",
            "recovery_time",
            ],
    "DOOR":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",
            "fixed_av_delay",
            "a_pulse_amplitude_regulated",
            "min_dynamic_av_delay",            
            "v_pulse_amplitude_regulated",
            "a_pulse_width",
            "v_pulse_width",        
            "activity_threshold",
            "reaction_time",
            "response_factor",
            "recovery_time",
            ],
    "DDIR":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",
            "fixed_av_delay",
            "a_pulse_amplitude_regulated",
            "min_dynamic_av_delay",            
            "v_pulse_amplitude_regulated",
            "a_pulse_width",
            "v_pulse_width",
            "v_sensitivity",
            "v_refractory_period",
            "a_refractory_period",
            "pvarp",
            "activity_threshold",
            "reaction_time",
            "response_factor",
            "recovery_time",
            ],
    "DDDR":["lower_rate_limit",
            "upper_rate_limit",
            "max_sensor_rate",
            "fixed_av_delay",
            "dynamic_av_delay",
            "min_dynamic_av_delay",
            "sensed_av_delay_offset",
            "a_pulse_amplitude_regulated",
            "v_pulse_amplitude_regulated",
            "a_pulse_amplitude_unregulated",
            "v_pulse_amplitude_unregulated",
            "a_pulse_width",
            "v_pulse_width",
            "a_sensitivity",
            "v_sensitivity",
            "v_refractory_period",
            "a_refractory_period",
            "pvarp",
            "pvarp_extension",
            "hysteresis_rate_limit",
            "rate_smoothing",
            "atr_mode",
            "atr_duration",
            "atr_fallback_time",
            "ventricular_blanking",
            "activity_threshold",
            "reaction_time",
            "response_factor",
            "recovery_time",
            ],    
}
