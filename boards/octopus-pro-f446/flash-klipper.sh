#!/bin/bash

cd "$HOME/klipper"


flash_usb(){
	echo -e "\033[1;34m\nCleaning and building Klipper firmware for Octopus Pro F446\033[0m"
	make clean KCONFIG_CONFIG=~/printer_data/config/boards/octopus-pro-f446/klipper_usb.config
	echo -e "\033[1;34m\nFlashing Klipper to Octopus Pro F446.\033[0m"
	make flash FLASH_DEVICE=/dev/serial/by-id/usb-Klipper_stm32f446xx_570030001551303432323631-if00 KCONFIG_CONFIG=~/printer_data/config/boards/octopus-pro-f446/klipper_usb.config -j4  > /dev/null 2>&1
}

flash_uart(){
        echo -e "\033[1;34m\nCleaning and building Klipper firmware for Octopus Pro F446\033[0m"
        make clean KCONFIG_CONFIG=~/printer_data/config/boards/octopus-pro-f446/klipper_uart.config
        echo -e "\033[1;34m\nFlashing Klipper to Octopus Pro F446.\033[0m"
        make flash FLASH_DEVICE=/dev/ttyAMA0 KCONFIG_CONFIG=~/printer_data/config/boards/octopus-pro-f446/klipper_uart.config
}

echo -e "\033[1;34m\nStopping Klipper service.\033[0m"
sudo service klipper stop
sleep 5
flash_usb
sleep 5
echo -e "\033[1;34m\nStarting Klipper service.\033[0m"
sudo service klipper start
