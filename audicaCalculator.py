import json
import shutil
from mido import MidiFile
import mido
import os
import csv
from math import sqrt
#variables to be adjusted
spacing_difficulty = 0.3

csvfile = open('output.csv', 'w', newline='', encoding="utf8")
fieldnames = ['Map Title', 'Difficulty', 'Difficulty Rating', "BPM", "Author"]
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
writer.writerow({'Map Title': "Song Name", 'Difficulty': "Difficulty", 'Difficulty Rating': "Difficulty Rating", 'Author': "Author", "BPM": "BPM"})


def calculateAudicaMap(filename):
    filename = filename

    cueFiles = []
    #reading zipfile
    from zipfile import ZipFile
    audicafile = ZipFile(filename, mode='r')
    #print(audicafile.namelist())

    #extract files
    for item in audicafile.namelist():
        if item.find('.mid') > 0:
            audicafile.extract(item, path="./temp/")
            midiname = item

    #get desc
    for item in audicafile.namelist():
        if item.find('.desc') > 0:
            audicafile.extract(item, path="./temp/")
            with open ("./temp/" + item) as desc:
                mapdesc = json.load(desc)
    MapTitle = mapdesc["artist"] + " - " + mapdesc["title"].split("<size")[0]
    author = mapdesc.get("author", "HMX")

    print("Map: " + MapTitle)
    print("Author: " + author)

    #get BPM
    mid = MidiFile("./temp/" + midiname)
    for i, track in enumerate(mid.tracks):
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo

    print("Audica BPM: " + str(round(mido.tempo2bpm(tempo), 2)) + "\n")

    def getDifficultyRating(difficultyName):
        with open ("./temp/" + difficultyName) as map:
            audicamap = json.load(map)
            cues = audicamap["cues"]

        mapLength = cues[-1]["tick"] / 480 * tempo / 1000000
        objectCount = 0
        calculatedObjects = 0
        
        leftHand = []
        rightHand = []
        anyHand = []

        finalCues = []

        def getTrueCoordinates(cue):
            pitch = cue["pitch"]
            x = pitch % 12
            y = int(pitch / 12)
            cue["trueX"] = x + cue["gridOffset"]["x"]
            cue["trueY"] = y + cue["gridOffset"]["y"]
            
        for item in cues:
            getTrueCoordinates(item)

        def getObjectDifficulty(object):
            difficulty = 0
            if object["behavior"] == 0: #normal circle
                difficulty = 1 + object.get("spacing", 0) * spacing_difficulty
            elif object["behavior"] == 1: #vertical object
                difficulty = 1.2 + object.get("spacing", 0) * spacing_difficulty
            elif object["behavior"] == 2: #horizontal object
                difficulty = 1.5 + object.get("spacing", 0) * spacing_difficulty
            elif object["behavior"] == 3: #sustain
                difficulty = 1 + object.get("spacing", 0) * spacing_difficulty
            elif object["behavior"] == 4: #chain start
                difficulty = 1.2 + object.get("spacing", 0) * spacing_difficulty
            elif object["behavior"] == 5: #chain node
                difficulty = 0.2 
            elif object["behavior"] == 6: #melee
                difficulty = 0.6
            return difficulty

        #divide the hand types into their own lists
        for item in cues:
            if item["handType"] == 1:
                rightHand.append(item)
            elif item["handType"] == 2:
                leftHand.append(item)
            else:
                anyHand.append(item)

        for x,y in zip(leftHand[::],leftHand[1::]):
        #    print(abs(y["gridOffset"]["x"] - x["gridOffset"]["x"]))
        #    print(y["tick"], x["tick"])
            y["spacing"] = sqrt( (y["trueX"] - x["trueX"])**2 + (y["trueY"] - x["trueY"])**2 )



        for x,y in zip(rightHand[::],rightHand[1::]):
        #    print(abs(y["gridOffset"]["x"] - x["gridOffset"]["x"]))
        #    print(y["tick"], x["tick"])
            y["spacing"] = sqrt( (y["trueX"] - x["trueX"])**2 + (y["trueY"] - x["trueY"])**2 )

        finalCues = leftHand + rightHand + anyHand

        finalCuesSorted = sorted(finalCues, key=lambda k: k['tick']) 

        '''
        with open("debug" + difficultyName + '.cues', 'w') as outfile:
            json.dump(cues, outfile, indent=4)
        '''

        for item in finalCuesSorted:
            if item["behavior"] != 5:
                objectCount += 1

            calculatedObjects += getObjectDifficulty(item)


        NPS = round((objectCount / mapLength), 2)
        StarRating = str( round((calculatedObjects / mapLength), 2))# + "★"  
        diffname = difficultyName.capitalize().replace(".cues", "")

        print("Difficulty: " + diffname)

        print( "Object count: " + str(objectCount) )
        print( "NPS: " + str( NPS ) )
        print( "Weighted objects: " + str( round(calculatedObjects, 2 )) )
        print( "Difficulty Rating: " + StarRating )
        print("")
        writer.writerow({'Map Title': MapTitle, 'Difficulty': diffname, 'Difficulty Rating': StarRating, 'Author': author, "BPM": round(mido.tempo2bpm(tempo), 2)})
        return diffname, NPS, StarRating

    for item in audicafile.namelist():
        if item.find('.cues') > 0:
            audicafile.extract(item, path="./temp/")
            cueFiles.append(item)
            diffname,nps,StarRating = getDifficultyRating(item)

    shutil.rmtree("./temp/")

for files in os.listdir("./maps/"):
    calculateAudicaMap("./maps/" + files)

