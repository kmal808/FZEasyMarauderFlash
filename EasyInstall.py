#!/bin/python3
import os
import platform
from git import Repo
import glob
import time
import shutil
import serial.tools.list_ports
import requests
import json
import esptool
from colorama import Fore, Back, Style
from pathlib import Path
import git
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('-s', '--serialport', type=str, help="Define serial port", default='')
args=parser.parse_args()
serialport=args.serialport

OPENASCII=Fore.GREEN+'''
#################################################################################
#    Marauder Flasher Script							#
#    Python edition by SkeletonMan based off of a Windows Batch			#
#    script by Frog, UberGuidoz, and ImprovingRigamarole			#
#										#
#    Thanks to everyone who has done testing on various chips for me		#
#    Thanks to Scorp for compiling needed bins for the ESP32-WROOM		#
#    Thanks to AWOK for pointing out a bug, adding his boards, and testing  	#
#################################################################################
'''+Style.RESET_ALL

print(OPENASCII)
print("Make sure your ESP32 or WiFi devboard is plugged in!")
BR=str("115200")

def checkforserialport():
	global serialport
	if serialport!='':
		print("Will not check for serial port or possible chip type since it is specified as", serialport)
		return
	else:
		serialport=''
	print("Checking for serial port...")
	vids=['303A','10C4','1A86', '0483']
	com_port=None
	ports=list(serial.tools.list_ports.comports())
	for vid in vids:
		for port in ports:
			if vid in port.hwid:
				serialport=port.device
				device=vid
	if serialport=='':
		print(Fore.RED+"No ESP32 device was detected!"+Style.RESET_ALL)
		print(Fore.RED+"Please plug in a Flipper WiFi devboard or an ESP32 chip and try again"+Style.RESET_ALL)
		choose_fw()
	if device=='':
		return
	elif device=='303A':
		print(Fore.BLUE+"You are most likely using a Flipper Zero WiFi Devboard or an ESP32-S2"+Style.RESET_ALL)
	elif device=='10C4':
		print(Fore.BLUE+"You are most likely using an ESP32-WROOM, an ESP32-S2-WROVER, or an ESP32-S3-WROOM"+Style.RESET_ALL)
	elif device=='1A86':
		print(Fore.MAGENTA+"You are most likely using a knock-off ESP32 chip! Success is not guaranteed!"+Style.RESET_ALL)
	elif device== '0483':
		print(Fore.BLUE+"You are most likely using an DrB0rk S3 Multiboard"+Style.RESET_ALL)

	return

def checkforextrabins():
	extraesp32binsrepo="https://github.com/UberGuidoZ/Marauder_BINs.git"
	global extraesp32bins
	extraesp32bins=("Extra_ESP32_Bins")
	global scorpbins
	scorpbins=(extraesp32bins+"/Marauder/WROOM")
	if os.path.exists(extraesp32bins):
		print("The extra ESP32 bins folder exists!")
	else:
		print("The extra ESP32 bins folder does not exist!")
		print("That's okay, downloading them now...")
		Repo.clone_from(extraesp32binsrepo, extraesp32bins)
	return

