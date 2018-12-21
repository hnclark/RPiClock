#RPiClock

A simple smart clock program built for Raspberry Pi using Python with PyGame and OpenWeatherMap

##Setup

Rename `example_config.txt` to `config.txt` and edit it to contain the relevant information: your OpenWeatherMap API key, zip code, and what time periods you want it to enter night mode (dims the screen)

##Running the clock

Simply run `sudo python clock.py` to run the program. It requires sudo to change the display's backlight brightness