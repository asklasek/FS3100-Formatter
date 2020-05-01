# Converts CSV file from Prep Data into a usable file for OI FS-3100

# Output text file`s format:
# Row number=Cup number`Sample name`Injection type`Repetitions`Dilution`Weight`Vial number`Comment

# test1 signifies Ammonia
# test2 signifies NO2NO3

import time
import sys

def main():
    runName=input("Enter the name of the run: ")    # User inputs the name for the run and file to be written.
    test=verifyTest(input("Enter the test name: ")) # User inputs the test name.
    wgName=input("Enter a workgroup number: ")      # User inputs the first workgroup number.
    runList, rowNum=initializeRunList(test)
    cupNum=114 # Initialize the sample cup numbers
    while wgName!="":
        fileNameIn=formatName(wgName)     # Create infile name.
        try:
            inFile=open(fileNameIn, "r")  # Open file for reading.
            wgNum=fileNameIn[0:8]         # Workgroup number.
            runList, rowNum, injections=startingQC(runList,test,rowNum,wgNum) # Add starting QC to the run list. Initialize injection count.
            sampleList=sortSamples(wgNum, inFile)                             # Sort the L-numbers, spikes and dups for the workgroup.
            runList, rowNum, cupNum=addSamples(runList, sampleList, test, rowNum, wgNum, injections, cupNum) # Add  the samples to the run list.
        except IOError: # Ensure user`s file is in the folder.
            print(fileNameIn + " was not a valid file in the folder.")
        wgName=input('Submit another workgroup number or press "Enter" to complete the entries: ')   # User inputs the workgroup number to be formatted.
    writeRun(runList, runName) # Write the samples to the formatted file.
    time.sleep(3)

# writeRun() takes a list and writes it to an out file named from the runName.
def writeRun(runList, runName):
    try:            # Create the .tbl file to be written to.
        fileNameOut=runName+".tbl"
        outFile=open(fileNameOut, "w")
    except IOError: # Exit the program if file cannot be created.
        print(fileNameOut+" could not be created.")
        time.sleep(4)
        sys.exit(1)
    rows="Rows="+str(len(runList))  # Find the total rows and create the header list.
    header=["","[Sample Table]","Signature=EnviroFlow Sample Table File.","Version=3","SoftwareRevision=234",rows,"Columns=8"]
    for item in header: # Write the header for the document to the outfile.
        outFile.write(item+"\n")
    for item in runList:       # Write the list of samples to the outfile.
        outFile.write(item+"\n")
    print("File created successfully.")
    

def addSamples(runList, sampleList, test, rowNum, wgNum, injections, cupNum):
    for item in sampleList:
        strRowNumber, rowNum=rowConverter(rowNum) # Increase and format the row number.
        strCupNum=str(cupNum)   # Format and increase the cup number.
        cupNum+=1
        injections+=1
        if injections>10: # Insert a CCV/CCB bracketing pair every 10 injections.
            injections=1  # Reset injections to 1
            if test=="test1": # Ammonia Bracket
                bracketList=["102`CCV`U`1`1`1`0`","0`CCB`U`1`1`1`0`","0`Read Baseline`RB`1`1`1`0`"]
                for QC in bracketList:
                    runList.append(strRowNumber+QC)
                    strRowNumber, rowNum=rowConverter(rowNum)
            else:
                bracketList=["107`CCV-NO3`U`1`1`1`0`","108`CCV-NO2`U`1`1`1`0`","0`CCB`U`1`1`1`0`","0`Read Baseline`RB`1`1`1`0`"]
                for QC in bracketList:
                    runList.append(strRowNumber+QC)
                    strRowNumber, rowNum=rowConverter(rowNum)
        line=strRowNumber+strCupNum+"`"+item+"`U`1`1`1`0`" # Line format for Omnion csv format.
        runList.append(line)
    #strRowNumber, rowNum=rowConverter(rowNum)  # Add a closing bracket of CCV/CCB
    if test=="test1": # Ammonia Bracket
        bracketList=["102`CCV`U`1`1`1`0`","0`CCB`U`1`1`1`0`","0`Read Baseline`RB`1`1`1`0`"]
        for QC in bracketList:
            strRowNumber, rowNum=rowConverter(rowNum)
            runList.append(strRowNumber+QC)
    else:
        bracketList=["107`CCV-NO3`U`1`1`1`0`","108`CCV-NO2`U`1`1`1`0`","0`CCB`U`1`1`1`0`","0`Read Baseline`RB`1`1`1`0`"]
        for QC in bracketList:
            strRowNumber, rowNum=rowConverter(rowNum)
            runList.append(strRowNumber+QC)
    return runList, rowNum, cupNum
    

# sortSamples() creates a list of samples from the csv file of a workgroup that is sorted in numerical order with the
# Duplicate and Spiked samples added in the appropriate order. The .csv file is also closed. The sorted list is returned.
def sortSamples(wgNum, inFile):
    numList=[]    # List of numbers to be sorted.
    sampleList=[] # Sorted L-numbers with spikes and duplicates.
    file=inFile.readlines()
    for item in file:
        if item[0]=="L" and item[1]!="C":               # Ensure that LCS/LCSD are not appended to the list.
            num=int(item[1:7])+(float(item[8:10])/100)  # Convert the L number into a decimal for sorting.
            numList.append(num)
    numList.sort()        # Put the L numbers in numerical order.
    for item in numList:  # Revert numbers back to L-numbers and append to list.
        strNum=str(item).split(".")
        if len(strNum[1])==1:  # Add the zero back to mulitples of ten since the float division does not keep trailing zeros.
            LNum="L"+strNum[0]+"-"+strNum[1]+"0 "+wgNum
        else:
            LNum="L"+strNum[0]+"-"+strNum[1]+" "+wgNum
        sampleList.append(LNum)
        for item in file: # Add any Duplicates or Spikes to the list after the parent sample.
            if item[4:23]==LNum or item[3:22]==LNum:
                sampleList.append(item.rstrip("\n"))
    inFile.close()     # Close the workgroup`s .csv file
    return sampleList  # Return the sorted sample list.

