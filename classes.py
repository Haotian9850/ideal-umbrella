class MusicalDirection():
    def __init__(self, staff, **kwargs):
        self.words = kwargs.get("words") 
        self.measure_no = kwargs.get("measure_no")    # TODO deprecate 
        self.staff = staff  

        self.starting_note_identifier = kwargs.get("starting_note_identifier")
        self.ending_note_identifier = kwargs.get("ending_note_identifier")

        self.direction_type = kwargs.get("direction_type")
        self.direction_text = kwargs.get("direction_text")

        self.beat_unit = kwargs.get("beat_unit")
        self.per_minute = kwargs.get("per_minute")
        self.tag_name = kwargs.get("tag_name")
        self.child_tag_name = kwargs.get("child_tag_name")
        self.text = kwargs.get("text")
        self.number = kwargs.get("number")
        self.spread = kwargs.get("spread")
        self.type = kwargs.get("type") 
        self.line_end = kwargs.get("line_end")
        self.line_type = kwargs.get("line_type")
        self.size = kwargs.get("size")
        self.line = kwargs.get("line")

        self.onset_times_trend = None   # TODO remove
        self.dynamics_trend_player = None
        self.dynamics_trend_master = None 
        self.num_notes_analyzed_dynamics = kwargs.get("num_notes_analyzed_dynamics")
        

    def __str__(self):
        attrs = {k : v for k, v in vars(self).items() if v is not None} 
        return f"Direction at {self.starting_note_identifier}: {attrs}"

    def __eq__(self, other):
        if isinstance(other, MusicalDirection):
            return self.words.lower() == other.words.lower() and self.measure_no == other.measure_no 
        return False 

    def __hash__(self):
        return hash("{}-{}".format(self.measure_no, self.words.lower() if self.words else "unknown"))



