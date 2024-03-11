# /usr/bin/env python

from pylsl import StreamInlet, resolve_byprop
from pythonosc import udp_client
from threading import Thread
from time import sleep

from muse_osc.buffers import BandCalculator, ELEMENTS, BANDS

class LslToOscStreamer:

    def __init__(self, host, port, compute_bands = False):
        self.client = udp_client.SimpleUDPClient(host, port)
        self.is_streaming = False

        self.inlets = {
            # As defined in muselsl stream
            'EEG': None,
            'accelerometer': None,
            'PPG': None,
            'gyroscope': None,
        }

        self.band_calculator = None

        self.shift_length = 0.2
        self.sample_rate = 256

        if compute_bands:
            print("Initializing Band Calculator")
            self.band_calculator = BandCalculator()
            self.shift_length = self.band_calculator.shift_length
            self.sample_rate = self.band_calculator.sample_rate


    def connect(self, prop='type', stream_types=['EEG']):
        for stream_type in stream_types:
            if stream_type == 'ACC': stream_type = 'accelerometer'
            if stream_type == 'GYRO': stream_type = 'gyroscope'

            streams = resolve_byprop(prop, stream_type, timeout=5)
            if len(streams) == 0:
                print(f"Can't find {stream_type} stream.")
                continue
            self.inlets[stream_type] = StreamInlet(streams[0], max_chunklen=12)
        # If no Inlet was created
        if list(set(self.inlets.values())) == [None]:
            raise RuntimeError(f"No Stream available.")
        print(f"Streams available: {self.inlets}")
        return True

    def stream_data(self):
        self.is_streaming = True
        streaming_thread = Thread(target=self._stream_handler)
        streaming_thread.daemon = True
        streaming_thread.start()

    def _stream_handler(self):
        hz_10_counter = 0
        while self.is_streaming:
            for stream_type, inlet in self.inlets.items():
                # print(f"Pushing data for {stream_type}")
                if inlet == None: continue
                sample_chunk, ts = inlet.pull_sample(); sample_chunk = [sample_chunk]
                # sample_chunk, _ = inlet.pull_chunk(
                #     timeout=1, max_samples=int(self.shift_length * self.sample_rate)
                #     )
                for sample in sample_chunk:
                    # Taken by the spec of Mind-Monitor
                    # https://mind-monitor.com/FAQ.php#oscspec
                    if stream_type == "EEG":
                        assert len(sample) == 5 # TP9, AF7, AF8, TP10, AUX
                        self.client.send_message("/muse/eeg", sample)
                        # Broken out per EEG element
                        for channel_idx, channel in enumerate([
                                "/muse/eeg/tp9",
                                "/muse/eeg/af7",
                                "/muse/eeg/af8",
                                "/muse/eeg/tp10",
                                "/muse/eeg/aux",
                            ]):
                            self.client.send_message(channel, sample[channel_idx])

                    if stream_type == "gyroscope":
                        assert len(sample) == 3 # X, Y, Z                
                        self.client.send_message("/muse/gyro", sample)

                    if stream_type == "accelerometer":
                        assert len(sample) == 3 # X, Y, Z
                        self.client.send_message("/muse/acc", sample)

                    if stream_type == "PPG":
                        assert len(sample) == 3 # PPG1, PPG2, PPG3
                        self.client.send_message("/muse/ppg", sample)

                if self.band_calculator != None and stream_type == "EEG": # Compute bands
                    self.band_calculator.add_sample(sample_chunk, sample_type="EEG")

                    if round(ts,1) - int(ts) != hz_10_counter:
                        self.band_calculator.compute_bands()
                        # print(self.band_calculator.get_protocol('alpha'))
                        hz_10_counter = round(ts,1) - int(ts)

                        for band in BANDS:
                            channel = f"/muse/elements/{band}_absolute"
                            powers = []
                            self.client.send_message(channel,
                                    self.band_calculator.get_band_power(band, elements="ALL")
                                )

    def close_stream(self):
        self.is_streaming = False
        for inlet in self.inlets.values():
            inlet.close_stream()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
                prog='muselsl2osc',
                description='Converts LSL input to OSC for use with tools like Neuromore',
            )
    parser.add_argument('--host', '-H', help="The HOST where OSC will be sent to", default='127.0.0.1')
    parser.add_argument('--port', '-p', help="The PORT where OSC will be sent to", default=4545)
    parser.add_argument('--timeout', help="Number of seconds until exit", default=3600)
    parser.add_argument('--lsl-streams', help='List of Muse LSL streams to be accepted', nargs='+',
        choices=['EEG','ACC','PPG','GYRO'], default=['EEG']
        )
    args = parser.parse_args()

    host = args.host
    port = args.port
    stream_time_sec = args.timeout

    print(f"Initializing connection to {args.host}:{args.port} - forwarding LSL streams: {args.lsl_streams}")
    streamer = LslToOscStreamer(host, port, compute_bands=True)
    streamer.connect(
        stream_types=args.lsl_streams
    )

    print(f"Start streaming data for {stream_time_sec} seconds")
    streamer.stream_data()
    sleep(stream_time_sec)
    streamer.close_stream()
    print("Stopped streaming. Exiting program...")
