import random
from objects import ShortNote, LongNote

class NoteLogic:
    def __init__(self, config):
        self.config = config
        self.spawn_time = 0
        self.base_spawn_interval = config['SPAWN_INTERVAL']
        self.difficulty_timer = 0
        self.current_difficulty = 1
        self.MIN_PADDING = 100  # Minimum distance between notes in pixels
        self.min_spawn_interval = (self.MIN_PADDING / config['NOTE_SPEED']) * 1000
        self.last_spawn_time = {lane: 0 for lane in range(config['NUM_LANES'])}
        
        self.patterns = [
            {'type': 'single', 'weight': 40},
            {'type': 'double', 'weight': 30},
            {'type': 'triple', 'weight': 15},
            {'type': 'long', 'weight': 5},
            {'type': 'burst', 'weight': 10}
        ]

    def get_spawn_interval(self):
        """Dynamically adjust spawn interval based on difficulty"""
        min_interval = 500
        return max(self.base_spawn_interval - (self.current_difficulty * 50), min_interval)

    def update_difficulty(self, current_time):
        """Increase difficulty every 30 seconds"""
        if (current_time - self.difficulty_timer) > 30000:
            self.current_difficulty = min(self.current_difficulty + 1, 10)
            self.difficulty_timer = current_time

    def select_pattern(self):
        """Select pattern with weighted probabilities"""
        total = sum(p['weight'] for p in self.patterns)
        r = random.uniform(0, total)
        upto = 0
        for pattern in self.patterns:
            if upto + pattern['weight'] >= r:
                return pattern
            upto += pattern['weight']
        return self.patterns[0]

    def get_available_lanes(self, current_time, pattern_type, active_notes):
        """Get lanes available for spawning based on last spawn time and active long notes"""
        num_lanes = self.config['NUM_LANES']
        match pattern_type:
            case 'single':
                required = 1
            case 'double':
                required = 2
            case 'triple':
                required = 3
            case 'long' | 'burst':
                required = 1
            case _:
                required = 1

        # Exclude lanes with active long notes
        active_long_note_lanes = {note.lane for note in active_notes if isinstance(note, LongNote) and note.active}

        available = [lane for lane in range(num_lanes) 
                    if (current_time - self.last_spawn_time[lane]) >= self.min_spawn_interval and lane not in active_long_note_lanes]
        
        if len(available) >= required:
            if pattern_type == 'burst':
                return random.sample(available, min(3, len(available)))
            return random.sample(available, required)
        return []

    def generate_notes(self, current_time, active_notes):
        new_notes = []
        self.update_difficulty(current_time)

        if current_time - self.spawn_time >= self.get_spawn_interval():
            pattern = self.select_pattern()
            if lanes := self.get_available_lanes(
                current_time, pattern['type'], active_notes
            ):
                if pattern['type'] == 'burst':
                    for lane in lanes:
                        note = ShortNote(lane)
                        new_notes.append(note)
                        self.last_spawn_time[lane] = current_time
                else:
                    chord_id = random.randint(1000, 9999)
                    for lane in lanes:
                        if pattern['type'] == 'long':
                            length = self.config['NOTE_SPEED'] * (1 + random.random())
                            new_notes.append(LongNote(lane, length))
                        else:
                            note = ShortNote(lane)
                            note.chord_id = chord_id if len(lanes) > 1 else None
                            new_notes.append(note)
                        self.last_spawn_time[lane] = current_time

                self.spawn_time = current_time

        return new_notes