#!/bin/bash

cd "$HOME/klipper"


flash(){
	echo -e "\033[1;34m\nCleaning and building Klipper firmware for Mellow SB2040 V1.\033[0m"
	make clean KCONFIG_CONFIG=~/printer_data/config/boards/mellow-sb2040-v1/klipper_canbus.config
	make -s KCONFIG_CONFIG=~/printer_data/config/boards/mellow-sb2040-v1/klipper_canbus.config -j4  > /dev/null 2>&1
	mv ~/klipper/out/klipper.bin mellow_sb2040_v1.bin
	echo -e "\033[1;34m\nFlashing Klipper to Mellow SB2040 V1.\033[0m"
	python3 ~/katapult/scripts/flash_can.py -f ~/klipper/mellow_sb2040_v1.bin -u 56993da7b11b
}

echo -e "\033[1;34m\nStopping Klipper service.\033[0m"
sudo service klipper stop
sleep 5
flash
sleep 5
echo -e "\033[1;34m\nStarting Klipper service.\033[0m"
sudo service klipper start