def choose_fw():
	choices='''
//==================================================================\\\ 
|| Options:						            ||
||  1) Flash Marauder on WiFi Devboard or ESP32-S2	            ||
||  2) Flash SD Serial Marauder on Devboard or ESP32-S2	            ||
||  3) Save Flipper Blackmagic WiFi settings		            ||
||  4) Flash Flipper Blackmagic				            ||
||  5) Flash Marauder on ESP32-WROOM			            ||
||  6) Flash Marauder on ESP32 Marauder Mini		            ||
||  7) Flash Marauder on ESP32-S3			            ||
||  8) Flash Marauder on AWOK v1-3 or Duoboard                      ||
||  9) Flash Marauder on AWOK v4 Chungus Board                      ||
|| 10) Flash Marauder on AWOK v5 ESP32                              ||
|| 11) Flash Marauder on AWOK Dual ESP32 (Orange Port)              ||
|| 12) Flash Marauder on AWOK Dual ESP32 Touch Screen (White Port)  ||
|| 13) Flash Marauder on AWOK Dual ESP32 Mini (White Port)          ||
|| 14) Update all files					            ||
|| 15) Exit						            ||
\\\==================================================================//
'''
#I know having all these globals isn't great, I may or may not fix it later
	global selectedfw
	global selectedboard
	global flashsize
	global offset_one
	global bootloader_bin
	global offset_two
	global partitions_bin
	global offset_three
	global boot_app
	global offset_four
	global fwbin
	global chip

	print(choices)
	fwchoice=int(input("Please enter the number of your choice: "))
	if fwchoice==1:
		print("You have chosen to flash Marauder on a WiFi devboard or ESP32-S2")
		chip="esp32s2"
		selectedfw="Marauder"
		selectedboard="ESP32-S2"
		flashsize='4MB'
		offset_one='0x1000'
		bootloader_bin=extraesp32bins+'/Marauder/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=extraesp32bins+'/Marauder/partitions.bin'
		offset_three='0x10000'
		fwbin=esp32marauderfw
		checkforserialport()
		flashtheboard()
	elif fwchoice==2:
		print("You have chosen to flash Marauder on a WiFi devboard or ESP32-S2 with SD Serial Support")
		chip="esp32s2"
		selectedfw="Marauder with SD Serial Support"
		selectedboard="ESP32-S2"
		flashsize='4MB'
		offset_one='0x1000'
		bootloader_bin=extraesp32bins+'/Marauder/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=extraesp32bins+'/Marauder/partitions.bin'
		offset_three='0x10000'
		fwbin=esp32marauderfwserial
		checkforserialport()
		flashtheboard()
	elif fwchoice==3:
		print("You have chosen to save Flipper Blackmagic WiFi settings")
		chip="esp32s2"
		checkforserialport()
		save_flipperbmsettings()
	elif fwchoice==4:
		print("You have chosen to flash Flipper Blackmagic")
		chip="esp32s2"
		checkforserialport()
		flash_flipperbm()
	elif fwchoice==5:
		print("You have chosen to flash Marauder onto an ESP32-WROOM")
		chip="esp32"
		selectedfw="Marauder"
		selectedboard="ESP32-WROOM"
		flashsize='2MB'
		offset_one='0x1000'
		bootloader_bin=scorpbins+'/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=scorpbins+'/partitions.bin'
		offset_three='0x10000'
		fwbin=espoldhardwarefw
		checkforserialport()
		flashtheboard()
	elif fwchoice==6:
		print("You have chosen to flash Marauder onto an ESP32 Marauder Mini")
		chip="esp32"
		selectedfw="Marauder"
		selectedboard="ESP32 Marauder Mini"
		flashsize='2MB'
		offset_one='0x1000'
		bootloader_bin=scorpbins+'/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=scorpbins+'/partitions.bin'
		offset_three='0x10000'
		fwbin=esp32minifw
		checkforserialport()
		flashtheboard()
	elif fwchoice==7:
		print("You have chosen to flash Marauder onto an ESP32-S3")
		chip="esp32s3"
		selectedfw="Marauder"
		selectedboard="ESP32-S3"
		flashsize='8MB'
		offset_one='0x0'
		bootloader_bin=extraesp32bins+'/S3/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=extraesp32bins+'/S3/partitions.bin'
		offset_three='0xE000'
		boot_app=extraesp32bins+'/S3/boot_app0.bin'
		offset_four='0x10000'
		fwbin=esp32s3fw
		checkforserialport()
		flashtheboardwithappbin()
	elif fwchoice==8:
		print("You have chosen to flash Marauder onto an AWOK v1-3 or Duoboard")
		chip="esp32"
		selectedfw="Marauder"
		selectedboard="AWOK v1-3 or Duoboard"
		flashsize='2MB'
		offset_one='0x1000'
		bootloader_bin=scorpbins+'/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=scorpbins+'/partitions.bin'
		offset_three='0x10000'
		fwbin=espoldhardwarefw
		checkforserialport()
		flashtheboard()
	elif fwchoice==9:
		print("You have chosen to flash Marauder on an AWOK v4 Chungus Board")
		chip="esp32s2"
		selectedfw="Marauder"
		selectedboard="AWOK v4 Chungus Board"
		flashsize='4MB'
		offset_one='0x1000'
		bootloader_bin=extraesp32bins+'/Marauder/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=extraesp32bins+'/Marauder/partitions.bin'
		offset_three='0x10000'
		fwbin=esp32marauderfw
		checkforserialport()
		flashtheboard()
	elif fwchoice==10:
		print("You have chosen to flash Marauder on an AWOK v5 ESP32")
		chip="esp32s2"
		selectedfw="Marauder with SD Serial Support"
		selectedboard="AWOK v5 ESP32"
		flashsize='4MB'
		offset_one='0x1000'
		bootloader_bin=extraesp32bins+'/Marauder/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=extraesp32bins+'/Marauder/partitions.bin'
		offset_three='0x10000'
		fwbin=esp32marauderfwserial
		checkforserialport()
		flashtheboard()
	elif fwchoice==11:
		print("You have chosen to flash Marauder on an AWOK Dual ESP32 (Orange Port)")
		chip="esp32s2"
		selectedfw="Marauder with SD Serial Support"
		selectedboard="AWOK Dual ESP32 (Orange Port)"
		flashsize='4MB'
		offset_one='0x1000'
		bootloader_bin=extraesp32bins+'/Marauder/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=extraesp32bins+'/Marauder/partitions.bin'
		offset_three='0x10000'
		fwbin=esp32marauderfwserial
		checkforserialport()
		flashtheboard()
	elif fwchoice==12: 
		print("You have chosen to flash Marauder onto an AWOK Dual ESP32 Touch Screen (White Port)")
		chip="esp32"
		selectedfw="Marauder"
		selectedboard="AWOK Dual ESP32 Touch Screen (White Port)"
		flashsize='2MB'
		offset_one='0x1000'
		bootloader_bin=scorpbins+'/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=scorpbins+'/partitions.bin'
		offset_three='0x10000'
		fwbin=espnewhardwarefw
		checkforserialport()
		flashtheboard()
	elif fwchoice==13:
		print("You have chosen to flash Marauder onto an AWOK Dual ESP32 Mini (White Port)")
		chip="esp32"
		selectedfw="Marauder Mini"
		selectedboard="AWOK Dual ESP32 Mini (White Port)"
		flashsize='2MB'
		offset_one='0x1000'
		bootloader_bin=scorpbins+'/bootloader.bin'
		offset_two='0x8000'
		partitions_bin=scorpbins+'/partitions.bin'
		offset_three='0x10000'
		fwbin=esp32minifw
		checkforserialport()
		flashtheboard()
	elif fwchoice==14:
		print("You have chosen to update all of the files")
		update_option()
	elif fwchoice==15:
		print("You have chosen to exit")
		print("Exiting!")
		exit()
	else:
		print(Fore.RED+"Invalid option!"+Style.RESET_ALL)
		exit()
	return

