import json
from zipfile import ZipFile
import midi
import sys

class audica_file():

    def __init__(self, file):
        self.audica = ZipFile(file)
        self.desc = self.load_desc(self.audica.open("song.desc").read().decode("utf-8"))
        self.tempos = self.get_tempos_from_midi(self.audica.open(self.get_song_mid()))
        self.get_difficulties()

    def get_difficulties(self):
        self.difficulties = {}
        difficulty_list = []
        for name in self.audica.namelist():
            if ".cues" in name:
                difficulty_list.append(name)
            else:
                pass
        for file in difficulty_list:
            difficulty_name = file.replace(".cues", "")
            self.difficulties[difficulty_name] = self.load_diff(self.audica.open(file))

    def get_song_mid(self):
        moggsongitems = []
        for name in self.audica.namelist():
            if ".moggsong" in name:
                moggsongitems.append(name)
            else:
                pass
        try:
            f = self.audica.open(moggsongitems[0]).read().decode("utf-8")
        except:
            print(sys.exc_info())

        lines = f.split("\n")
        for line in lines:
            if ".mid" in line:
                song_mid = line.split("\"")[1]
        return song_mid
                
    def load_diff(self, diff_name):
        targets = []
        try:
            f = open(diff_name, 'r')
        except:
            f = diff_name
        try:
            difficulty = json.load(f)
        except:
            difficulty = json.loads(f)

        for cue in difficulty["cues"]:
            targets.append(audica_target(cue, self.tempos))
        return targets

    def load_desc(self, file):
        try:
            f = open(file, 'r')
        except:
            f = file
        try:
            desc = json.load(f)
        except:
            desc = json.loads(f)
        return desc

    def get_tempos_from_midi(self, midi_file):
        pattern = midi.read_midifile(midi_file)
        tick = 0
        tempos = []

        for track in pattern:
            for event in track:
                if type(event) is midi.SetTempoEvent:
                    tick += event.tick
                    tempos.append({
                        "tick": tick,
                        "tempo": event.get_bpm()
                        })
        return tempos

class audica_target():

    def __init__(self, cue, tempos):
        self.tick = cue["tick"]
        self.tickLength = cue["tickLength"]
        self.pitch = cue["pitch"]
        self.velocity = cue["velocity"]
        self.handType = self.get_handtype(cue["handType"])
        self.behavior = self.get_behavior(cue["behavior"])
        self.zOffset = cue.get("zOffset", 0)
        self.gridOffset = (cue["gridOffset"]["x"], cue["gridOffset"]["y"])
        self.tempos = tempos



    def get_behavior(self, enum):
        audica_behaviors = {
            0: "target",
            1: "vertical",
            2: "horizontal",
            3: "sustain",
            4: "chain_start",
            5: "chain_node",
            6: "melee"
        }
        return audica_behaviors.get(enum, "invalid behavior")

    def get_handtype(self, enum):
        audica_handtypes = {
            0: "either",
            1: "right",
            2: "left"
        }
        return audica_handtypes.get(enum, "invalid handtype")

    def behavior_to_cue(self, behavior):
        audica_behaviors = {
            "target": 0,
            "vertical": 1,
            "horizontal": 2,
            "sustain": 3,
            "chain_start": 4,
            "chain_node": 5,
            "melee": 6
        }
        return audica_behaviors.get(behavior, "invalid behavior")

    def handtype_to_cue(self, enum):
        audica_handtypes = {
            "either": 0,
            "right": 1,
            "left": 2
        }
        return audica_handtypes.get(enum, "invalid handtype")

    def getTrueCoordinates(self):
        """Translates Audica coordinates into real x/y coordinates."""
        pitch = self.pitch
        x = pitch % 12
        y = int(pitch / 12)
        trueX = x + self.gridOffset[0]
        trueY = y + self.gridOffset[1]
        return (trueX, trueY)

    def get_delta_time(self):
        tempos = self.tempos
        if len(tempos) > 1:
            tick = self.tick
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
            return self.tick / 480 * tempos[0]

    def get_cue(self):
        cue = {
        "tick": self.tick,
        "tickLength": self.tickLength,
        "pitch": self.pitch,
        "velocity": self.velocity,
        "gridOffset": {
            "x": self.gridOffset[0],
            "y": self.gridOffset[1]
        },
        "zOffset": self.zOffset,
        "handtype": self.behavior_to_cue(self.behavior),
        "behavior": self.handtype_to_cue(self.handType)
        }
        return cue
    
    #invalid use of repr to be fixed later
    def __repr__(self):
        return f"[{self.tick}, {self.handType}, {self.behavior}]"

