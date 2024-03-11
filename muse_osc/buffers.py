import numpy as np

import muse_osc.utils as muselsl_utils

# Modify these to change aspects of the signal processing

# Length of the EEG data buffer (in seconds)
# This buffer will hold last n seconds of data and be used for calculations
BUFFER_LENGTH = 5

# Length of the epochs used to compute the FFT (in seconds)
EPOCH_LENGTH = 1

# Amount of overlap between two consecutive epochs (in seconds)
OVERLAP_LENGTH = 0.8

# Amount to 'shift' the start of each next consecutive epoch
SHIFT_LENGTH = EPOCH_LENGTH - OVERLAP_LENGTH

ELEMENTS = ["TP9","AF7", "AF8", "TP10", "AUX"]
BANDS = ["delta", "theta", "alpha", "beta"]

class BandCalculator:

    def __init__(self, sample_rate=256, retention_sec=5, epoch_sec=1, overlap_sec = 0.8):

        self.buffers = {
            'EEG': None,
            'accelerometer': None,
            'PPG': None,
            'gyroscope': None,
        }

        self.shift_length = epoch_sec - overlap_sec
        # Compute the number of epochs in "buffer_length"
        n_win_test = int(np.floor((retention_sec - epoch_sec) /
                                  self.shift_length + 1))

        self.sample_rate = sample_rate
        self.retention_sec = retention_sec,
        self.epoch_sec = epoch_sec

        self.buffers['EEG'] = {
            'elements' : {
                element: np.zeros((int(sample_rate * retention_sec), 1))
                for element in ELEMENTS 
            },
            'bands' : {
                'elements' : {
                    element: {
                        band: np.zeros((n_win_test, 1))
                        for band in BANDS
                    }
                    for element in ELEMENTS 
                },
            },
            'filter_states' : {
                element: None
                for element in ELEMENTS 
            },
        }
        print("Buffers initialized")


    def add_sample(self, sample, sample_type="EEG", ):
        if not sample_type == "EEG": raise RuntimeError(f"Sample Type {sample_type} not implemented!")
        for element, index in zip(ELEMENTS, range(len(sample[0]))):
            # print(index)
            value = np.array(sample)[:, [index]]
            # print(f"{element}: {value}")
            self.buffers[sample_type]['elements'][element], self.buffers[sample_type]['filter_states'][element] = muselsl_utils.update_buffer(
                    self.buffers[sample_type]['elements'][element], value, notch=True,
                    filter_state=self.buffers[sample_type]['filter_states'][element]
                )


    def compute_bands(self):

        data_epoches = {}
        for element in ELEMENTS:

            data_epoches[element] = muselsl_utils.get_last_data(
                self.buffers['EEG']['elements'][element],
                self.epoch_sec * self.sample_rate)

            band_powers = muselsl_utils.compute_band_powers(
                    data_epoches[element],
                    self.sample_rate
                )

            assert len(BANDS) == len(band_powers)
            # print(len(band_powers[0]))
            for band, power in zip(BANDS, band_powers):
                # print(band, power)
                self.buffers['EEG']['bands']['elements'][element][band], _ = muselsl_utils.update_buffer(
                    self.buffers['EEG']['bands']['elements'][element][band],
                                             np.asarray([power]))


    def get_band_power(self, band, elements="ALL", aux=False):

        assert band in BANDS

        if elements == 'ALL': elements = ELEMENTS[:]
        if not aux:
            if "AUX" in elements:
                elements.remove("AUX")
            if len(elements) == 0:
                return 0

        ret = 0.0
        for element in elements:
            # Compute the average band powers for all epochs in buffer
            # This helps to smooth out noise
            ret += np.mean(self.buffers['EEG']['bands']['elements'][element][band], axis=0)

        # Return the mean of all the element measurements for the band
        return float(ret / len(elements))


    def get_protocol(self, protocol, elements="ALL", aux=False):

        assert protocol in ["alpha", "beta", "alpha-theta"]

        # Alpha Protocol:
        # Simple redout of alpha power, divided by delta waves in order to rule out noise
        if protocol == "alpha":
            alpha = self.get_band_power("alpha", elements=elements, aux=aux)
            delta = self.get_band_power("delta", elements=elements, aux=aux)
            return alpha / delta

        # Beta Protocol:
        # Beta waves have been used as a measure of mental activity and concentration
        # This beta over theta ratio is commonly used as neurofeedback for ADHD
        if protocol == "beta":
            theta = self.get_band_power("theta", elements=elements, aux=aux)
            beta = self.get_band_power("beta", elements=elements, aux=aux)
            return beta / theta

        # Alpha/Theta Protocol:
        # This is another popular neurofeedback metric for stress reduction
        # Higher theta over alpha is supposedly associated with reduced anxiety
        if protocol == "alpha-theta":
            theta = self.get_band_power("theta", elements=elements, aux=aux)
            alpha = self.get_band_power("alpha", elements=elements, aux=aux)
            return theta / alpha