def erase_esp32fw():
	tries=3
	attempts=0
	for i in range(tries):
		try:
			attempts+=1
			print("Erasing firmware...")
			esptool.main(['-p', serialport, '-b', BR, '-c', chip, '--before', 'default_reset', '-a', 'no_reset', 'erase_region', '0x9000', '0x6000'])
		except Exception as err:
			print(err)
			if attempts==3:
				print("Unable to erase the firmware on", chip)
				exit()
			print("Waiting 5 seconds and trying again...")
			time.sleep(5)
			continue
		print(chip, "was successfully erased!")
		break
	print("Waiting 5 seconds...")
	time.sleep(5)	
	return

def checkforesp32marauder():
	print("Checking for Marauder releases")
	if os.path.exists("ESP32Marauder/releases"):
		print("Great, you have the Marauder releases folder!")
	else:
		print("Marauder releases folder does not exist, but that's okay, downloading them now...")
		os.makedirs('ESP32Marauder/releases')
		marauderapi="https://api.github.com/repos/justcallmekoko/ESP32Marauder/releases/latest"
		response=requests.get(marauderapi)
		jsondata=response.json()
		assetdls=range(0,10)
		for assetdl in assetdls:
			marauderasset=jsondata['assets'][assetdl]['browser_download_url']
			if marauderasset.find('/'):
				filename=(marauderasset.rsplit('/', 1)[1])
			downloadfile=requests.get(marauderasset, allow_redirects=True)
			open('ESP32Marauder/releases/'+filename, 'wb').write(downloadfile.content)
	esp32marauderfwc=('ESP32Marauder/releases/esp32_marauder_v*_flipper.bin')
	if not glob.glob(esp32marauderfwc):
		print("No ESP32 Marauder Flipper firmware exists somehow!")
	global esp32marauderfw
	for esp32marauderfw in glob.glob(esp32marauderfwc):
		if os.path.exists(esp32marauderfw):
			print("ESP32 Marauder firmware exists at", esp32marauderfw)
	return

