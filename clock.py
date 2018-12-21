# -*- coding: utf-8 -*-
import pygame #for graphics
import datetime #for time
import os #for getuid
import sys #for exit
import requests #for weather api calls
import json #for weather api response json
import time #for sleep

#check if run as sudo (required for backlighting)
if(os.getuid() != 0):
    print("ERROR: clock.py must be run as sudo")
    sys.exit()
        
#initialize pygame
print("Initializing pygame...")
pygame.init()

#background
bg_color = (0, 0, 0)
    
#header
header_font = pygame.font.SysFont('Roboto', 288)
header_color= (255, 255, 255)
header_position = (0.5, 0.475)
header_aa = True

#subheader
subheader_font = pygame.font.SysFont('Roboto', 60)
subheader_color= (255, 0, 0)
subheader_position = (0.5, 0.825)
subheader_aa = True

#weather icon
weather_icon_position = (10, 10)
weather_icon = pygame.image.load("icons/03d.png")

#weather info
info_font = pygame.font.SysFont('Roboto', 24)
info_color= (255, 255, 255)
info_position = (70, 15)
info_aa = True

weather_string = "Loading weather..."

#current time
current_datetime = datetime.datetime.now()

#night mode settings
night_mode_start = datetime.time(hour = 21)
night_mode_end = datetime.time(hour = 5)

#weather
api_url = "http://api.openweathermap.org/data/2.5/weather"
api_url_full = ""

#display
backlight_default = 255
backlight_night_mode = 64

#counters
draw_count = 0
weather_count = 0

def rel_to_abs_coord(pos, display_info):
    return (pos[0]*display_info.current_w, pos[1]*display_info.current_h)

def rel_to_abs_surf(surf, pos, display_info):
    return (rel_to_abs_coord(pos, display_info)[0] - (surf.get_rect().width / 2), rel_to_abs_coord(pos, display_info)[1] - (surf.get_rect().height / 2))

def load_config():
    global api_url_full, backlight_default, backlight_night_mode, night_mode_start, night_mode_end

    print("Loading config file..")
    config = open('config.txt','r')

    api_key = config.readline().split()[0]
    api_zip = config.readline().split()[0]
    
    api_url_full = api_url+"?zip="+api_zip+"&appid="+api_key

    backlight_default = int(config.readline().split()[0])
    backlight_night_mode = int(config.readline().split()[0])

    night_mode_start = datetime.datetime.strptime(config.readline().split()[0], "%H:%M:%S").time()
    night_mode_end = datetime.datetime.strptime(config.readline().split()[0], "%H:%M:%S").time()

    config.close()

def set_backlight(val):
    #requires sudo permission
    
    backlight_file = open("/sys/class/backlight/rpi_backlight/brightness", 'w')
    backlight_file.write(str(val))
    backlight_file.close()

def get_weather_data():
    response = requests.get(api_url_full)
    
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        return None
    
def update_weather():
    global weather_string, weather_icon, weather_count

    weather_count += 1
    
    weather_data = get_weather_data()
    if weather_data:
        temp_k = float(weather_data["main"]["temp"])
        temp_c = temp_k - 273
        temp_f = (9*(temp_k - 273)/5) + 32

        weather_name = weather_data["weather"][0]["main"]
        
        weather_string = weather_name + " - " + "{0:.1f}".format(temp_f) + u"°"
        
        weather_icon_name = weather_data["weather"][0]["icon"]
        weather_icon = pygame.image.load("icons/{0}.png".format(weather_icon_name))
    else:
        print("ERROR: Could not load weather")

def is_night_mode(time):
    if night_mode_start < night_mode_end:
        #start and end on same day, ie: 1am and 9am
        return time >= night_mode_start and time <= night_mode_end
    else:
        #start and end on subsequent days, ie: 9pm and 5am
        return time >= night_mode_start or time <= night_mode_end
        

def draw(display_info, screen):
    global draw_count

    draw_count += 1

    if is_night_mode(current_datetime.time()):
        set_backlight(backlight_night_mode)
    else:
        set_backlight(backlight_default)

    #get time as string
    time_string = current_datetime.strftime("%-H:%M")
    date_string = current_datetime.strftime("%-d %B %Y")
    
    #redraw the screen
    screen.fill(bg_color)
        
    header_surface = header_font.render(time_string, header_aa, header_color)
    screen.blit(header_surface, rel_to_abs_surf(header_surface, header_position, display_info))

    subheader_surface = subheader_font.render(date_string, subheader_aa, subheader_color)
    screen.blit(subheader_surface, rel_to_abs_surf(subheader_surface, subheader_position, display_info))
    
    screen.blit(weather_icon, weather_icon_position)
                
    info_surface = info_font.render(weather_string, info_aa, info_color)
    screen.blit(info_surface, info_position)
    
    pygame.display.flip()

def main():
    global current_datetime

    load_config()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    #for debugging (if a pygame script crashes while fullscreen it cannot be exited)
    #screen = pygame.display.set_mode((800,400))

    pygame.display.set_caption("Clock")
    pygame.mouse.set_visible(False)

    #display info
    display_info = pygame.display.Info()

    #preliminary draw, so the user sees more than a black screen
    draw(display_info, screen)

    #get weather info
    update_weather()

    #redraw the screen with fetched weather info
    draw(display_info, screen)
    
    running = True
    while running:
        #check if the user has exited the program
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        #get current time
        prev_datetime = current_datetime
        current_datetime = datetime.datetime.now()
        
        #redraw every minute
        if current_datetime.time().second % 60 == 0 and prev_datetime.time().second % 60 == 59:
            
            #check weather every hour
            if current_datetime.time().minute % 60 == 0 and prev_datetime.time().minute % 60 == 59:
                update_weather()

            draw(display_info, screen)

        #sleep for 10ms to spare the cpu
        time.sleep(.01)
        
    pygame.quit()
    set_backlight(backlight_default)

    print("Quitting: {0} redraws, {1} weather api calls".format(draw_count, weather_count))

if __name__ == "__main__":
    main()
