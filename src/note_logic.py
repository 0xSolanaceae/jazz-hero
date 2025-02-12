import random
from objects import ShortNote, LongNote

class NoteLogic:
    def __init__(self, config):
        self.config = config
        self.spawn_time = 0
        self.chord_counter = 0
        
    def generate_notes(self, current_time):
        new_notes = []
        if current_time - self.spawn_time >= self.config['SPAWN_INTERVAL']:
            # 30% chance to spawn a long note, else spawn a chord of short notes
            if random.random() < 0.1:
                lane = random.randint(0, self.config['NUM_LANES'] - 1)
                length = self.config['NOTE_SPEED'] * 0.8
                new_notes.append(LongNote(lane, length))
            else:
                chord_count = random.choices(
                    [1, 2, 3], 
                    weights=[60, 30, 10], 
                    k=1
                )[0]
                self.chord_counter += 1
                lanes_to_spawn = random.sample(
                    range(self.config['NUM_LANES']), 
                    chord_count
                )
                for lane in lanes_to_spawn:
                    note = ShortNote(lane)
                    note.chord_id = self.chord_counter
                    new_notes.append(note)
            self.spawn_time = current_time
        return new_notes