def checkforesp32marauderserial():
	esp32marauderfwserialc=('ESP32Marauder/releases/esp32_marauder_v*_flipper_sd_serial.bin')
	if not glob.glob(esp32marauderfwserialc):
		print("No ESP32 Marauder Flipper SD Serial firmware exists somehow!")
	global esp32marauderfwserial
	for esp32marauderfwserial in glob.glob(esp32marauderfwserialc):
		if os.path.exists(esp32marauderfwserial):
			print("ESP32 Marauder firmware exists at", esp32marauderfwserial)
	return

def checkfors3bin():
	esp32s3fwc=('ESP32Marauder/releases/esp32_marauder_v*_multiboardS3.bin')
	if not glob.glob(esp32s3fwc):
		print("mutliboards3 bin does not exist!")
	global esp32s3fw
	for esp32s3fw in glob.glob(esp32s3fwc):
		if os.path.exists(esp32s3fw):
			print("ESP32-S3 firmware bin exists at", esp32s3fw)
		else:
			print("Somehow, the mutliboardS3.bin file does not exist!")
	return

def checkforoldhardwarebin():
	espoldhardwarefwc=('ESP32Marauder/releases/esp32_marauder_v*_old_hardware.bin')
	if not glob.glob(espoldhardwarefwc):
		print("old_hardware bin does not exist!")
	global espoldhardwarefw
	for espoldhardwarefw in glob.glob(espoldhardwarefwc):
		if os.path.exists(espoldhardwarefw):
			print("Old Hardware bin exists at", espoldhardwarefw)
		else:
			print("Somehow, the old_hardware.bin file does not exist!")
	return

def checkforminibin():
	esp32minifwc=('ESP32Marauder/releases/esp32_marauder_v*_mini.bin')
	if not glob.glob(esp32minifwc):
		print("mini bin does not exist!")
	global esp32minifw
	for esp32minifw in glob.glob(esp32minifwc):
		if os.path.exists(esp32minifw):
			print("Mini bin exists at", esp32minifw)
		else:
			print("Somehow, the mini bin does not exist!")
	return

def checkfornewhardwarebin():
	espnewhardwarefwc=('ESP32Marauder/releases/esp32_marauder_v*_new_hardware.bin')
	if not glob.glob(espnewhardwarefwc):
		print("new_hardware bin does not exist!")
	global espnewhardwarefw
	for espnewhardwarefw in glob.glob(espnewhardwarefwc):
		if os.path.exists(espnewhardwarefw):
			print("New Hardware bin exists at", espnewhardwarefw)
		else:
			print("Somehow, the new_hardware.bin file does not exist!")
	return

def prereqcheck():
	print("Checking for prerequisites...")
	checkforextrabins()
	checkforesp32marauder()
	checkforesp32marauderserial()
	checkfors3bin()
	checkforoldhardwarebin()
	checkforminibin()
	checkfornewhardwarebin()
	return

def flashtheboard():
	erase_esp32fw()
	tries=3
	attempts=0
	for i in range(tries):
		try:
			attempts+=1
			print("Flashing", selectedfw, "on", selectedboard)
			esptool.main(['-p', serialport, '-b', BR, '-c', chip, '--before', 'default_reset', '-a', 'no_reset', 'write_flash', '--flash_mode', 'dio', '--flash_freq', '80m', '--flash_size', flashsize, offset_one, bootloader_bin, offset_two, partitions_bin, offset_three, fwbin])
		except Exception as err:
			print(err)
			if attempts==3:
				print("Could not flash", selectedfw, "on", selectedboard)
				exit()
			print("Waiting 5 seconds and trying again...")
			time.sleep(5)
			continue
		print(Fore.GREEN+selectedboard, "has been flashed with", selectedfw+Style.RESET_ALL)
		break
	return

