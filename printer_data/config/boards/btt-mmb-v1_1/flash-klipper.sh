#!/bin/bash

cd "$HOME/klipper"


flash(){
	echo -e "\033[1;34m\nCleaning and building Klipper firmware for BTT MMB V1.1.\033[0m"
	make clean KCONFIG_CONFIG=~/printer_data/config/boards/btt-mmb-v1_1/klipper_canbus.config
	make -s KCONFIG_CONFIG=~/printer_data/config/boards/btt-mmb-v1_1/klipper_canbus.config -j4  > /dev/null 2>&1
	mv ~/klipper/out/klipper.bin btt_mmb_v1_1.bin
	echo -e "\033[1;34m\nFlashing Klipper to BTT MMB V1.1.\033[0m"
	python3 ~/katapult/scripts/flash_can.py -f ~/klipper/btt_mmb_v1_1.bin -u c2d5f652b572
}

echo -e "\033[1;34m\nStopping Klipper service.\033[0m"
sudo service klipper stop
sleep 5
flash
sleep 5
echo -e "\033[1;34m\nStarting Klipper service.\033[0m"
sudo service klipper start
