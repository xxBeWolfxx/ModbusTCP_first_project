from random import randrange
import time
import re
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.register_read_message import ReadInputRegistersResponse

#   Registers in use: (-1)
#       Recipes: R10,R11,R12
#       Tank: R100
#       Communication: R98
#   Markes:
#       refuelingStart: M101
#       refuelingStop: M102
#       refuelingDrop: M103


client = 0
valueTank = 0
statusCommuniaction = 0
recipeO = 0
recipeF = 0
refuelingStart = 0
releaseStart = 0
temp_rec_F = 0
temp_rec_O = 0
temp_val_tank = 0
fisrtStarting = True
runningPLC = True


def ReadingRegisters():
    global statusCommuniaction
    global valueTank
    global client
    global recipeF
    global recipeO
    global refuelingStart
    global releaseStart
    global launchingStart

    refuelingStart = client.read_coils(97, 1, unit=0x01).bits[0]
    releaseStart = client.read_coils(96, 1, unit=0x01).bits[0]
    temp_recipe = client.read_holding_registers(10, 2, unit=0x01)
    recipeF = int(temp_recipe.registers[0])
    recipeO = int(temp_recipe.registers[1])
    statusCommuniaction = int(client.read_holding_registers(
        97, 1, unit=0x01).registers[0])
    valueTank = int(client.read_holding_registers(
        99, 1, unit=0x01).registers[0])
    launchingStart = client.read_coils(0, 1, unit=0x01).bits[0]


def RefuelingTank(temp_recipe, recipe):
    temp_recipe = RandomNumberTo100(temp_recipe, recipe)
    return temp_recipe


def ReleaseTank(tank_value):
    if tank_value > 0:
        if tank_value < 10:
            tank_value = 0
        else:
            tank_value = tank_value - 10
    print("Process of fuel drain: ", tank_value)
    return tank_value


def SystemChecking(Communication, tank, client):
    if Communication == 2 and tank == 100:
        items = list(range(0, 57))
        l = len(items)

        # Initial call to print 0% progress
        printProgressBar(0, l, prefix='Progress:',
                         suffix='Complete', length=50)
        for i, item in enumerate(items):
            # Do stuff...
            time.sleep(0.1)
            # Update Progress Bar
            printProgressBar(i + 1, l, prefix='Progress:',
                             suffix='Complete', length=50)
        client.write_coil(1, 1, unit=0x01)


def RandomNumberTo100(value, max_value):

    if value < max_value - 10:
        temp = randrange(1, 10, 2)
        value = value + temp

    elif value > max_value - 11 and value < max_value:
        value = value + (max_value - value)
        time.sleep(1.5)

    return value


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def quittingProgram(status):
    global client
    if status:
        print("Closing connection with PLC")
        client.close()
    if not status:
        print("I can't connect to PLC")
    print("Goodbay")


def display(recipeF, recipeO, statusCommuniaction, valueTank, refuelingStart, launchingStart, temp_rec_F, temp_rec_O):
    print("**********************NEW DATA**************************")
    print("Recipe of fuel: ",  recipeF)
    print("Recipe of suboxide: ", recipeO)
    print("Status of communication: ", statusCommuniaction)
    print(
        "Status of: Tank: {0} fuel: {1} and suboxide: {2}".format(valueTank, temp_rec_F, temp_rec_O))
    print("Status of tank: ", refuelingStart)
    print("Startup status: ", launchingStart)
    print("---------------------------------------------------------")


while runningPLC:
    if fisrtStarting:
        ip = input("I need PLC's:  ")
        client = ModbusClient(ip)
        if not client.connect():
            runningPLC = False
        print("Communication: ", client.connect())
        fisrtStarting = False
    while client.connect():
        time.sleep(3.0)
        ReadingRegisters()
        display(recipeF, recipeO, statusCommuniaction,
                valueTank, refuelingStart, launchingStart, temp_rec_F, temp_rec_O)
        client.write_register(97, 2, unit=0x01)

        if refuelingStart:
            temp_rec_F = RefuelingTank(temp_rec_F, recipeF)
            client.write_register(60, temp_rec_F, unit=0x01)
            temp_rec_O = RefuelingTank(temp_rec_O, recipeO)
            client.write_register(61, temp_rec_O, unit=0x01)
            client.write_register(99, temp_rec_F+temp_rec_O, unit=0x01)
            temp_val_tank = temp_rec_F+temp_rec_O
            SystemChecking(statusCommuniaction, temp_val_tank, client)

        if releaseStart:
            temp_val_tank = ReleaseTank(temp_val_tank)
            client.write_register(99, temp_val_tank, unit=0x01)
            client.write_register(60, 0, unit=0x01)
            client.write_register(61, 0, unit=0x01)
            temp_rec_F = temp_rec_O = 0

        if launchingStart:
            temp_rec_F = temp_rec_O = 0

quittingProgram(client.connect())