def flashtheboardwithappbin():
	erase_esp32fw()
	tries=3
	attempts=0
	for i in range(tries):
		try:
			attempts+=1
			print("Flashing", selectedfw, "on", selectedboard)
			esptool.main(['-p', serialport, '-b', BR, '-c', chip, '--before', 'default_reset', '-a', 'no_reset', 'write_flash', '--flash_mode', 'dio', '--flash_freq', '80m', '--flash_size', flashsize, offset_one, bootloader_bin, offset_two, partitions_bin, offset_three, boot_app, offset_four, fwbin])
		except Exception as err:
			print(err)
			if attempts==3:
				print("Could not flash", selectedfw, "on", selectedboard)
				exit()
			print("Waiting 5 seconds and trying again...")
			time.sleep(5)
			continue
		print(Fore.GREEN+selectedboard, "has been flashed with", selectedfw+Style.RESET_ALL)
		break
	return

def save_flipperbmsettings():
	tries=3
	attempts=0
	for i in range(tries):
		try:
			attempts +=1
			print("Saving Flipper Blackmagic WiFi Settings to Extra_ESP32_Bins/Blackmagic/nvs.bin")
			esptool.main(['-p', serialport, '-b', BR, '-c', chip, '-a', 'no_reset', 'read_flash', '0x9000', '0x6000', extraesp32bins+'/Blackmagic/nvs.bin'])
		except Exception as err:
			print(err)
			if attempts==3:
				print("Could not save Flipper Blackmagic WiFi Settings")
				exit()
			print("Waiting 5 seconds and trying again...")
			time.sleep(5)
			continue
		print(Fore.GREEN+"Flipper Blackmagic Wifi Settings have been saved to ", extraesp32bins+"/Blackmagic/nvs.bin!"+Style.RESET_ALL)
		break
	return

def flash_flipperbm():
	if os.path.exists(extraesp32bins+"/Blackmagic/nvs.bin"):
		erase_esp32fw()
		tries=3
		attempts=0
		for i in range(tries):
			try:
				attempts +=1
				print("Flashing Flipper Blackmagic with WiFi Settings restore")
				esptool.main(['-p', serialport, '-b', BR, '-c', chip, '--before', 'default_reset', '-a', 'no_reset', 'write_flash', '--flash_mode', 'dio', '--flash_freq', '80m', '--flash_size', '4MB', '0x1000', extraesp32bins+'/Blackmagic/bootloader.bin', '0x8000', extraesp32bins+'/Blackmagic/partition-table.bin', '0x9000', extraesp32bins+'/Blackmagic/nvs.bin', '0x10000', extraesp32bins+'/Blackmagic/blackmagic.bin'])
			except Exception as err:
				print(err)
				if attempts==3:
					print("Could not flash Blackmagic with WiFi Settings")
					exit()
				print("Waiting 5 seconds and trying again...")
				time.sleep(5)
				continue
			print(Fore.GREEN+"Flipper Blackmagic has been flashed with the WiFi Settings restored"+Style.RESET_ALL)
			break
		return
	else:
		erase_esp32fw()
		tries=3
		attempts=0
		for i in range(tries):
			try:
				attempts +=1
				print("Flashing Flipper Blackmagic without WiFi Settings restore")
				esptool.main(['-p', serialport, '-b', BR, '-c', chip, '--before', 'default_reset', '-a', 'no_reset', 'write_flash', '--flash_mode', 'dio', '--flash_freq', '80m', '--flash_size', '4MB', '0x1000', extraesp32bins+'/Blackmagic/bootloader.bin', '0x8000', extraesp32bins+'/Blackmagic/partition-table.bin', '0x10000', extraesp32bins+'/Blackmagic/blackmagic.bin'])
			except Exception as err:
				print(err)
				if attempts==3:
					print("Could not flash Blackmagic")
					exit()
				print("Waiting 5 seconds and trying again...")
				time.sleep(5)
				continue
			print(Fore.GREEN+"Flipper Blackmagic has been flashed without WiFi Settings restored"+Style.RESET_ALL)
			break
	return

def update_option():
	print("Checking for and deleting the files before replacing them...")
	cwd = os.getcwd()
	for paths in Path(cwd).rglob('ESP32Marauder/*/*'):
		os.remove(paths)
	os.rmdir('ESP32Marauder/releases')
	os.rmdir('ESP32Marauder')
	extrarepo = os.path.join(cwd, "Extra_ESP32_Bins")
	repo = Repo(extrarepo)
	repo.git.reset('--hard')
	repo.git.clean('-xdf')
	repo.remotes.origin.pull()
	prereqcheck()
	choose_fw()
	return

prereqcheck()
choose_fw()
