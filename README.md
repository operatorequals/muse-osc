# muse-osc
Connect Muse Headband to Neuromore Studio

Connects your [Muse Headband](https://choosemuse.com/) to Neurofeedback systems accepting OSC, like [Neuromore Studio](https://www.neuromore.com/products).

*No Muse Mobile App, other Mobile Apps or OSC interfaces are required*

## Usage

0. Install requirements of this project:
```bash
pip install -r requirements.txt
# (optionally) install muselsl to connect to Muse
pip install muselsl
```

1. Use [`muselsl`](https://github.com/alexandrebarachant/muse-lsl) (or anything else like [BlueMuse](https://github.com/kowalej/BlueMuse) or [MuseLSL2](https://github.com/DominiqueMakowski/MuseLSL2)) to connect to Muse through Bluetooth and start the LSL stream:
```bash
muselsl stream
```

2. Run this project to read LSL and start the OSC stream
```bash
python -m muse-osc
```

3. Connect to Neuromore Studio.

	Check the OSC Input settings, as can be found in [Neuromore Documentation](https://doc.neuromore.com/?cat=0&page=8#osc-settings-in-neuromore-studio). Default port is `4545/UDP` and host is `localhost`. These are also the default values for `muse-osc` `--host` and `--port` arguments.

4. Use an *OSC Input Node* in Neuromore Studio.

	Set `OSC address` and `Sample rate` as shown in [OSC Channels](https://github.com/operatorequals/muse-osc#osc-channels).


### OSC channels

The channels generally follow the excellent [Mind Monitor's Spec](https://mind-monitor.com/FAQ.php#oscspec).

##### Note: This module only covers the basics of this spec, as Mind Monitor is an advanced project, doing a lot of processing to the EEG data to mathematically identiify Jaw Clenches, Eye Blinks and other events.

The supported channels:

`EEG`

```bash
# Raw EEG - 256Hz
/muse/eeg # <-- tuple of 5
## Breakout per electrode
/muse/eeg/tp9
/muse/eeg/af7
/muse/eeg/af8
/muse/eeg/tp10
/muse/eeg/aux

# Bands - 10Hz
## Average value of all electrodes
/muse/elements/delta_absolute
/muse/elements/theta_absolute
/muse/elements/alpha_absolute
/muse/elements/beta_absolute
```

Currently, the `PPG`, `GYRO`, `ACC` LSL streams are not tested, yet theoretically follow the same spec.

### `--help`

As it is common to paste `arparse` `--help` output:

```bash
python -m muse_osc -h
usage: muselsl2osc [-h] [--host HOST] [--port PORT] [--timeout TIMEOUT] [--lsl-streams {EEG,ACC,PPG,GYRO} [{EEG,ACC,PPG,GYRO} ...]]

Converts LSL input to OSC for use with tools like Neuromore

options:
  -h, --help            show this help message and exit
  --host HOST, -H HOST  The HOST where OSC will be sent to
  --port PORT, -p PORT  The PORT where OSC will be sent to
  --timeout TIMEOUT     Number of seconds until exit
  --lsl-streams {EEG,ACC,PPG,GYRO} [{EEG,ACC,PPG,GYRO} ...]
                        List of Muse LSL streams to be accepted
```

## Credits

This work is heavily based on these projects:

* https://github.com/ViacheslavBobrov/LSL_Neuromore
This project was used as baseline code. It implements the basics of LSL to OSC streaming.

* https://github.com/alexandrebarachant/muse-lsl
The [`neurofeedback.py`](https://github.com/alexandrebarachant/muse-lsl/blob/master/examples/neurofeedback.py) example of this project has been used, to calculate bands and protocols with `numpy`. The [`utils.py`](https://github.com/alexandrebarachant/muse-lsl/blob/master/examples/utils.py) file has been used verbatim.