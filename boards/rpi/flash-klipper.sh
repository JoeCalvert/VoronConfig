#!/bin/bash

cd "$HOME/klipper"


flash(){
	echo -e "\033[1;34m\nCleaning and building Klipper firmware for RPI MCU.\033[0m"
	make clean KCONFIG_CONFIG=~/printer_data/config/boards/rpi/klipper.config
	echo -e "\033[1;34m\nFlashing Klipper to RPI MCU.\033[0m"
	make flash KCONFIG_CONFIG=~/printer_data/config/boards/rpi/klipper.config -j4 > /dev/null 2>&1
}

echo -e "\033[1;34m\nStopping Klipper service.\033[0m"
sudo service klipper stop
sleep 5
flash
sleep 5
echo -e "\033[1;34m\nStarting Klipper service.\033[0m"
sudo service klipper start
