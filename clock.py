# -*- coding: utf-8 -*-
import pygame #for graphics
import datetime #for time
import os #for getuid
import sys #for exit
import requests #for weather api calls
import json #for weather api response json
import time #for sleep

def rel_to_abs_coord(pos, display_info):
    return (pos[0]*display_info.current_w, pos[1]*display_info.current_h)

def rel_to_abs_surf(surf, pos, display_info):
    return (rel_to_abs_coord(pos, display_info)[0] - (surf.get_rect().width / 2), rel_to_abs_coord(pos, display_info)[1] - (surf.get_rect().height / 2))

def time_print(string):
    print("["+str(datetime.datetime.now())+"]: "+string)

#check if run as sudo (required for backlighting)
if(os.getuid() != 0):
    time_print("ERROR: clock.py must be run as sudo")
    sys.exit()

#initialize pygame
time_print("Initializing pygame...")
pygame.init()

#screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
#for debugging (if a pygame script crashes while fullscreen it cannot be exited)
screen = pygame.display.set_mode((800,400))

pygame.display.set_caption("Clock")

#if pygame.mouse.set_visible(False) is used, the touchscreen doesn't work
#we can work around that by making a cursor with no visible pixels that is set visible
pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))

#display info
display_info = pygame.display.Info()

#background
bg_color = (0, 0, 0)

bg_color_alarm = (41, 171, 135)

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

next_draw = datetime.datetime.now()

#weather icon
weather_icon_position = (10, 10)
weather_icon = pygame.image.load("icons/03d.png")

#weather info
weather_panel_bbox = pygame.Rect((0, 0),(display_info.current_w, 60))

info_font = pygame.font.SysFont('Roboto', 24)
info_color= (255, 255, 255)
info_position = (70, 15)
info_aa = True

weather_string = "Loading weather..."

next_weather_update = datetime.datetime.now()

#forecast
forecast_date_offset = (0, 30)
forecast_icon_offset = (0, 70)

forecast_list = []

#current opened panel
opened_panel = None

#current time
current_datetime = datetime.datetime.now()

#night mode settings
night_mode_start = datetime.time(hour = 21)
night_mode_end = datetime.time(hour = 5)

#alarm settings
alarm_time = datetime.time(hour = 5)

alarm_deactivation = None

alarm_mode = False

#weather
api_url = "http://api.openweathermap.org/data/2.5/"
api_url_end = ""

#display
backlight_default = 255
backlight_night_mode = 64

#counters
draw_count = 0
weather_count = 0

def load_config():
    global api_url_end, backlight_default, backlight_night_mode, night_mode_start, night_mode_end, alarm_time

    time_print("Loading config file..")
    config = open('config.txt','r')

    api_key = config.readline().split()[0]
    api_zip = config.readline().split()[0]
    
    api_url_end = "?zip="+api_zip+"&appid="+api_key

    backlight_default = int(config.readline().split()[0])
    backlight_night_mode = int(config.readline().split()[0])

    night_mode_start = datetime.datetime.strptime(config.readline().split()[0], "%H:%M:%S").time()
    night_mode_end = datetime.datetime.strptime(config.readline().split()[0], "%H:%M:%S").time()

    alarm_time = datetime.datetime.strptime(config.readline().split()[0], "%H:%M:%S").time()

    config.close()

def set_backlight(val):
    #requires sudo permission
    
    backlight_file = open("/sys/class/backlight/rpi_backlight/brightness", 'w')
    backlight_file.write(str(val))
    backlight_file.close()

def get_weather_data(request_type):
    response = requests.get(api_url + request_type + api_url_end)
    try:
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'))
        else:
            return None
    except:
        return None
    
def update_weather():
    global weather_string, weather_icon, forecast_list, weather_count, next_weather_update, next_draw

    weather_count += 2
    
    weather_data = get_weather_data("weather")

    forecast_data = get_weather_data("forecast")
    
    if weather_data and forecast_data:
        temp_k = float(weather_data["main"]["temp"])
        temp_c = temp_k - 273
        temp_f = (9*(temp_k - 273)/5) + 32

        weather_name = weather_data["weather"][0]["main"]
        
        weather_string = weather_name + " - " + "{0:.1f}".format(temp_f) + u"°"
        
        weather_icon_name = weather_data["weather"][0]["icon"]
        weather_icon = pygame.image.load("icons/{0}.png".format(weather_icon_name))

        for forecast in forecast_data["list"]:
            date = datetime.datetime.strptime(forecast["dt_txt"], "%Y-%m-%d %H:%M:%S")
            desc = forecast["weather"][0]["main"]
            icon_name = forecast["weather"][0]["icon"]
            icon = pygame.image.load("icons/{0}.png".format(icon_name))

            #only append forecasts at 15:00 to simplify display
            if date.time().hour == 15:
                forecast_list.append((date, desc, icon))
            
        next_weather_update = datetime.datetime.now() + datetime.timedelta(hours = 1)
        next_draw = datetime.datetime.now()
        
    else:
        time_print("ERROR: Could not load weather")
        next_weather_update = datetime.datetime.now() + datetime.timedelta(minutes = 1)

