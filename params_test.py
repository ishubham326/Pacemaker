import pytest       # run pytest in the directory to run all tests in the file
from params import params as p
from params import params_by_pacing_mode

# these are only put in scope for testing (normally don't do this)
from params import NonNumericParam, NumericParam

class TestNonNumericParam():
    def test_init_1_correct_storage(self):
        programmable_values = ["Off", "DDD", "VDD", "DDI", "DOO", "AOO", "AAI",
                               "VOO", "VVI", "AAT", "VVT", "DDDR", "VDDR", 
                               "DDIR", "DOOR", "AOOR", "AAIR", "VOOR", "VVIR"]

        assert p["mode"].nominal == "DDD"
        assert p["mode"].value == "DDD"
        assert p["mode"].programmable_values == programmable_values

    def test_init_2_bad_key(self):
        with pytest.raises(KeyError):
            NonNumericParam({
                "programable_values": ["Off", "DDD", "VDD", "DDI", "DOO"],
                "nominal":"DDD",
            })
        with pytest.raises(KeyError):
            NonNumericParam({
                "programmable_values": ["Off", "DDD", "VDD", "DDI", "DOO"],
            })

    def test_init_3_bad_programmable_values(self):
        with pytest.raises(AssertionError):
            NonNumericParam({
                "programmable_values": ["Off", 2],
                "nominal":"Off",
            })
        with pytest.raises(AssertionError):
            NonNumericParam({
                "programmable_values": [None, "On"],
                "nominal":"On",
            })

    def test_init_4_bad_nominal(self):
        with pytest.raises(AssertionError):
            NonNumericParam({
                "programmable_values": ["Off", "DDD", "VDD", "DDI", "DOO"],
                "nominal":"On",
            })

    def test_is_valid(self):
        assert p["activity_threshold"].is_valid("V-Low")
        assert not p["activity_threshold"].is_valid("-Low")
         
    def test_set(self):
        assert p["atr_mode"].set("On")
        assert p["atr_mode"].value == "On"

        assert not p["atr_mode"].set(None)
        assert p["atr_mode"].value == "On"

        assert not p["atr_mode"].set("Something")
        assert p["atr_mode"].value == "On"

    def test_get(self):
        p["mode"].set("VVI")
        assert p["mode"].get() == 8

    def test_get_str(self):
        p["mode"].set("VVI")
        assert p["mode"].get_str() == "VVI"

    def test_get_strings(self):
        values = ["Off", "On"]
        assert p["atr_mode"].get_strings() == values

    def test_get_max_value_size_in_bytes(self):
        a_list = [str(i) for i in range(10)]
        m = NonNumericParam({
            "programmable_values":a_list,
            "nominal":a_list[0],
        })
        assert m.get_max_value_size_in_bytes() == 1

        a_list = [str(i) for i in range(255)]
        print(len(a_list))
        m = NonNumericParam({
            "programmable_values":a_list,
            "nominal":a_list[0],
        })
        assert m.get_max_value_size_in_bytes() == 1

        a_list = [str(i) for i in range(256)]
        m = NonNumericParam({
            "programmable_values":a_list,
            "nominal":a_list[0],
        })
        assert m.get_max_value_size_in_bytes() == 2

        a_list = [str(i) for i in range(1000)]
        m = NonNumericParam({
            "programmable_values":a_list,
            "nominal":a_list[0],
        })
        assert m.get_max_value_size_in_bytes() == 2