# startingQC() takes a run list, test type, number of rows, and workgroup name, adds the starting QC for the workgroup, and returns the runList.
# The injections counter is also initialized and returned.
def startingQC(runList, test, rowNum, wgNum):
    if test=="test1": # Ammonia initializing QC.
        startingQCList=["102`ICV`U`1`1`1`0`","0`Blank "+wgNum+"`U`1`1`1`0`","109`LCS`U`1`1`1`0`","110`LCSD`U`1`1`1`0`"]
        if rlvCheck()==True: # Check for Drinking Water in the workgroup.
            startingQCList.append("105`RL 0.100`U`1`1`1`0`")
        for item in startingQCList: # Add the initial QC for the workgroup to the run list.
            strRowNumber, rowNum=rowConverter(rowNum) # Increase and format the row.
            runList.append(strRowNumber+item)     # Append the information from the QC List.
        injections=len(startingQCList)-1 # Initialize the injections counter from the ICV
    else: # NO2NO3 initializing QC.
        startingQCList=["107`ICV-NO3`U`1`1`1`0`","108`ICV-NO2`U`1`1`1`0`","0`Blank "+wgNum+"`U`1`1`1`0`","109`LCS`U`1`1`1`0`","110`LCSD`U`1`1`1`0`"]
        if rlvCheck()==True: # Check for Drinking Water in the workgroup.
            startingQCList.append("101`RL 0.100`U`1`1`1`0`")
        for item in startingQCList: # Add the initial QC for the workgroup to the run list.
            strRowNumber, rowNum=rowConverter(rowNum) # Increase and format the row.
            runList.append(strRowNumber+item)     # Append the information from the QC List.
        injections=len(startingQCList)-2 # Initialize the injections counter from the ICV
    return runList, rowNum, injections

# initializeRunList() adds the starting information for the run and an optional calibration based on the test.
def initializeRunList(test):
    if test=="test1":   # Ammonia initiallizing injections.
        runList=["Row_001=102`Sync`SYNC`1`1`1`0`","Row_002=0`INSTBLK`CO`1`1`1`0`","Row_003=0`Read Baseline`RB`1`1`1`0`",
                 "Row_004=101`Cal 10.0 ppm`C`1`1`1`0`","Row_005=102`Cal 5.00 ppm`C`1`1`1`0`","Row_006=103`Cal 2.50 ppm`C`1`1`1`0`",
                 "Row_007=104`Cal 1.00 ppm`C`1`1`1`0`","Row_008=105`Cal 0.10 ppm`C`1`1`1`0`","Row_009=0`Cal 0.00 ppm`C`1`1`1`0`",
                 "Row_010=0`Read Baseline`RB`1`1`1`0`"]
    else:               # NO2NO3 initiallizing injections.
        runList=["Row_001=106`Sync`SYNC`1`1`1`0`","Row_002=0`INSTBLK`CO`1`1`1`0`","Row_003=0`Read Baseline`RB`1`1`1`0`",
                 "Row_004=0`Cal 0.000 ppm`C`1`1`1`0`","Row_005=102`Cal 0.100 ppm`C`1`1`1`0`","Row_006=103`Cal 0.500 ppm`C`1`1`1`0`",
                 "Row_007=104`Cal 1.000 ppm`C`1`1`1`0`","Row_008=105`Cal 2.500 ppm`C`1`1`1`0`","Row_009=106`Cal 5.000 ppm`C`1`1`1`0`",
                 "Row_010=106`Cal 10.00 ppm`C`1`1`1`0`","Row_011=0`Read Baseline`RB`1`1`1`0`"]
    rowNum=len(runList) # Initialize the row count.
    return runList, rowNum

# rowConverter() takes the row number, adds 1 to it, and converts it to the format for the file. The new row number and formatted row string are returned.
def rowConverter(rowNum):
    rowNum+=1
    if rowNum<10:    # Single Digit row.
        strRowNum="Row_00"+str(rowNum)+"="
    elif rowNum<100: # Double Digit row.
        strRowNum="Row_0"+str(rowNum)+"="
    else:          # Triple Digit row.
        strRowNum="Row_"+str(rowNum)+"="
    return strRowNum, rowNum

def rlvCheck():
    rlv=input("Is there an RLV to be analyzed (Y/N): ")
    if rlv.lower()=="y" or rlv.lower()=="yes":
        return True
    return False

# verifyTest() ensures that the test is applicable to the program and ends the program if the test cannot be handled.
def verifyTest(test):
    if test.lower()=="nh3" or test.lower()=="ammonia":
        return "test1"
    elif test.lower()=="no2no3" or test.lower()=="nox":
        return "test2"
    else:
        print("\n\nThat is not a valid test for this program.")
        time.sleep(4)
        sys.exit(1)
    
# formatName() takes the user input and formats it to the name of the .csv file created from Prep Data
def formatName(wgName):
    name=""
    for char in wgName:
        if char.isdigit()==True:  # Only takes the digits that the user entered.
            name+=char
    nameIn="WG"+name+".csv"       # Input file's name
    return nameIn

if __name__=="__main__":
    main()