def is_night_mode(time):
    if night_mode_start < night_mode_end:
        #start and end on same day, ie: 1am and 9am
        return time >= night_mode_start and time <= night_mode_end
    else:
        #start and end on subsequent days, ie: 9pm and 5am
        return time >= night_mode_start or time <= night_mode_end
        

def draw(display_info, screen):
    global draw_count, next_draw

    draw_count += 1

    if alarm_mode:
        set_backlight(backlight_default)
    else:
        if is_night_mode(current_datetime.time()):
            set_backlight(backlight_night_mode)
        else:
            set_backlight(backlight_default)

    #get time as string
    time_string = current_datetime.strftime("%-H:%M")
    date_string = current_datetime.strftime("%-d %B %Y")
    
    #redraw the screen
    if alarm_mode:
        screen.fill(bg_color_alarm)
    else:
        screen.fill(bg_color)
        
    header_surface = header_font.render(time_string, header_aa, header_color)
    screen.blit(header_surface, rel_to_abs_surf(header_surface, header_position, display_info))

    subheader_surface = subheader_font.render(date_string, subheader_aa, subheader_color)
    screen.blit(subheader_surface, rel_to_abs_surf(subheader_surface, subheader_position, display_info))

    if opened_panel == "weather_panel":
        for index, forecast in enumerate(forecast_list):
            base_pos = (0.1 + 0.2*index, 0)
            
            forecast_date_surface = info_font.render(forecast[0].strftime("%A"), info_aa, info_color)
            date_centered_pos = rel_to_abs_surf(forecast_date_surface, base_pos, display_info)
            date_pos = (date_centered_pos[0] + forecast_date_offset[0], date_centered_pos[1] + forecast_date_offset[1])
            screen.blit(forecast_date_surface, date_pos)

            forecast_icon_surface = forecast[2]
            icon_centered_pos = rel_to_abs_surf(forecast_icon_surface, base_pos, display_info)
            icon_pos = (icon_centered_pos[0] + forecast_icon_offset[0], icon_centered_pos[1] + forecast_icon_offset[1])
            screen.blit(forecast_icon_surface, icon_pos)
            
    else:
        screen.blit(weather_icon, weather_icon_position)
                
        info_surface = info_font.render(weather_string, info_aa, info_color)
        screen.blit(info_surface, info_position)
    
    pygame.display.flip()

    next_draw = datetime.datetime.now() + datetime.timedelta(hours = 1)

def handle_panels(mouse_pos):
    global opened_panel
    
    if weather_panel_bbox.collidepoint(mouse_pos):
        opened_panel = "weather_panel"
    else:
        opened_panel = None

def activate_alarm():
    global alarm_mode, alarm_deactivation, next_draw
    alarm_mode = True
    alarm_deactivation = datetime.datetime.now() + datetime.timedelta(minutes = 1)
    
    next_draw = datetime.datetime.now()

def deactivate_alarm():
    global alarm_mode, next_draw
    alarm_mode = False
    alarm_deactivation = None
    
    next_draw = datetime.datetime.now()

def main():
    global current_datetime, opened_panel, next_draw

    load_config()

    #preliminary draw, so the user sees more than a black screen
    draw(display_info, screen)
    
    running = True
    while running:
        #check if the user has exited the program
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.MOUSEBUTTONUP:
                if alarm_mode:
                    deactivate_alarm()
                handle_panels(pygame.mouse.get_pos())
                next_draw = datetime.datetime.now()
                
        #get current time
        prev_datetime = current_datetime
        current_datetime = datetime.datetime.now()

        if prev_datetime.time() <= alarm_time and current_datetime.time() >= alarm_time:
            activate_alarm()

        if alarm_mode and current_datetime >= alarm_deactivation:
            deactivate_alarm()

        #redraw if necessary or if minute changes
        if current_datetime >= next_draw or (prev_datetime.time().second % 59 == 0 and current_datetime.time().second % 60 == 0):
            draw(display_info, screen)

        if current_datetime >= next_weather_update:
            update_weather()

        #sleep for 10ms to spare the cpu
        time.sleep(.01)
        
    pygame.quit()
    set_backlight(backlight_default)

    time_print("Quitting: {0} redraws, {1} weather api calls".format(draw_count, weather_count))

if __name__ == "__main__":
    main()