class TestNumericParam():
    def test_init_1_correct_storage(self):
        programmable_values = [None, {"min":3, "max":21, "increment":3}, 25]

        assert p["rate_smoothing"].nominal == None
        assert p["rate_smoothing"].value == None
        assert p["rate_smoothing"].unit == "%"
        assert p["rate_smoothing"].programmable_values == programmable_values

    def test_init_2_missing_parameter_data(self):
        with pytest.raises(KeyError):
            NumericParam({
                "nominal":120,
                "unit":"ppm",
            })
        with pytest.raises(KeyError):
            NumericParam({
                "programmable_values":[{"min":50, "max":175, "increment":5}],
                "unit":"ppm",
            })
        with pytest.raises(KeyError):
            NumericParam({
                "programmable_values":[{"min":50, "max":175, "increment":5}],
                "nominal":120,
            })

    def test_init_3_missing_min_max_increment(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"max":175, "increment":5}],
                "nominal":120,
                "unit":"ppm",
            })
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":50, "increment":5}],
                "nominal":120,
                "unit":"ppm",
            })
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":50, "max":175}],
                "nominal":120,
                "unit":"ppm",
            })

    def test_init_4_switch_max_min(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":180, "max":175, "increment":5}],
                "nominal":180,
                "unit":"ppm",
            })
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":-10, "max":-100, "increment":5}],
                "nominal":15,
                "unit":"ppm",
            })

    def test_init_5_bad_increment_size(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":50, "max":57, "increment":6}],
                "nominal":50,
                "unit":"ppm",
            })

        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":-50, "max":-5, "increment":6}],
                "nominal":-50,
                "unit":"ppm",
            })
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":-50, "max":-5, "increment":-6}],
                "nominal":-50,
                "unit":"ppm",
            })

    def test_init_6_bad_nominal(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":50, "max":175, "increment":5}],
                "nominal":20,
                "unit":"ppm",
            })
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":50, "max":175, "increment":5}],
                "nominal":51,
                "unit":"ppm",
            })

    def test_init_7_string_programmable_value(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values": ["Off", 2],
                "nominal":2,
                "unit":"%",
            })

    def test_init_8_float_programmable_value(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values": [1.2, 2],
                "nominal":2,
                "unit":"%",
            })

    def test_init_9_programmable_value_order(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":50, "max":75, "increment":5},
                                       {"min":75, "max":175, "increment":10},
                                       20],
                "nominal":55,
                "unit":"ppm",
            })
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":75, "max":175, "increment":5},
                                       {"min":50, "max":75, "increment":10},
                                       20],
                "nominal":55,
                "unit":"ppm",
            })

    def test_init_10_ranges_mutually_exclusive(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values":[{"min":50, "max":75, "increment":5},
                                       {"min":65, "max":175, "increment":10}],
                "nominal":55,
                "unit":"ppm",
            })

    def test_init_11_none_not_first(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values": [1, 2, None,
                                       {"min":65, "max":175, "increment":10}],
                "nominal":2,
                "unit":"%",
            })

    def test_init_12_length(self):
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values": [None],
                "nominal":None,
                "unit":"%",
            })
        with pytest.raises(AssertionError):
            NumericParam({
                "programmable_values": [3],
                "nominal":3,
                "unit":"%",
            })

    def test_is_valid(self):
        assert p["rate_smoothing"].is_valid(None)
        assert p["rate_smoothing"].is_valid(9)
        assert p["rate_smoothing"].is_valid(15)
        assert p["rate_smoothing"].is_valid(25)
        assert not p["rate_smoothing"].is_valid(16)
        assert not p["rate_smoothing"].is_valid(24)
        assert not p["rate_smoothing"].is_valid("Off")
         
    def test_set(self):
        assert p["rate_smoothing"].set(6)
        assert p["rate_smoothing"].value == 6

        assert p["rate_smoothing"].set(25)
        assert p["rate_smoothing"].value == 25

        assert p["rate_smoothing"].set(None)
        assert p["rate_smoothing"].value is None

        assert not p["rate_smoothing"].set(16)
        assert p["rate_smoothing"].value is None

        assert not p["rate_smoothing"].set(24)
        assert p["rate_smoothing"].value is None

        assert not p["rate_smoothing"].set("Something")
        assert p["rate_smoothing"].value is None

    def test_get(self):
        p["rate_smoothing"].set(9)
        assert p["rate_smoothing"].get() == 9

    def test_get_max_value_size_in_bytes(self):
        m = NumericParam({
            "programmable_values": [None, 25, 100, 200],
            "nominal":25,
            "unit":"%",
        })
        assert m.get_max_value_size_in_bytes() == 1
        m = NumericParam({
            "programmable_values": [None, 25,
                                   {"min":65, "max":255, "increment":1}],
            "nominal":25,
            "unit":"%",
        })
        assert m.get_max_value_size_in_bytes() == 1
        m = NumericParam({
            "programmable_values": [21, 64,
                                   {"min":65, "max":256, "increment":1}],
            "nominal":21,
            "unit":"%",
        })
        assert m.get_max_value_size_in_bytes() == 2

    def test_increment_1(self):
        #"programmable_values":[{"min":30, "max":50, "increment":5},
        #                       {"min":51, "max":90, "increment":1},
        #                       {"min":95, "max":175, "increment":5}],
        p["lower_rate_limit"].set(45)
        p["lower_rate_limit"].increment()
        assert p["lower_rate_limit"].get() == 50
        p["lower_rate_limit"].increment()
        assert p["lower_rate_limit"].get() == 51
        p["lower_rate_limit"].increment()
        assert p["lower_rate_limit"].get() == 52
        p["lower_rate_limit"].increment()
        assert p["lower_rate_limit"].get() == 53

        p["lower_rate_limit"].set(89)
        p["lower_rate_limit"].increment()
        assert p["lower_rate_limit"].get() == 90
        p["lower_rate_limit"].increment()
        assert p["lower_rate_limit"].get() == 95
        p["lower_rate_limit"].increment()
        assert p["lower_rate_limit"].get() == 100

        p["lower_rate_limit"].set(175)
        p["lower_rate_limit"].increment()
        assert p["lower_rate_limit"].get() == 175

    def test_increment_2(self):
        # "programmable_values":[None, {"min":3, "max":21, "increment":3}, 25],
        p["rate_smoothing"].set(None)
        p["rate_smoothing"].increment()
        assert p["rate_smoothing"].get() == 3

        p["rate_smoothing"].set(18)
        p["rate_smoothing"].increment()
        assert p["rate_smoothing"].get() == 21
        p["rate_smoothing"].increment()
        assert p["rate_smoothing"].get() == 25
        p["rate_smoothing"].increment()
        assert p["rate_smoothing"].get() == 25

    def test_decrement_1(self):
        #"programmable_values":[{"min":30, "max":50, "increment":5},
        #                       {"min":51, "max":90, "increment":1},
        #                       {"min":95, "max":175, "increment":5}],
        p["lower_rate_limit"].set(175)
        p["lower_rate_limit"].decrement()
        assert p["lower_rate_limit"].get() == 170
        p["lower_rate_limit"].decrement()
        assert p["lower_rate_limit"].get() == 165

        p["lower_rate_limit"].set(100)
        p["lower_rate_limit"].decrement()
        assert p["lower_rate_limit"].get() == 95
        p["lower_rate_limit"].decrement()
        assert p["lower_rate_limit"].get() == 90

        p["lower_rate_limit"].set(40)
        p["lower_rate_limit"].decrement()
        assert p["lower_rate_limit"].get() == 35
        p["lower_rate_limit"].decrement()
        assert p["lower_rate_limit"].get() == 30
        p["lower_rate_limit"].decrement()
        assert p["lower_rate_limit"].get() == 30

    def test_decrement_2(self):
        # "programmable_values":[None, {"min":3, "max":21, "increment":3}, 25],
        p["rate_smoothing"].set(None)
        p["rate_smoothing"].decrement()
        assert p["rate_smoothing"].get() == 3

        p["rate_smoothing"].set(25)
        p["rate_smoothing"].decrement()
        assert p["rate_smoothing"].get() == 21
        p["rate_smoothing"].decrement()
        assert p["rate_smoothing"].get() == 18
        p["rate_smoothing"].decrement()
        assert p["rate_smoothing"].get() == 15

        p["rate_smoothing"].set(9)
        p["rate_smoothing"].decrement()
        assert p["rate_smoothing"].get() == 6
        p["rate_smoothing"].decrement()
        assert p["rate_smoothing"].get() == 3
        p["rate_smoothing"].decrement()
        assert p["rate_smoothing"].get() == 3

class TestParamsByMode():
    def test_values_in_params(self):
        for key in params_by_pacing_mode:
            for element in params_by_pacing_mode[key]:
                assert element in p
