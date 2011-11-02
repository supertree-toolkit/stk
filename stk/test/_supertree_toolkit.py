import unittest
import math
import sys
sys.path.append("../common")
import detect_notches
import notchio
import os

class TestDetectNotches(unittest.TestCase):

    def test_simpleCase(self):
        # create config file - just the bits we need
        # remembering it gets passed other functions too...
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 1000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'constant.csv'
        forward_config['input_dir'] = 'data'
        forward_config['simulation_name'] = 'simple'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        # should be one notch at 0m height with a time of 1000 years
        nNotches = len(notches)
        self.assertEqual(nNotches,1)
        # NOTE: half a dx range either side of 0
        self.assert_(-0.12500001 < notches[0] < 0.12500001,"Notch at: "+str(notches[0]))
        self.assertEqual(notch_times[0],1000.)

    def test_simpleCaseHiRes(self):
        # same as above - the simple 90 deg cliff of Pirazzoli
        # with much higher spatial resolution this time
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 1000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'constant.csv'
        forward_config['input_dir'] = 'data'
        forward_config['simulation_name'] = 'pirazzoli_90'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        # should be one notch at 0m height with a time of 1000 years
        nNotches = len(notches)
        self.assertEqual(nNotches,1)
        # NOTE: half a dx range either side of 0
        self.assert_(-0.05 < notches[0] < 0.05)
        self.assertEqual(notch_times[0],1000.)

    # The following tests use different angled cliffs to start
    # This causes the maximum "depth" to occur just below or above
    # mean sea level, depending on whether it's an over-hang or slope
    # respectively. We therefore add some tolerance to these tests
    # It is possible to get the notch to occur at exactly 0m, but this
    # requires a long simulation (>10kyr for the 27deg cliff)

    def test_pirazzoli_117(self):
        # same as above, but using the 117 deg cliff of Pirazzoli
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 1000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'boring.csv'
        forward_config['input_dir'] = 'data/pirazzoli'
        forward_config['simulation_name'] = '117_deg'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        # should be one notch at 0m height with a time of 1000 years
        nNotches = len(notches)
        self.assertEqual(nNotches,1)
        self.assertTrue(-0.04 < notches[0] < 0.04,"Notch found at "+str(notches[0]))
        self.assertEqual(notch_times[0],1000.)

    def test_pirazzoli_45(self):
        # same as above, but using the 45 deg cliff of Pirazzoli
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 1000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'boring.csv'
        forward_config['input_dir'] = 'data/pirazzoli'
        forward_config['simulation_name'] = '45_deg'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        # should be one notch at 0m height with a time of 1000 years
        nNotches = len(notches)
        self.assertEqual(nNotches,1)
        self.assertTrue(-0.04 < notches[0] < 0.04,"Notch found at "+str(notches[0]))
        self.assertEqual(notch_times[0],1000.)

    def test_pirazzoli_27(self):
        # same as above, but using the 27 deg cliff of Pirazzoli
        # Runs to 1500 years
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 1500.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'boring.csv'
        forward_config['input_dir'] = 'data/pirazzoli'
        forward_config['simulation_name'] = '27_deg'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        # should be one notch at 0m height with a time of 1500 years
        nNotches = len(notches)
        self.assertEqual(nNotches,1)
        # Lower angle, so error larger
        self.assertTrue(-0.05 < notches[0] < 0.05,"Notch found at "+str(notches[0]))
        self.assertEqual(notch_times[0],1500.)

    def test_pirazzoli_63(self):
        # same as above, but using the 63 deg cliff of Pirazzoli
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 1000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'boring.csv'
        forward_config['input_dir'] = 'data/pirazzoli'
        forward_config['simulation_name'] = '63_deg'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        # should be one notch at 0m height with a time of 1000 years
        nNotches = len(notches)
        self.assertEqual(nNotches,1)
        self.assertTrue(-0.04 < notches[0] < 0.04,"Notch found at "+str(notches[0]))
        self.assertEqual(notch_times[0],1000.)

    def test_pirazzoli_135(self):
        # same as above, but using the 135 deg cliff of Pirazzoli
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 1000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'boring.csv'
        forward_config['input_dir'] = 'data/pirazzoli'
        forward_config['simulation_name'] = '135_deg'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        # should be one notch at ~0m height with a time of 1000 years
        nNotches = len(notches)
        self.assertEqual(nNotches,1)
        self.assertTrue(-0.04 < notches[0] < 0.04,"Notch found at "+str(notches[0]))
        self.assertEqual(notch_times[0],1000.)

    # More realistic tests using the Med eustatic SL curve

    def test_med_steady_uplift(self):
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 7000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'sea-level_curve.csv'
        forward_config['input_dir'] = 'data/notch_detection/steady_uplift_med'
        forward_config['simulation_name'] = '90_deg'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        nNotches = len(notches)
        self.assertEqual(nNotches,1)
        #print "Steady uplift:\n----------------\n"
        self.assertTrue(4.10 < notches[0] < 4.12,"Notch found at "+str(notches[0]))
        #print notches
        self.assertTrue(1700 < notch_times[0] < 1750, "Notch time: "+str(notch_times[0]))

    def test_med_4_notches(self):
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 7000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'sea-level_curve.csv'
        forward_config['input_dir'] = 'data/notch_detection/4_notches'
        forward_config['simulation_name'] = '90_deg'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        nNotches = len(notches)
        self.assertEqual(nNotches,4)
        nTimes = len(notch_times)
        self.assertEqual(nTimes,4)
        #print "4 notches:\n----------------\n"
        self.assertTrue(0.15 < notches[0] < 0.2,"Notch found at "+str(notches[0]))
        self.assertTrue(1.85 < notches[1] < 1.9,"Notch found at "+str(notches[1]))
        self.assertTrue(3.69 < notches[2] < 3.72,"Notch found at "+str(notches[2]))
        self.assertTrue(4.14 < notches[3] < 4.16,"Notch found at "+str(notches[3]))
        #print notches
        self.assertTrue(6700 < notch_times[0] < 6750, "Notch time: "+str(notch_times[0]))
        self.assertTrue(5450 < notch_times[1] < 5500, "Notch time: "+str(notch_times[1]))
        self.assertTrue(3600 < notch_times[2] < 3650, "Notch time: "+str(notch_times[2]))
        self.assertTrue(1700 < notch_times[3] < 1750, "Notch time: "+str(notch_times[3]))

    def test_2_notches(self):
        forward_config = {}
        forward_config['start_time'] = 0.0
        forward_config['end_time'] = 3000.0
        forward_config['dt'] = 1.0
        forward_config['sea_level_file'] = 'sea_level.csv'
        forward_config['input_dir'] = 'data/notch_detection/2_notches'
        forward_config['simulation_name'] = '2_notches'
        forward_config['tidal_range'] = 1.0
        # now construct the sea level and times
        times,sl = notchio.construct_sea_level(forward_config)
        notch_times, notches = detect_notches.notches_from_csv(forward_config, 0.3, times, sl)
        nNotches = len(notches)
        self.assertEqual(nNotches,2)
        nTimes = len(notch_times)
        self.assertEqual(nTimes,2)
        #print "2 notches:\n----------------\n" 
        self.assertTrue(2.95 < notches[1] < 3.05,"Notch found at "+str(notches[1]))
        self.assertTrue(1.45 < notches[0] < 1.55,"Notch found at "+str(notches[0]))
        #print notches
        self.assertTrue(475 < notch_times[0] < 525,"Notch time was "+str(notch_times[0]))
        self.assertTrue(1500 < notch_times[1] < 1550,"Notch time was "+str(notch_times[1]))

    def test_linear_extrapolation(self):
        from scipy.interpolate import interp1d
        from scipy import arange, array

        x = arange(0,10)
        y = x # linear function
        f_i = interp1d(x, y)
        f_x = detect_notches.extrap1d(f_i)
        at_11 = f_x([11])

        self.assertTrue(at_11 == 11, "Extrapolate linearly")



if __name__ == '__main__':
    unittest.main()
 
