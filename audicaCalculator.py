import json
import shutil
from mido import MidiFile
import mido
import midi
import os
import csv
from math import sqrt
#variables to be adjusted
spacing_difficulty = 0.25
spacing_cap = 1.8

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
    tempo = -1
    for i, track in enumerate(mid.tracks):
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
    #empty tempo handling
    if tempo == -1:
        tempo = mapdesc["tempo"]
    #get tempos
    def get_tempos_from_midi(midi_file):
        pattern = midi.read_midifile("./temp/" + midiname)
        tick = 0
        temposList = []

        for track in pattern:
            for event in track:
                if type(event) is midi.SetTempoEvent:
                    tick += event.tick
                    temposList.append({
                        "tick": tick,
                        "tempo": event.get_bpm()
                        })
                #empty tempo handling
                if not temposList:
                    temposList.append({
                        "tick": 0,
                        "tempo": tempo
                        })
        # for i, track in enumerate(pattern.tracks):
        #     for msg in track:
        #         if msg.type == 'set_tempo':
        #             tempos.append({
        #                 "tick": msg.tick,
        #                 "tempo": msg.tempo
        #                 })
            return temposList

    print("Audica BPM: " + str(round(mido.tempo2bpm(tempo), 2)) + "\n")

    def getDifficultyRating(difficultyName):
        with open ("./temp/" + difficultyName) as map:
            audicamap = json.load(map)
            cues = audicamap["cues"]

        midiForTempo = MidiFile("./temp/" + midiname)
        tempos = get_tempos_from_midi(midiForTempo)

        # print("previous last cue: " + str(cues[-1]["tick"]) + " at " + str(tempo))
        # mapLength = cues[-1]["tick"] / 480 * tempo / 1000000
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
            cueSpacing = object.get("spacing", 0) * spacing_difficulty
            # cap spacing difficulty weight
            if ( cueSpacing > spacing_cap):
                print("beeg spacing alert beeg spacing alert: " + str(cueSpacing))
                cueSpacing = spacing_cap
            if object["behavior"] == 0: #normal circle
                difficulty = 1 + cueSpacing
            elif object["behavior"] == 1: #vertical object
                difficulty = 1.2 + cueSpacing
            elif object["behavior"] == 2: #horizontal object
                difficulty = 1.3 + cueSpacing
            elif object["behavior"] == 3: #sustain
                difficulty = 1 + cueSpacing
            elif object["behavior"] == 4: #chain start
                difficulty = 1.2 + cueSpacing
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

        #function to calculate time between given cues
        def get_delta_time(cue):
        #tempos = self.tempos
            if len(tempos) > 1:
                # print(str(cue["tick"]))
                tick = cue["tick"]
                time = 0
                last_tempo = 0
                last_tick = 0
                for tempo in tempos:
                    bpm = tempo["tempo"]
                    t = tempo["tick"]
                    if t != 0:
                        if tick >= t:
                            tick_time = 60000 / (last_tempo * 480)
                            tick_count = t - last_tick
                            time = time + (tick_time * tick_count)
                            last_tempo = bpm
                            last_tick = t
                        else:
                            break
                    else:
                        last_tempo = bpm
                difference = tick - last_tick
                if difference != 0:
                    tick_time = 60000 / (last_tempo * 480)
                    time = time + (tick_time * difference)
                return time
            else:
                # print("ELSE get_delta_time tempos: " + str(mido.bpm2tempo(tempos[0]["tempo"])))
                # print("cue tick: " + str(cue["tick"]))
                return cue["tick"] / 480 * mido.bpm2tempo(tempos[0]["tempo"]) /1000
                #/ 1000000

        #get first and last cues

        firstCueTime = round(get_delta_time(finalCuesSorted[0]), 2)
        lastCueTime = round(get_delta_time(finalCuesSorted[-1]), 2)

        # print("1st: " + str(firstCueTime))
        # print("Last: " + str(lastCueTime))

        # print("prev mapLength: " + str(mapLength))

        mapLength = (lastCueTime - firstCueTime) / 1000

        # print("cur mapLength: " + str(round(mapLength, 2)))

        NPS = round((objectCount / mapLength), 2)
        StarRating = str( round((calculatedObjects / mapLength), 2))
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

