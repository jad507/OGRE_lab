# Reverse Telescope Stability Tests

## Overview

This is the code that is meant to analyze the results of the stability tests on the reverse telescope system.


## Test settings
We need to standardize the test settings so that data collected will be standardized, isolating the variables of interest.
The variables of interest are: 
 - location of the centroid of the dot, especially noting how much it moves around at both the second scale (due to vibration, helping us eliminate vibration at the hardware level), and at the days scale (unknown cause, will also need to be solved).
 - FWHM of the dot, especially noting if it changes across time.

Things that need to be standardized and documented:
 - LED intensity. We need to pick one voltage and stick with it. I want to see if the display can go down to millivolts, so that we can more precisely pick the voltage, rather than floating somewhere between 2.6 and 2.7 (or any other decivolt numbers)
 - Shutter speed. Currently all are being taken at 1/833, hence the filename
 - framerate. We have some tests going at once a minute, some at once a second, and some at "max" framerate (please copy the exact text of what the settings tooltip says for a setting of 0 minutes, 0 seconds between images)
 - framerate again: I am pretty sure that the images saved are a function of the display framerate, which during some tests were set to 25, some to 50, others to 52.?? 
 - Wind: document if we're running the cleanroom fans for some of the short run tests. Currently in the filename for some of them
 - Naming convention for the filenames. Should make analysis easier.
 - Folder structure: Alex would like to make sure each test goes into its own folder.
 - Total test size/length: the size of the tests is getting unwieldy, especially without any meaningful parallelization and the inability to run analysis without downloading all the data to your local machine. I'm sure there's workarounds.

## Tests done

### 2025-09-17
(settings for this day are from memory. no notes were taken. Will need to be more careful about notes in the future.)

Attempted dot re-collimation from previous state, and got reasonably circular results, but dot is much larger than previously. 
Among the previous tests was to add additional 80/20 framing, which involved motion to the entire reverse telescope frame. Very likely that the system requires full recollimation of all parts, but unlikely that we will choose to do it before we set up the vibration damping feet.
Voltage set to 2.7. Gain set to 4. Binning disabled. 

1-833-stability 25-09-17 08-46-31 single test image

1-833-stability 25-09-17 08-53-16 .. 1-833-stability 25-09-17 08-54-16 one minute of secondly images, taken accidentally, as I was trying to take max framerate images, but because of my naming convention chosen, it simply wrote-over the other ones in that second.

1-833-stability3054 .. 1-833-stability3153  max framerate images for 100 images

1-833-stability0001 .. 1-833-stability0287 max framerate images for a few seconds before manually stopping it

1-833-stability0288 25-09-17 09-06-49 .. 1-833-stability10286 25-09-17 11-59-49 secondly images for 10000 images.

Machine was shut down overnight, with LED unplugged. (unplug/replug process is a possible source of change to dot location?)

### 2025-09-18
Dot was not adjusted from previous tests, but is in a different location and with worse collimation. 
Among the previous tests was to add additional 80/20 framing. 
Voltage set to 2.6. Gain set to 4. Binning disabled. 

TODO: add test information for this day.

stability: high framerate with fan on

fanoff: high framerate (will need to calculate framerate. likely 25, 50 or 52.37) with fan off

longrun: Secondly data for a long time. Leads to a LOT of images, so secondly long-runs are no longer recommended

nightvideo: high framerate before overnight run

overnightvideo: minutely images over night.


Machine was run overnight, continuing to take images once a *minute* for 10,000 frames.

### 2025-09-19
At 09:06 we had some construction vibration sounds, but it wasn't as bad as it usually is. Unclear on if it will show up in the data. It had a bit of a spike around 09:11, again at 9:28. Wasn't paying attention to construction for the rest of the day.

Continued to run from previous night until 1373 frames. Stopped at 15:04. 

Alex would like less data total. Will run over the weekend at one frame a minute. In new folder.


### 2025-09-22
Weekend run was still going strong. Dot has moved into the top-middle. A quick look at the data shows that it first wandered down off the screen, and then back up. We might be able to guess very long time-scale sinusoidal movement?

Took Max framerate (52.37 fps) video for 3 minutes in its own folder

Resumed one frame per minute snapshots. Took voltage with handheld voltmeter, found that it is 2.622 V. Has not been adjusted since 2022-09-18.

### 2025-09-23


### 2025-09-24

### 2025-09-25
### 2025-09-26
During some Nate tests at 1:30 it was discovered that we were disconnected from the camera and the dot had moved off screen as we were touching things. Dot was refound, no changes to collimation, but does not map perfectly onto past data.


## Questions Jeff has about things
### FITS Format
I (Jeff) was reading the [FITS spec](https://fits.gsfc.nasa.gov/fits_standard.html) and its meaning was pretty opaque to me. 
From a practical standpoint, [my previous code](https://github.com/jad507/ReverseTelescopeDot) made use of the bitmaps directly. 
If I'm understanding the FITS standard, the sort of "standard" way we are using FITS is basically the same as a bitmap with an additional header, where it's just 3 arrays of [Image Resolution], one for each color channel.
So, a few things seem possible (all confirmed in a conversation with James):
- you should be able to combine all the frames for a run into the same FITS file if you wanted to. It would be a GIANT file (according to him, you'd simply crash your computer trying get all the tREXS data into a single file and opening it).
- you should be able to slam any information you want into the header: information about date, time, framerate, LED voltage, Shutter speed, fan status, etc could be put into there. Maybe we should put it in there by default. Maybe we should put the information into a per-test .txt within the folder that the data sits.
- you should be able to put processed information into the header: information about the centroid, FWHM in headers, so you only need to read headers in order to do the full calculation
- you should be able to resize the data. What if you loop through the entire test in bitmap form, and extract a maximum bounding box for all relevant data, add a header x,y coordinate and delete the rest from the fits so that you minimize total filesize for the complete set of fits.
- you should be able to have arbitrarily large ints in a fits. As you go through the files, you could form a secondary fits file that just adds all previously seen images together so you get a heatmap of the entire series. Not sure if that's scientifically/statistically meaningful.

### test settings
It seems like we're pretty keen to stay on 1/833, so let's just get rid of that from the filename.
We're pretty keen to switch to per-test folders.
I would like to get greater detail on the voltage and fix it in place more precisely. I also want to take a look at the max value and set voltage so that max value is like 200 out of 255 in greyscale. It probably doesn't matter.


## accelerometer data
Code written by Nate Hamme
Hardware is: 

-two 3-axis accelerometer blocks (PCB brand, unknown model number)

-PCB Piezotronics Model 482C series sensor signal conditioner. 4 channels, set up for xyz on the cantilevered light source, soon to switch to xyz on the primary mirror and y on the cantilevered light source. 
Part number 482C15, Serial LW006102, last calibrated 08/09/2022 by H. Lynch.
Frequency response should be in the .05Hz to 100kHz range, depending on gain settings (1x, 10x, 100x). Gain settings can be adjusted by unscrewing the top and moving around a jumper inside of it. Currently unknown jumper/gain settings.

-National Instruments NI USB-6218 32 inputs, 16-bit, 250 kS/s Isolated Multifunction I/O.
all cables plugged into the Analog Input, channels 49-54 (with more room for other cables)
You will need to download a [driver](https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#569353) from the NI website to use it.
Seems like it has some sort of programming interface that allows you to fiddle with the settings.
