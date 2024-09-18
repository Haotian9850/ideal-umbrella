import xml.etree.ElementTree as ET
import logging
from collections import OrderedDict

from enum import Enum
import time

import sys 
sys.path.append("../")

from utils.Utils import Utils
from utils.extract_musical_directions import build_note_identifier_directions_map


logger = logging.getLogger("main")

class ArticulationMarkings(Enum):
    STACCATO = "STACCATO"
    STACCATISSIMO = "STACCATISSIMO"
    PORTATO = "PORTATO"
    ACCENT = "ACCENT"
    MARCATO = "MARCATO"
    TENUTO = "TENUTO"


class MusicalDirectionWords(Enum):
    TEMPO_DIRECTIONS = {
        "più mosso", "Allegro", "poco a poco ritardando", "Sostenuto", "poco a poco piu agitato ", "Andante sostenuto", "poco agitato", "più animato con passione", "poco cresc.", "poco cresc. ed agitato", "poco rallentando", "Un poco più mosso", "dim. e rallent.", "sempre più piano, rallentando", "Vivo", "cresc. ed accel.", "poco riten", "accelerando", "poco a poco ritenuto", "Un poco meno mosso", "agitato con appassionato", "Andante ", "Tempo I°", "Tempo rubato", "Più lento ", "Poco moto", "Allegro con fuoco ", "Presto ", "velocissimo", "poco accelerando", "poco rubato", "Poco meno mosso", "Adagio", "Animato", "cresc. ed accel.", "Andante quasi recitativo", "Andante con moto", "più mosso", "Allegro vivace. ", "rall...", "riten.", "sempre più f", "poco a poco crescendo", "Un poco mosso", "Presto", "accel poco a poco", "più cresc.", "dim. e rall.", "Larghetto ", "Tempo primo", "più smorz. e rit.", "allargando", "Più vivo", "Lento, ma non troppo ", "Più mosso.", "poco più animato", "Calmato", "poco a poco ritard.", "Agitato", "a tempo", "poco a poco cresc.", "con fuoco", "Allegro agitato ", "M. M. ", "cresc.ed accel. poco a poco", "Allegro assai", "più allegro", "Andantino", "Vivace con brio", "Allegretto", "Lento sostenuto", "allegro", "allegro molto", "andante", "adagio", "presto", "largo", "vivace", "grave", "moderato", "accelerando", "accel.", "ritardando", "rit.", "a tempo", "lento", "ritenuto", "riten.", "meno mosso", "allegretto", "presto con fuoco", "maestoso", "prestissimo", "poco rit.", "meno mosso", "poco riten.", "molto vivace"
    }

    TEMPO_DIRECTIONS_TREND = {
        "più mosso", "poco a poco ritardando", "poco a poco piu agitato ", "più animato con passione", "poco cresc.", "poco cresc. ed agitato", "poco rallentando", "Un poco più mosso", "dim. e rallent.", "sempre più piano, rallentando", "cresc. ed accel.", "poco riten", "accelerando", "poco a poco ritenuto", "Un poco meno mosso", "poco accelerando", "cresc. ed accel.", "rall...", "riten.", "poco a poco crescendo", "accel poco a poco", "più cresc.", "dim. e rall.", "più smorz. e rit.", "poco a poco ritard.", "poco a poco cresc.", "cresc.ed accel. poco a poco", "accelerando", "accel.", "ritardando", "rit.", "ritenuto", "riten.", "poco rit.", "poco riten."
    }

    DYNAMICS_DIRECTIONS = {
        "dim.", "poco cresc.", "poco cresc. ed agitato", "dim. e rallent.", "sempre più piano, rallentando", "f cresc.", "poco riten", "rinforzando", "poco a poco decrescendo", "p cresc.", "poco diminuendo", "pp e rall.", "crescendo", "dim. ed allarg.", "poco a poco crescendo", "poco dim.", "poco a poco accel. al tempo primo", "cresc. ed accel.", "poco dim.", "p", "poco a poco cresc.", "pp leggiero", "poco a poco ritard.", "poco a poco diminuendo", "pp e poco ritenuto", "cresc. e stretto", "sempre più f", "più f", "più crescendo.", "poco rinforzando", "p", "più rinforzando", "sempre più forte", "poco a poco ritard.", "poco a poco cresc.", "poco", "poco calando", "sempre pianissimo e senza sordini", "pp smorz.", "poco a poco ritard.", "forte","piano", "fortissimo", "pianissimo", "crescendo", "cresc.", "decrescendo", "decresc.", "mezzo-forte", "mezzo-piano", "pesante", "diminuendo", "dim.", "con forza", "ten.", "tenuto", "sotto voce", "il piu forte possible", "mezza voce", "più cresc.", "molto cresc.", "poco a poco cresc", "pfz", "smorzando", "sempreff", "ffz", "f", "ff", "mp", "sf", "sff", "fp", "sfp", "sfff", "fff", "pp", "sempre cresc.", "poco a poco più tranquillo"
    }

    DYNAMIC_DIRECTIONS_TREND = {
        "dim.", "poco cresc.", "poco cresc. ed agitato", "dim. e rallent.", "sempre più piano", "rallentando", "f cresc.", "poco riten", "rinforzando", "poco a poco decrescendo", "poco rallentando", "poco accelerando", "p cresc.", "poco diminuendo", "pp e rall.", "crescendo", "dim. ed allarg.", "poco a poco crescendo", "poco dim.", "poco a poco accel. al tempo primo", "cresc. ed accel.", "poco dim.", "poco a poco cresc.", "poco a poco ritard.", "poco a poco diminuendo", "cresc. e stretto", "sempre più f", "più crescendo.", "poco rinforzando", "più rinforzando", "sempre più forte", "poco a poco ritard.", "poco a poco cresc.", "poco calando", "sempre pianissimo e senza sordini", "pp smorz.", "poco a poco ritard.", "crescendo", "cresc.", "decrescendo", "decresc.", "diminuendo", "dim.", "con forza", "ten.", "tenuto", "più cresc.", "molto cresc.", "poco a poco cresc", "sempre cresc.", "poco a poco più tranquillo", "sempre più dim.", "sempre più piano"
    }

    ARTICULATION_DIRECTIONS = {"dol. e legato", "dol.", "dolce", "grazioso", "leggieriss", "leggierissimo", "moderato cantabile", "il canto marcato", "poco a poco più tranquillo"}


class SubsegmentTypes(Enum):
    PHRASE = "phrase"
    ACCENTED_MELODY = "accented_melody"
    HIDDEN_MELODY = "hidden_melody"
    MUSICAL_DIRECTION = "musical_direction"


class SectionComparisonMethods():
    def __init__(self, **kwargs):
        self.metric = kwargs.get("metric")
        self.comparison_type = kwargs.get("comparison_type")

    def __str__(self):
        return f"SectionComparisonMethods(metric={self.metric}, comparison_type={self.comparison_type})"

class SectionComparisonMetrics(Enum):
    NOTE_DURATION = "note_duration"
    ONSET_VELOCITY = "onset_velocity"
    ONSET_TIME = "onset_time"
    MEASURE_DURATION = "measure_duration"


# TODO think more on the types of comparison. Need to be completely metric agnostic here
class SectionComparisonTypes(Enum):
    PEARSON_CORR = "pearson_corr"   # pearson correlation between player and master
    RATIO_AVG_BEFORE_AND_AFTER = "ratio_avg_before_and_after"   # ratio of average value before and after the section between player and master
    RATIO_TREND = "ratio_trend"   # player & master ratio of trends
    RATIO_MEASURE_DURATION = "ratio_measure_duration"

    # TODO figure out what's more??



class MusicalDirectionTypes(Enum):
    TEMPO = "tempo"
    DYNAMICS = "dynamics"
    ARTICULATION = "articulation"


class PromptTemplate():
    def __init__(self, **kwargs):
        # for musical direction comparison sections
        self.good_prompt_template = kwargs.get("good_prompt_template")
        self.bad_prompt_template = kwargs.get("bad_prompt_template")

        # for more complicated comparison sections (phrases, melodies, etc.)
        # TODO think about what to do here

        self.info_prompt = kwargs.get("info_prompt")    # information only, doesn't contain any metric

    def __str__(self):
        return f"PromptTemplate: {str({k : v for k, v in vars(self).items() if v is not None})}"


# TODO add a single-section comparison class (as opposed to before-and-after comparison). Example usecase: wedge
class SingleComparisonSection():
    def __init__(self, **kwargs):
        self.start_note_id = kwargs.get("start_note_id")
        self.end_note_id = kwargs.get("end_note_id")
        self.start_measure = kwargs.get("start_measure")
        self.end_measure = kwargs.get("end_measure")

        self.voice = kwargs.get("voice")

        self.comparison_methods = kwargs.get("comparison_methods", [])  # list of SectionComparisonMethods objects
        self.staff = kwargs.get("staff")

        self.musical_direction = kwargs.get("musical_direction")    # one musical direction per one before and after comparison section

        self.note_ids = kwargs.get("note_ids")
        self.prompt_template = kwargs.get("prompt_template")

        self.is_global = kwargs.get("is_global")
        self.custom_prompt_function = kwargs.get("custom_prompt_function")


    def __str__(self):
        return f"SingleComparisonSection: {str({k : v for k, v in vars(self).items() if v is not None})}, musical direction {str(self.musical_direction)}, comparison methods {', '.join([str(m) for m in self.comparison_methods])}, prompt template {str(self.prompt_template)}"

# TODO generate prompt template
class BeforeAndAfterComparisonSection():
    def __init__(self, **kwargs):
        self.before_start_note_id = kwargs.get("before_start_note_id")
        self.before_end_note_id = kwargs.get("before_end_note_id")
        self.after_start_note_id = kwargs.get("after_start_note_id")
        self.after_end_note_id = kwargs.get("after_end_note_id")

        # alternatively
        self.before_start_measure = kwargs.get("before_start_measure")
        self.before_end_measure = kwargs.get("before_end_measure")
        self.after_start_measure = kwargs.get("after_start_measure")
        self.after_end_measure = kwargs.get("after_end_measure")

        self.musical_direction = kwargs.get("musical_direction")    # one musical direction per one before and after comparison section
        self.voice = kwargs.get("voice")
        self.comparison_methods = kwargs.get("comparison_methods", [])  # list of SectionComparisonMethods objects
        self.staff = kwargs.get("staff")

        self.before_note_ids = kwargs.get("before_note_ids", [])
        self.after_note_ids = kwargs.get("after_note_ids", [])

        self.is_initial_tempo_marking = kwargs.get("is_initial_tempo_marking")
        self.prompt_template = kwargs.get("prompt_template")
   
    def __str__(self):
        return f"BeforeAndAfterComparisonSection: {str({k : v for k, v in vars(self).items() if v is not None})}, musical direction {str(self.musical_direction)}), comparison methods {', '.join([str(m) for m in self.comparison_methods])}, prompt template {str(self.prompt_template)}"


class SubsegmentForComparison:
    def __init__(self, **kwargs):
        self.start_note_id = kwargs.get("start_note_id")
        self.end_note_id = kwargs.get("end_note_id")
        self.start_measure = kwargs.get("start_measure")
        self.end_measure = kwargs.get("end_measure")

        self.note_ids = kwargs.get("note_ids")  # mutually exclusive with start / end note ids
        self.subsegment_type = kwargs.get("subsegment_type")   # phrase | melody | hidden melody?

        self.musical_directions = kwargs.get("musical_directions")
        self.musical_direction_type = kwargs.get("musical_direction_type")  # tempo | dynamics | articulation

        self.staff = kwargs.get("staff")
        self.voice = kwargs.get("voice")

        self.before_n_after_comparison_sections = kwargs.get("before_and_after_comparison_sections", [])
        self.single_comparison_sections = kwargs.get("single_comparison_sections", [])

   
    def sort_before_n_after_comparison_sections(self):
        """
        Sort the before_and_after_comparison_sections list by the start_note_id of the before section.
        """
        self.before_n_after_comparison_sections.sort(key=lambda x: (int(x.before_start_note_id.split("-")[1]), int(x.before_start_note_id.split("-")[2])))

    def sort_single_comparison_sections(self):
        """
        Sort the single_comparison_sections list by the start_note_id.
        """
        self.single_comparison_sections.sort(key=lambda x: (int(x.start_note_id.split("-")[1]), int(x.start_note_id.split("-")[2])))


    def __eq__(self, other) -> bool:
        if not isinstance(other, SubsegmentForComparison):
            return NotImplemented
       
        return (
            self.start_note_id == other.start_note_id and
            self.end_note_id == other.end_note_id and
            self.start_measure == other.start_measure and
            self.end_measure == other.end_measure and
            set(self.note_ids) == set(other.note_ids) and
            self.subsegment_type == other.subsegment_type and
            self.musical_direction_type == other.musical_direction_type and
            self.staff == other.staff and
            self.voice == other.voice
        )
       

    def __str__(self):
        return f"SubsegmentForComparison: {str(vars(self))}"

class ArticulationDetails():
    def __init__(self, **kwargs):
        self.note_id = kwargs.get("note_id")
        self.is_slurred = kwargs.get("is_under_slur")   # legato articulation?
        self.articulation_marking = kwargs.get("articulation_marking")
        self.staff = kwargs.get("staff")

    def __str__(self):
        return str(vars(self))
   
class ScoreDetails():
    def __init__(self, **kwargs):
        self.score_id = kwargs.get("score_id")
        self.unnested_note_identifier_directions_map = kwargs.get("unnested_note_identifier_directions_map")
        self.unnested_measure_no_articulation_details_map = kwargs.get("measure_no_articulation_details_map")
       
        self.subsegments_for_comparison = kwargs.get("subsegments_for_comparison")


# TODO build localized prompt template for a given comparison section based on subsegment
def build_prompt_template(comparison_section, subsegment:SubsegmentForComparison):

    direction = comparison_section.musical_direction

    if direction:
        start_measure = int(direction.starting_note_identifier.split("-")[1])
        end_measure = int(direction.ending_note_identifier.split("-")[1]) if direction.ending_note_identifier else None

        # music direction-based prompts
        if subsegment.musical_direction_type == MusicalDirectionTypes.TEMPO.value and isinstance(comparison_section, BeforeAndAfterComparisonSection) and comparison_section.is_initial_tempo_marking:
            comparison_section.prompt_template = PromptTemplate(
                info_prompt=f"The initial tempo marking for this score is {comparison_section.musical_direction.text}"
            )

        elif subsegment.musical_direction_type == MusicalDirectionTypes.TEMPO.value:
            # search in the subsegment for surrounding tempo direction
            if len(subsegment.musical_directions) == 1:
                if direction.text in MusicalDirectionWords.TEMPO_DIRECTIONS_TREND.value:
                    comparison_section.prompt_template = PromptTemplate(
                        good_prompt_template=f"The tempo marking '{direction.text}' in measure {start_measure} is accurately followed",
                        bad_prompt_template=f"The tempo marking '{direction.text}' in measure {start_measure} needs improvement"
                    )

                else:
                    # not a trend tempo direction, so it is more of a sudden transition
                    comparison_section.prompt_template = PromptTemplate(
                        good_prompt_template = f"The tempo transition to '{direction.text}' in measure {start_measure} is accurately followed",
                        bad_prompt_template=f"The tempo transition to '{direction.text}' in measure {start_measure} needs improvement"
                    )

            else:
                i = subsegment.musical_directions.index(direction)
                if i >= 1:
                    # there is another tempo direction before it
                    prev_tempo_direction = subsegment.musical_directions[i - 1]
                    prev_tempo_measure = prev_tempo_direction.starting_note_identifier.split("-")[1]

                    comparison_section.prompt_template = PromptTemplate(
                        good_prompt_template=f"The tempo transition to '{direction.text}' in measure {start_measure} following the previous '{prev_tempo_direction.text}' in measure {prev_tempo_measure} is accurately followed",
                        bad_prompt_template=f"The tempo transition to '{direction.text}' in measure {start_measure} following the previous '{prev_tempo_direction.text}' in measure {prev_tempo_measure} needs improvement"
                    )

                else:
                    # there is another tempo direction after it
                    next_tempo_direction = subsegment.musical_directions[i + 1]
                    next_tempo_measure = next_tempo_direction.starting_note_identifier.split("-")[1]
                    comparison_section.prompt_template = PromptTemplate(
                        good_prompt_template=f"The tempo transition to '{direction.text}' in measure {start_measure} before the '{next_tempo_direction.text}' in measure {next_tempo_measure} is accurately followed",
                        bad_prompt_template=f"The tempo transition to '{direction.text}' in measure {start_measure} before the '{next_tempo_direction.text}' in measure {next_tempo_measure} needs improvement"
                    )

        elif subsegment.musical_direction_type == MusicalDirectionTypes.DYNAMICS.value:
            if len(subsegment.musical_directions) == 1:
                # only direction in the segment
                if direction.tag_name == "dynamics":
                    comparison_section.prompt_template = PromptTemplate(
                        good_prompt_template=f"The dynamics transition to '{direction.child_tag_name}' in measure {start_measure} is accurately followed",
                        bad_prompt_template=f"The dynamics transition to '{direction.child_tag_name}' in measure {start_measure} needs improvement"
                    )

                elif direction.tag_name == "wedge":
                    if end_measure and end_measure > start_measure:
                        comparison_section.prompt_template = PromptTemplate(
                            good_prompt_template=f"The {direction.type} from measure {start_measure} to {end_measure} is accurately followed",
                            bad_prompt_template=f"The {direction.type} from measure {start_measure} to {end_measure} needs improvement"
                        )
                    else:
                        comparison_section.prompt_template = PromptTemplate(
                            good_prompt_template=f"The {direction.type} in measure {start_measure} is accurately followed",
                            bad_prompt_template=f"The {direction.type} in measure {start_measure} needs improvement"
                        )
               
                elif direction.tag_name == "words":
                    if direction.text in MusicalDirectionWords.DYNAMIC_DIRECTIONS_TREND.value:
                        comparison_section.prompt_template = PromptTemplate(
                            good_prompt_template=f"The dynamics direction '{direction.text}' in measure {start_measure} is accurately followed",
                            bad_prompt_template=f"The dynamics direction '{direction.text}' in measure {start_measure} needs improvement"
                        )

                    else:
                        comparison_section.prompt_template = PromptTemplate(
                            good_prompt_template=f"The dynamics transition to '{direction.text}' in measure {start_measure} is accurately followed",
                            bad_prompt_template=f"The dynamics transition to '{direction.text}' in measure {start_measure} needs improvement"
                        )

            else:
                i = subsegment.musical_directions.index(direction)
                if i >= 1:
                    prev_dynamics_direction = subsegment.musical_directions[i - 1]
                    prev_dynamics_measure = int(prev_dynamics_direction.starting_note_identifier.split("-")[1])

                    if direction.tag_name == "wedge":
                        if prev_dynamics_direction.tag_name == "dynamics":
                            # p / pp / f / ff => wedge
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The {direction.type} from measure {start_measure} to {end_measure} from the '{prev_dynamics_direction.child_tag_name}' in measure {prev_dynamics_measure} is accurately followed",
                                bad_prompt_template=f"The {direction.type} from measure {start_measure} to {end_measure} from the '{prev_dynamics_direction.child_tag_name}' in measure {prev_dynamics_measure} is needs improvement"
                            )
                       
                        elif prev_dynamics_direction.tag_name == "wedge":
                            # wedge => wedge
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The {direction.type} in measure {start_measure} following the previous {prev_dynamics_direction.type} in measure {prev_dynamics_measure} is accurately followed",
                                bad_prompt_template=f"The {direction.type} in measure {start_measure} following the previous {prev_dynamics_direction.type} in measure {prev_dynamics_measure} needs improvement"
                            )

                        elif prev_dynamics_direction.tag_name == "words":
                            # word => wedge. This may not be very common
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The {direction.type} in measure {start_measure} following the previous {prev_dynamics_direction.text} in measure {prev_dynamics_measure} is accurately followed",
                                bad_prompt_template=f"The {direction.type} in measure {start_measure} following the previous {prev_dynamics_direction.text} in measure {prev_dynamics_measure} needs improvement"
                            )

                    elif direction.tag_name == "dynamics":
                        if prev_dynamics_direction.tag_name == "wedge":
                            # wedge => p / pp / f / ff
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The dynamics transition to {direction.child_tag_name} in measure {start_measure} from the previous {prev_dynamics_direction.type} in measure {prev_dynamics_measure} is accurately followed",
                                bad_prompt_template=f"The dynamics transition to {direction.child_tag_name} in measure {start_measure} from the previous {prev_dynamics_direction.type} in measure {prev_dynamics_measure} needs improvement"
                            )

                        elif prev_dynamics_direction.tag_name == "dynamics":
                            # p / pp / f / ff => p / pp / f / ff
                            if prev_dynamics_direction.child_tag_name == direction.child_tag_name:
                                if prev_dynamics_measure == start_measure:
                                    comparison_section.prompt_template = PromptTemplate(
                                        good_prompt_template=f"The dynamics stay at '{direction.child_tag_name}' in measure {start_measure} is accurately followed",
                                        bad_prompt_template=f"The dynamics stay at '{direction.child_tag_name}' in measure {start_measure} needs improvement"
                                    )
                                else:
                                    comparison_section.prompt_template = PromptTemplate(
                                        good_prompt_template=f"The dynamics stay at '{direction.child_tag_name}' from measure {prev_dynamics_measure} to {start_measure} is accurately followed",
                                        bad_prompt_template=f"The dynamics stay at '{direction.child_tag_name}' from measure {prev_dynamics_measure} to {start_measure} needs improvement"
                                    )

                            else:
                                comparison_section.prompt_template = PromptTemplate(
                                    good_prompt_template=f"The dynamics transition from the '{prev_dynamics_direction.child_tag_name}' in measure {prev_dynamics_measure} to the '{direction.child_tag_name}' in measure {start_measure} is accurately followed",
                                    bad_prompt_template=f"The dynamics transition from the '{prev_dynamics_direction.child_tag_name}' in measure {prev_dynamics_measure} to the '{direction.child_tag_name}' in measure {start_measure} needs improvement"
                                )

                        elif prev_dynamics_direction.tag_name == "words":
                            # word =>  p / pp / f / ff
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The dynamics transition to {direction.child_tag_name} in measure {start_measure} following the previous {prev_dynamics_direction.text} in measure {prev_dynamics_measure} is accurately followed",
                                bad_prompt_template=f"The dynamics transition to {direction.child_tag_name} in measure {start_measure} following the previous {prev_dynamics_direction.text} in measure {prev_dynamics_measure} needs improvement"
                            )

                else:
                    next_dynamics_direction = subsegment.musical_directions[i + 1]
                    next_dynamics_measure = next_dynamics_direction.starting_note_identifier.split("-")[1]
                    if direction.tag_name == "wedge":
                        if next_dynamics_direction.tag_name == "wedge":
                            # wedge => wedge. This one is the same as just one wedge
                            if end_measure and end_measure > start_measure:
                                comparison_section.prompt_template = PromptTemplate(
                                    good_prompt_template=f"The {direction.type} from measure {start_measure} to {end_measure} is accurately followed",
                                    bad_prompt_template=f"The {direction.type} from measure {start_measure} to {end_measure} needs improvement"
                                )
                            else:
                                comparison_section.prompt_template = PromptTemplate(
                                    good_prompt_template=f"The {direction.type} in measure {start_measure} is accurately followed",
                                    bad_prompt_template=f"The {direction.type} in measure {start_measure} needs improvement"
                                )

                        elif next_dynamics_direction.tag_name == "dynamics":
                            # wedge => p / pp / f / ff
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The {direction.type} in measure {start_measure} leading to {next_dynamics_direction.child_tag_name} is accurately followed",
                                bad_prompt_template=f"The {direction.type} in measure {start_measure} leading to {next_dynamics_direction.child_tag_name} needs improvement"
                            )

                        elif next_dynamics_direction.tag_name == "words":
                            # wedge => word
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The {direction.type} in measure {start_measure} leading to the '{next_dynamics_direction.text}' direction is accurately followed",
                                bad_prompt_template=f"The {direction.type} in measure {start_measure} leading to the '{next_dynamics_direction.text}' direction needs improvement"
                            )

                    elif direction.tag_name == "dynamics":
                        if next_dynamics_direction.tag_name == "wedge":
                            # p / pp / f / ff => wedge
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The '{direction.child_tag_name}' in measure {start_measure} leading to the {next_dynamics_direction.type} in measure {next_dynamics_measure} is accurately followed",
                                bad_prompt_template=f"The '{direction.child_tag_name}' in measure {start_measure} leading to the {next_dynamics_direction.type} in measure {next_dynamics_measure} needs improvement"
                            )
                       
                        elif next_dynamics_direction.tag_name == "dynamics":
                            # p / pp / f / ff => p / pp / f / ff. This one is the same as just one direction
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The '{direction.child_tag_name}' direction in measure {start_measure} is accurately followed",
                                bad_prompt_template=f"The '{direction.child_tag_name}' direction in measure {start_measure} needs improvement"
                            )

                        elif next_dynamics_direction.tag_name == "words":
                            # p / pp / f / ff => words
                            comparison_section.prompt_template = PromptTemplate(
                                good_prompt_template=f"The '{direction.child_tag_name}' direction in measure {start_measure} leading to the {next_dynamics_direction.text} in measure {next_dynamics_measure} is accurately followed",
                                bad_prompt_template=f"The '{direction.child_tag_name}' direction in measure {start_measure} leading to the {next_dynamics_direction.text} in measure {next_dynamics_measure} needs improvement"
                            )

                    elif direction.tag_name == "words":
                        # words dynamics directions are always treated as just one direction
                        comparison_section.prompt_template = PromptTemplate(
                            good_prompt_template=f"The '{direction.text}' direction in measure {start_measure} is accurately followed",
                            bad_prompt_template=f"The '{direction.text}' direction in measure {start_measure} needs improvement"
                        )

        elif subsegment.musical_direction_type == MusicalDirectionTypes.ARTICULATION.value:
            # TODO think about what to do here
            # all articulation directions are treated independently
            comparison_section.prompt_template = PromptTemplate(
                good_prompt_template=f"The transition to '{direction.text}' in measure {start_measure} is accurately followed",
                bad_prompt_template=f"The transition to '{direction.text}' in measure {start_measure} needs improvement"
            )

    else:
        # TODO figure out what to do here
        if subsegment.subsegment_type == SubsegmentTypes.PHRASE.value:
            # TODO more complicated prompt template required for phrase - from tempo and dynamics, should be dependent on the metrics
            comparison_section.prompt_template = PromptTemplate(
                good_prompt_template=None,
                bad_prompt_template=None
            )
       
        elif subsegment.subsegment_type == SubsegmentTypes.ACCENTED_MELODY.value:
           
            start_measure = comparison_section.note_ids[0].split("-")[1]
            end_measure = comparison_section.note_ids[-1].split("-")[1]

            comparison_section.prompt_template = PromptTemplate(
                good_prompt_template=f"The accented melody from measure {start_measure} to {end_measure} is accurately articulated",
                bad_prompt_template=f"The articulation of the accented melody from measure {start_measure} to {end_measure} needs improvement"
            )


def get_global_subsegments_for_comparison():
    # for now, only global tempo comparison is needed
    return [
        SubsegmentForComparison(
            start_measure=None,
            end_measure=None,
            single_comparison_sections=[
                SingleComparisonSection(
                    start_measure=None,
                    end_measure=None,
                    is_global=True,
                    custom_prompt_function="GLOBAL_TEMPO_ANALYSIS", # TODO implement this function and put it with any other future custom prompt template functions
                    comparison_methods=[
                        SectionComparisonMethods(
                            metric=SectionComparisonMetrics.ONSET_TIME.value,
                            comparison_type=SectionComparisonTypes.RATIO_MEASURE_DURATION.value
                        )
                    ]
                )
            ]
        )
    ]


def build_score_details(unnested_score_xml_tree, score_id:str)->ScoreDetails:

    xml_tree = unnested_score_xml_tree

    first_measure, last_measure = Utils.get_first_last_measure(xml_tree)

    result = ScoreDetails(score_id=score_id)
    result.unnested_measure_no_articulation_details_map = build_unnested_measure_no_articulation_details_map(xml_tree=xml_tree)

    note_identifier_directions_map = build_note_identifier_directions_map(xml_tree=xml_tree)

    for note_identifier, directions in note_identifier_directions_map.items():
        print(f"note_identifier: {note_identifier}")
        for direction in directions:
            print(str(direction))


    for note_identifier, directions in note_identifier_directions_map.items():
        logger.debug(f"note_identifier: {note_identifier}")

        # remove pedal and octave shift directions for now
        note_identifier_directions_map[note_identifier] = list(set([d for d in directions if d.tag_name != "pedal" and d.tag_name != "octave_shift"]))
       

    result.unnested_note_identifier_directions_map = note_identifier_directions_map
       
    # find out regions where onset velocity needs to be analyzed
    measure_no_dynamics_directions_map = OrderedDict()

    measure_no_tempo_directions_map = OrderedDict()
    measure_no_articulation_directions_map = OrderedDict()

    for note_identifier, directions in result.unnested_note_identifier_directions_map.items():
        for direction in directions:
            if direction.tag_name == "dynamics":
                m = int(direction.starting_note_identifier.split("-")[1])
                if m not in measure_no_dynamics_directions_map.keys():
                    measure_no_dynamics_directions_map[m] = [direction]
                else:
                    measure_no_dynamics_directions_map[m].append(direction)

            if direction.tag_name == "wedge":

                start_measure = int(direction.starting_note_identifier.split("-")[1])
                end_measure = int(direction.ending_note_identifier.split("-")[1])

                for m in range(start_measure, end_measure + 1):
                    if m not in measure_no_dynamics_directions_map.keys():
                        measure_no_dynamics_directions_map[m] = [ direction ]
                    else:
                        measure_no_dynamics_directions_map[m].append(direction)

            if direction.tag_name == "words" and direction.text and direction.text.lower() in MusicalDirectionWords.DYNAMICS_DIRECTIONS.value:

                m = int(direction.starting_note_identifier.split("-")[1])

                if m not in measure_no_dynamics_directions_map.keys():
                    measure_no_dynamics_directions_map[m] = [direction]
                else:
                    measure_no_dynamics_directions_map[m].append(direction)

            if direction.tag_name == "words" and direction.text and direction.text.lower() in MusicalDirectionWords.TEMPO_DIRECTIONS.value:

                m = int(direction.starting_note_identifier.split("-")[1])

                if m not in measure_no_tempo_directions_map.keys():
                    measure_no_tempo_directions_map[m] = [direction]
                else:
                    measure_no_tempo_directions_map[m].append(direction)

            if direction.tag_name == "words" and direction.text and direction.text.lower() in MusicalDirectionWords.ARTICULATION_DIRECTIONS.value:
                m = int(direction.starting_note_identifier.split("-")[1])
                if m not in measure_no_articulation_directions_map.keys():
                    measure_no_articulation_directions_map[m] = [direction]
                else:
                    measure_no_articulation_directions_map[m].append(direction)

   
    # find consecutive sequences in measures with dynamics directions
    dynamics_sections = Utils.search_for_consecutive_sequences(sorted(measure_no_dynamics_directions_map.keys()), min_squence_size=1, max_gap=1)
   
    subsegments_for_comparison = []

    # for each section, try to include measure before and after it TODO handle first / last measure
    for section in dynamics_sections:
        expanded_start = section[0] - 1 if section[0] > first_measure else first_measure
        expanded_end = section[-1] + 1 if section[-1] < last_measure else last_measure

        s = SubsegmentForComparison(
            start_measure=expanded_start,
            end_measure=expanded_end,
            subsegment_type=SubsegmentTypes.MUSICAL_DIRECTION.value,
            musical_direction_type=MusicalDirectionTypes.DYNAMICS.value,
            voice=1
        )
        subsegments_for_comparison.append(s)  
               

    # include +/-2 measures for each tempo direction
    tempo_sections = Utils.search_for_consecutive_sequences(sorted(measure_no_tempo_directions_map.keys()), min_squence_size=1, max_gap=2)

    for section in tempo_sections:
        expanded_start = section[0] - 2 if section[0] > first_measure else first_measure
        expanded_end = section[-1] + 2 if section[-1] < last_measure else last_measure

        s = SubsegmentForComparison(
            start_measure=expanded_start,
            end_measure=expanded_end,
            subsegment_type=SubsegmentTypes.MUSICAL_DIRECTION.value,
            musical_direction_type=MusicalDirectionTypes.TEMPO.value,
            voice=1
        )
        subsegments_for_comparison.append(s)

    articulation_sections = Utils.search_for_consecutive_sequences(sorted(measure_no_articulation_directions_map.keys()), min_squence_size=1, max_gap=2)
    for section in articulation_sections:
        expanded_start = section[0] - 2 if section[0] > first_measure else first_measure
        expanded_end = section[-1] + 2 if section[-1] < last_measure else last_measure

        s = SubsegmentForComparison(
            start_measure=expanded_start,
            end_measure=expanded_end,
            subsegment_type=SubsegmentTypes.MUSICAL_DIRECTION.value,
            musical_direction_type=MusicalDirectionTypes.ARTICULATION.value,
            voice=1
        )
        subsegments_for_comparison.append(s)

    # collect all musical directions
    for subsegment in subsegments_for_comparison:

        if subsegment.subsegment_type != SubsegmentTypes.MUSICAL_DIRECTION.value:
            continue

        start_measure = subsegment.start_measure
        end_measure = subsegment.end_measure
        subsegment.musical_directions = []

        print(str(subsegment))

        for m in range(start_measure, end_measure + 1):
            if subsegment.musical_direction_type == MusicalDirectionTypes.DYNAMICS.value and m in measure_no_dynamics_directions_map:
                subsegment.musical_directions.extend(measure_no_dynamics_directions_map[m])
           
            if subsegment.musical_direction_type == MusicalDirectionTypes.TEMPO.value and m in measure_no_tempo_directions_map:
                subsegment.musical_directions.extend(measure_no_tempo_directions_map[m])
           
            if subsegment.musical_direction_type == MusicalDirectionTypes.ARTICULATION.value and m in measure_no_articulation_directions_map:
                subsegment.musical_directions.extend(measure_no_articulation_directions_map[m])

        subsegment.musical_directions = sorted(list(set((subsegment.musical_directions))), key=lambda d : int(d.starting_note_identifier.split("_")[1]))


    top_voice_right_hand_note_ids = Utils.filter_notes(xml_tree, "1", "1", is_chord=False)
    top_voice_left_hand_note_ids = Utils.filter_notes(xml_tree, "1", "2", is_chord=False)
    note_no_note_id_map, note_id_note_no_map = Utils.build_note_no_note_id_maps(xml_tree)


    # guess phrase from multi-measure slurs
    top_voice_slur_note_segments = segment_by_slurs(xml_tree, "1", "1")
    predicted_phrases_top_voice_note_ids = []

    for slur_segment in top_voice_slur_note_segments:
        measures = set()
        for note_id in slur_segment:
            measure_no = int(note_id.split("-")[1])
            measures.add(measure_no)

        if len(measures) >= 2:
            predicted_phrases_top_voice_note_ids.append(slur_segment)
            s = SubsegmentForComparison(
                start_measure=min(measures),
                end_measure=max(measures),
                note_ids=slur_segment,
                subsegment_type=SubsegmentTypes.PHRASE.value,
                voice=1,
                single_comparison_sections=[
                    SingleComparisonSection(
                        start_note_id=slur_segment[0],
                        end_note_id=slur_segment[-1],
                        staff="1",  # only top voice slurs are extracted
                        note_ids=Utils.find_between_note_ids(
                            start_note_id=slur_segment[0],
                            end_note_id=slur_segment[-1],
                            from_note_ids=top_voice_right_hand_note_ids,
                            note_id_note_no_map=note_id_note_no_map
                        ),
                        comparison_methods=[
                            SectionComparisonMethods(
                                metric=SectionComparisonMetrics.ONSET_VELOCITY.value,
                                comparison_type=SectionComparisonTypes.RATIO_TREND.value
                            ),
                            SectionComparisonMethods(
                                metric=SectionComparisonMetrics.ONSET_TIME.value,
                                comparison_type=SectionComparisonTypes.RATIO_TREND.value
                            )
                        ]
                    )
                ]
            )
            subsegments_for_comparison.append(s)

    subsegments_for_comparison = sorted(subsegments_for_comparison, key=lambda s: (s.start_measure, s.end_measure))

    # guess melodies from accented notes
    # identify accented note IDs
    measures_w_accented_notes = set()
    for measure_no, articulation_details in result.unnested_measure_no_articulation_details_map.items():
        for articulation_detail in articulation_details:
            if articulation_detail.articulation_marking == ArticulationMarkings.ACCENT.value:
                measures_w_accented_notes.add(int(measure_no))

    accented_notes_sections = Utils.search_for_consecutive_sequences(sorted(list(measures_w_accented_notes)), min_squence_size=2, max_gap=0)

    print(f"accented_notes_sections: {accented_notes_sections}, measures_w_accented_notes {sorted(list(measures_w_accented_notes))}")

    for section in accented_notes_sections:

        note_ids = list()

        for measure in section:
            if result.unnested_measure_no_articulation_details_map.get(str(measure)):
                accented_note_ids = [n.note_id for n in result.unnested_measure_no_articulation_details_map[str(measure)] if n.articulation_marking == ArticulationMarkings.ACCENT.value]
                note_ids.extend(accented_note_ids)
       
        s = SubsegmentForComparison(
            start_measure=section[0],
            end_measure=section[-1],
            subsegment_type=SubsegmentTypes.ACCENTED_MELODY.value,
            voice=1,
            note_ids=note_ids,
            single_comparison_sections=[
                SingleComparisonSection(
                    start_note_id=note_ids[0],
                    end_note_id=note_ids[-1],
                    staff="1",
                    note_ids=note_ids,
                    comparison_methods=[
                        SectionComparisonMethods(
                            metric=SectionComparisonMetrics.ONSET_VELOCITY.value,
                            comparison_type=SectionComparisonTypes.PEARSON_CORR.value
                        )
                    ]
                )
            ]
        )
        subsegments_for_comparison.append(s)

    print(f"top_voice_right_hand_note_ids: {len(top_voice_right_hand_note_ids)}, top_voice_left_hand_note_ids {len(top_voice_left_hand_note_ids)}")

    for s in subsegments_for_comparison:

        if s.musical_direction_type == MusicalDirectionTypes.DYNAMICS.value:
           
            # find out all wedges first
            occupied_regions_right = []
            occupied_regions_left = []

            wedges = [d for d in s.musical_directions if d.tag_name == "wedge"]
            non_wedges = [d for d in s.musical_directions if d.tag_name != "wedge"]
            for w in wedges:

                # FIXME there seems to be a bug where ending_note_identifier can be before starting_note_identifier when extracting wedges
                if int(w.starting_note_identifier.split('_')[-1]) < int(w.ending_note_identifier.split('_')[-1]):

                    if w.staff == "1":
                        occupied_regions_right.append([int(w.starting_note_identifier.split("_")[-1]), int(w.ending_note_identifier.split("_")[-1])])
                    else:
                        occupied_regions_left.append([int(w.starting_note_identifier.split("_")[-1]), int(w.ending_note_identifier.split("_")[-1])])

                    print(f"processing wedge from {w.starting_note_identifier} to {w.ending_note_identifier}, staff {w.staff}")

                    s.single_comparison_sections.append(SingleComparisonSection(
                        start_note_id=w.starting_note_identifier.split("_")[0],
                        end_note_id=w.ending_note_identifier.split("_")[0],
                        staff=w.staff,
                        musical_direction=w,
                        note_ids=Utils.find_between_note_ids(
                            start_note_id=w.starting_note_identifier.split("_")[0],
                            end_note_id=w.ending_note_identifier.split("_")[0],
                            from_note_ids=top_voice_right_hand_note_ids if w.staff == "1" else top_voice_left_hand_note_ids,
                            note_id_note_no_map=note_id_note_no_map
                        ),
                        comparison_methods=[
                            SectionComparisonMethods(
                                metric=SectionComparisonMetrics.ONSET_VELOCITY.value,
                                comparison_type=SectionComparisonTypes.RATIO_TREND.value
                            )
                        ]
                    ))
           
            # process non-wedge dynamics directions
            # treat directions like ff, p, mp as a single-note direction to start with
            non_overlapped_non_wedges = []

            for nw in non_wedges:
                note_no = int(nw.starting_note_identifier.split("_")[-1])
                is_included_in_wedge = False  
               
                measure = int(nw.starting_note_identifier.split("-")[1])

                occupied_regions = occupied_regions_right if nw.staff == "1" else occupied_regions_left

                for i, wr in enumerate(occupied_regions):
                    if note_no >= wr[0] and note_no <= wr[1]:
                        is_included_in_wedge = True
               
                if is_included_in_wedge:
                    # do not include this direction (for now)
                    pass

                else:
                    non_overlapped_non_wedges.append(nw)

                    if nw.tag_name == "dynamics":
                        if nw.staff == "1":
                            occupied_regions_right.append([int(nw.starting_note_identifier.split("_")[-1]), int(nw.starting_note_identifier.split("_")[-1])])
                        else:
                            occupied_regions_left.append([int(nw.starting_note_identifier.split("_")[-1]), int(nw.starting_note_identifier.split("_")[-1])])

           
            for nw in non_overlapped_non_wedges:

                # try to expand it as much as possible
                note_id = nw.starting_note_identifier.split("_")[0]
                note_no = int(nw.starting_note_identifier.split("_")[-1])
                m = int(nw.starting_note_identifier.split("-")[1])

                # TODO when direction is trends use SingleComparisonSection (+2 measures if possible), otherwise use BeforeAndAfterComparisonSection
                if nw.tag_name != "dynamics":

                    if nw.text in MusicalDirectionWords.DYNAMIC_DIRECTIONS_TREND.value:
                        end_note_id = Utils.find_last_note_id_in_measure(note_id_note_no_map, m + 2, last_measure)
                        end_note_no = note_id_note_no_map[end_note_id]

                        occupied_regions = occupied_regions_right if nw.staff == "1" else occupied_regions_left

                        for region in occupied_regions:
                            if region[0] < end_note_no and region[0] > note_no:
                                end_note_no = region[0]

                        end_note_id = note_no_note_id_map[end_note_no]

                        if nw.staff == "1":
                            occupied_regions_right.append([note_no, end_note_no])
                        else:
                            occupied_regions_left.append([note_no, end_note_no])

                        s.single_comparison_sections.append(
                            SingleComparisonSection(
                                start_note_id=note_id,
                                end_note_id=end_note_id,
                                staff=nw.staff,
                                musical_direction=nw,
                                note_ids=Utils.find_between_note_ids(
                                    start_note_id=note_id,
                                    end_note_id=end_note_id,
                                    from_note_ids=top_voice_right_hand_note_ids if nw.staff == "1" else top_voice_left_hand_note_ids,
                                    note_id_note_no_map=note_id_note_no_map
                                ),
                                comparison_methods=[
                                    SectionComparisonMethods(
                                        metric=SectionComparisonMetrics.ONSET_VELOCITY.value,
                                        comparison_type=SectionComparisonTypes.RATIO_TREND.value
                                    )
                                ]
                            )
                        )


                    else:
                        # for dynamics tag directions, its +1 and -1 measures are considered in before_note_id and after_note_id. However, only note IDs in its measure are added to occupied_regions so that one dynamics direction wouldn't block another one in the next measure
                        before_start_note_id = Utils.find_first_note_id_in_measure(note_id_note_no_map, m - 1, first_measure)
                        after_end_note_id = Utils.find_last_note_id_in_measure(note_id_note_no_map, m + 1, last_measure)

                        before_start_note_no = note_id_note_no_map[before_start_note_id]
                        after_end_note_no = note_id_note_no_map[after_end_note_id]

                        occupied_regions = occupied_regions_right if nw.staff == "1" else occupied_regions_left

                        for region in occupied_regions:

                            if region[-1] > before_start_note_no and region[-1] < note_no:
                                before_start_note_no = region[-1]

                            if region[0] < after_end_note_no and region[0] > note_no:
                                after_end_note_no = region[0]

                        before_start_note_id = note_no_note_id_map[before_start_note_no]
                        after_end_note_id = note_no_note_id_map[after_end_note_no]

                        if nw.staff == "1":
                            occupied_regions_right.append([before_start_note_no, after_end_note_no])
                        else:
                            occupied_regions_left.append([before_start_note_no, after_end_note_no])

                        comparison_section = BeforeAndAfterComparisonSection(
                            before_start_note_id=before_start_note_id,
                            before_end_note_id=note_id,
                            after_start_note_id=note_id,
                            after_end_note_id=after_end_note_id,
                            staff=nw.staff,
                            musical_direction=nw,
                            before_note_ids=Utils.find_between_note_ids(
                                start_note_id=before_start_note_id,
                                end_note_id=note_id,
                                from_note_ids=top_voice_right_hand_note_ids if nw.staff == "1" else top_voice_left_hand_note_ids,
                                note_id_note_no_map=note_id_note_no_map,
                                include_end=False
                            ),
                            after_note_ids=Utils.find_between_note_ids(
                                start_note_id=note_id,
                                end_note_id=after_end_note_id,
                                from_note_ids=top_voice_right_hand_note_ids if nw.staff == "1" else top_voice_left_hand_note_ids,
                                note_id_note_no_map=note_id_note_no_map
                            ),
                            comparison_methods=[
                                SectionComparisonMethods(
                                    metric=SectionComparisonMetrics.ONSET_VELOCITY.value,
                                    comparison_type=SectionComparisonTypes.RATIO_AVG_BEFORE_AND_AFTER.value
                                ),
                            ]
                        )
                   
                        s.before_n_after_comparison_sections.append(comparison_section)

               
            occupied_regions_right = sorted(occupied_regions_right, key=lambda x: x[0])
            occupied_regions_left = sorted(occupied_regions_left, key=lambda x: x[0])

            # remove dynamics tag directions from occupied_regions since dynamics tag directions CAN overlap each other in their before & after comparison regions

            # try to expand dynamics tag directions as much as possible. Ignore other dynamics tag direction in this process

            for nw in non_overlapped_non_wedges:
                if nw.tag_name == "dynamics":
                    print(f"dynamics tag direction found at {nw.starting_note_identifier.split('_')[-1]}")
                    note_id = nw.starting_note_identifier.split("_")[0]
                    note_no = int(nw.starting_note_identifier.split("_")[-1])
                    m = int(nw.starting_note_identifier.split("-")[1])

                    before_start_note_id = Utils.find_first_note_id_in_measure(note_id_note_no_map, m - 1, first_measure)
                    after_end_note_id = Utils.find_last_note_id_in_measure(note_id_note_no_map, m + 1, last_measure)

                    print(f"before_start_note_id {before_start_note_id}, after_end_note_id {after_end_note_id} for dynamic tag direction at {note_id}")

                    before_start_note_no = note_id_note_no_map[before_start_note_id]
                    after_end_note_no = note_id_note_no_map[after_end_note_id]

                    occupied_regions = occupied_regions_right if nw.staff == "1" else occupied_regions_left

                    for region in occupied_regions:

                        if region[-1] > before_start_note_no and region[-1] < note_no:
                            before_start_note_no = region[-1]

                        if region[0] < after_end_note_no and region[0] > note_no:
                            after_end_note_no = region[0]

                    before_start_note_id = note_no_note_id_map[before_start_note_no]
                    after_end_note_id = note_no_note_id_map[after_end_note_no]
                   
                    print(f"before_start_note_id {before_start_note_id}, after_end_note_id {after_end_note_id} for dynamics tag direction at {note_id}")

                    s.before_n_after_comparison_sections.append(
                        BeforeAndAfterComparisonSection(
                            before_start_note_id=before_start_note_id,
                            before_end_note_id=note_id,
                            after_start_note_id=note_id,
                            after_end_note_id=after_end_note_id,
                            staff=nw.staff,
                            musical_direction=nw,
                            before_note_ids=Utils.find_between_note_ids(
                                start_note_id=before_start_note_id,
                                end_note_id=note_id,
                                from_note_ids=top_voice_right_hand_note_ids if nw.staff == "1" else top_voice_left_hand_note_ids,
                                note_id_note_no_map=note_id_note_no_map,
                                include_end=False
                            ),
                            after_note_ids=Utils.find_between_note_ids(
                                start_note_id=note_id,
                                end_note_id=after_end_note_id,
                                from_note_ids=top_voice_right_hand_note_ids if nw.staff == "1" else top_voice_left_hand_note_ids,
                                note_id_note_no_map=note_id_note_no_map
                            ),
                            comparison_methods=[
                                SectionComparisonMethods(
                                    metric=SectionComparisonMetrics.ONSET_VELOCITY.value,
                                    comparison_type=SectionComparisonTypes.RATIO_AVG_BEFORE_AND_AFTER.value
                                )
                            ]
                        )
                    )


        if s.musical_direction_type == MusicalDirectionTypes.TEMPO.value:

            # get all tempo related directions
            tempo_directions_note_numbers = []
            for _, directions in measure_no_tempo_directions_map.items():
                for d in directions:
                    tempo_directions_note_numbers.append(int(d.starting_note_identifier.split("_")[-1]))
           
            print(f"tempo_directions_note_numbers: {tempo_directions_note_numbers}")

            # include surrounding 3 measures (for trend direction the next 3 measures only) for each tempo direction if possible
            for direction in s.musical_directions:
                note_id = direction.starting_note_identifier.split("_")[0]
                note_no = int(direction.starting_note_identifier.split("_")[-1])
                m = int(direction.starting_note_identifier.split("-")[1])

                is_trend_direction = direction.text in MusicalDirectionWords.TEMPO_DIRECTIONS_TREND.value

                if is_trend_direction:
                    end_note_id = Utils.find_last_note_id_in_measure(note_id_note_no_map, m + 3, last_measure)
                    end_note_no = note_id_note_no_map[end_note_id]
                    for i, n in enumerate(tempo_directions_note_numbers):
                        if note_no < n < end_note_no:
                            end_note_id = note_no_note_id_map[n]

                    cs = SingleComparisonSection(
                        start_note_id=note_id,
                        end_note_id=end_note_id,
                        staff=direction.staff,
                        musical_direction=direction,
                        note_ids=Utils.find_between_note_ids(
                            start_note_id=note_id,
                            end_note_id=end_note_id,
                            from_note_ids=top_voice_right_hand_note_ids if direction.staff == "1" else top_voice_left_hand_note_ids,
                            note_id_note_no_map=note_id_note_no_map,
                            include_end=False
                        ),
                        comparison_methods=[
                            SectionComparisonMethods(
                                metric=SectionComparisonMetrics.ONSET_VELOCITY.value,
                                comparison_type=SectionComparisonTypes.RATIO_TREND.value
                            )
                        ]
                    )

                    s.single_comparison_sections.append(cs)

                else:

                    before_start_note_id = Utils.find_first_note_id_in_measure(note_id_note_no_map, m - 3, first_measure)
                    after_end_note_id = Utils.find_last_note_id_in_measure(note_id_note_no_map, m + 3, last_measure)

                    before_start_note_no = note_id_note_no_map[before_start_note_id]
                    after_end_note_no = note_id_note_no_map[after_end_note_id]
                    # check if any other tempo direction is in between

                    for i, n in enumerate(tempo_directions_note_numbers):
                        if before_start_note_no < n < note_no:
                            before_start_note_no = n
                       
                        if note_no < n < after_end_note_no:
                            after_end_note_no = n

                    before_start_note_id = note_no_note_id_map[before_start_note_no]
                    after_end_note_id = note_no_note_id_map[after_end_note_no]

                    cs = BeforeAndAfterComparisonSection(
                        before_start_note_id=before_start_note_id,
                        before_end_note_id=note_id,
                        after_start_note_id=note_id,
                        after_end_note_id=after_end_note_id,
                        musical_direction=direction,
                        before_note_ids=Utils.find_between_note_ids(
                            start_note_id=before_start_note_id,
                            end_note_id=note_id,
                            from_note_ids=top_voice_right_hand_note_ids if direction.staff == "1" else top_voice_left_hand_note_ids,
                            note_id_note_no_map=note_id_note_no_map,
                            include_end=False
                        ),
                        after_note_ids=Utils.find_between_note_ids(
                            start_note_id=note_id,
                            end_note_id=after_end_note_id,
                            from_note_ids=top_voice_right_hand_note_ids if direction.staff == "1" else top_voice_left_hand_note_ids,
                            note_id_note_no_map=note_id_note_no_map
                        ),
                        comparison_methods=[
                            SectionComparisonMethods(
                                metric=SectionComparisonMetrics.ONSET_TIME.value,
                                comparison_type=SectionComparisonTypes.RATIO_AVG_BEFORE_AND_AFTER.value
                            )
                        ]
                    )

                    if m == first_measure and not cs.before_note_ids and direction.tag_name == "words" and direction.text:
                        cs.is_initial_tempo_marking = True

                    s.before_n_after_comparison_sections.append(cs)

        if s.musical_direction_type == MusicalDirectionTypes.ARTICULATION.value:
            # follow the same approach as tempo directions (for now)
            articulation_directions_note_numbers = []
            for _, directions in measure_no_articulation_directions_map.items():
                for d in directions:
                    articulation_directions_note_numbers.append(int(d.starting_note_identifier.split("_")[-1]))

            for direction in s.musical_directions:
                note_id = direction.starting_note_identifier.split("_")[0]
                note_no = int(direction.starting_note_identifier.split("_")[-1])
                m = int(direction.starting_note_identifier.split("-")[1])
                before_start_note_id = Utils.find_first_note_id_in_measure(note_id_note_no_map, m - 5, first_measure)
                after_end_note_id = Utils.find_last_note_id_in_measure(note_id_note_no_map, m + 5, last_measure)

                before_start_note_no = note_id_note_no_map[before_start_note_id]
                after_end_note_no = note_id_note_no_map[after_end_note_id]
                for i, n in enumerate(articulation_directions_note_numbers):
                    if before_start_note_no < n < note_no:
                        before_start_note_no = n
                   
                    if note_no < n < after_end_note_no:
                        after_end_note_no = n

                before_start_note_id = note_no_note_id_map[before_start_note_no]
                after_end_note_id = note_no_note_id_map[after_end_note_no]

                s.before_n_after_comparison_sections.append(
                    BeforeAndAfterComparisonSection(
                        before_start_note_id=before_start_note_id,
                        before_end_note_id=note_id,
                        after_start_note_id=note_id,
                        after_end_note_id=after_end_note_id,
                        musical_direction=direction,
                        before_note_ids=Utils.find_between_note_ids(
                            start_note_id=before_start_note_id,
                            end_note_id=note_id,
                            from_note_ids=top_voice_right_hand_note_ids if direction.staff == "1" else top_voice_left_hand_note_ids,
                            note_id_note_no_map=note_id_note_no_map,
                            include_end=False
                        ),
                        after_note_ids=Utils.find_between_note_ids(
                            start_note_id=note_id,
                            end_note_id=after_end_note_id,
                            from_note_ids=top_voice_right_hand_note_ids if direction.staff == "1" else top_voice_left_hand_note_ids,
                            note_id_note_no_map=note_id_note_no_map
                        ),
                        comparison_methods=[
                            # TODO these are experimental comparison methods
                            SectionComparisonMethods(
                                metric=SectionComparisonMetrics.ONSET_TIME.value,
                                comparison_type=SectionComparisonTypes.RATIO_AVG_BEFORE_AND_AFTER.value
                            ),
                            SectionComparisonMethods(
                                metric=SectionComparisonMetrics.ONSET_VELOCITY.value,
                                comparison_type=SectionComparisonTypes.RATIO_AVG_BEFORE_AND_AFTER.value
                            ),
                            SectionComparisonMethods(
                                metric=SectionComparisonMetrics.NOTE_DURATION.value,
                                comparison_type=SectionComparisonTypes.RATIO_AVG_BEFORE_AND_AFTER.value
                            )
                        ]
                    )
                )
    
    for sub in subsegments_for_comparison:
        print("\n\n")

        sub.sort_before_n_after_comparison_sections()
        sub.sort_single_comparison_sections()

        for s in sub.single_comparison_sections:
            build_prompt_template(comparison_section=s, subsegment=sub)

        for s in sub.before_n_after_comparison_sections:
            build_prompt_template(comparison_section=s, subsegment=sub)

    # TODO add global subsegments for comparison
    global_subsegments_for_comparison = get_global_subsegments_for_comparison()
    subsegments_for_comparison = global_subsegments_for_comparison + subsegments_for_comparison

    for sub in subsegments_for_comparison:

        print(f"Subsegment for comparison: {str(sub)}")
        if sub.musical_directions:
            for d in sub.musical_directions:
                print(str(d))    

        if sub.before_n_after_comparison_sections:
            for b in sub.before_n_after_comparison_sections:
                print(f"Before & After Comparison Section: {str(b)}")

        if sub.single_comparison_sections:
            for s in sub.single_comparison_sections:
                print(f"Single Comparison Section: {str(s)}")

        print("\n")

    return ScoreDetails(
        score_id=score_id,
        unnested_note_identifier_directions_map=note_identifier_directions_map,
        unnested_measure_no_articulation_details_map=measure_no_articulation_directions_map,
        subsegments_for_comparison=subsegments_for_comparison
    )



def segment_by_slurs(xml_tree, staff_no:str, voice_no:str)->list:
    root = xml_tree.getroot()

    unclosed_slur_start_no_note_no_map = dict()     # key: slur number, value: note number

    segments = list()

    curr_note_no = 0
    curr_measure_no = None

    for measure in root.findall(".//measure"):

        curr_measure_no = measure.get("number")

        # skip rest notes
        for note in measure.findall(".//note"):
            if note.find(".//rest") is not None:
                #print(f"Skipping rest note at measure {curr_measure_no}")
                continue

            curr_note_no += 1

            staff = note.find(".//staff").text
            #print(f"staff: {staff}, {type(staff)}, measure {curr_measure_no}")
            if staff != staff_no:
                # skip this note
                continue

            voice = None
           
            for note_child in note:
                if note_child.tag == "voice":
                    voice = note_child.text

            if voice != voice_no:
                continue
           
            for notation in note.findall(".//notations"):
                slurs = notation.findall(".//slur")

                #print(f"{len(slurs)} found in measure {curr_measure_no}")

                if slurs:
                    for slur in slurs:
                        logger.debug(f"Note {curr_note_no} (measure {curr_measure_no}, voice {voice}): {slur.attrib.get('number')} - {slur.attrib.get('type')}")
                       
                        slur_no = slur.attrib.get("number")
                        slur_type = slur.attrib.get("type")
                       
                        if slur_type == "start":
                            if slur_no in unclosed_slur_start_no_note_no_map.keys():
                                logger.warning(f"Slur number {slur_no} is already present in unclosed_slur_start_no_note_no_map!")

                            unclosed_slur_start_no_note_no_map[slur_no] = curr_note_no
                       
                        if slur_type == "stop":
                            if slur_no in unclosed_slur_start_no_note_no_map.keys():
                                start_note_no = unclosed_slur_start_no_note_no_map[slur_no]
                                segments.append([ start_note_no, curr_note_no ])

                                unclosed_slur_start_no_note_no_map.pop(slur_no)

                            else:
                                logger.warning(f"Slur number {slur_no} is not found in unclosed_slur_start_no_note_no_map: {unclosed_slur_start_no_note_no_map}")


    note_no_note_id_map, _ = Utils.build_note_no_note_id_maps(xml_tree)

    final_segments = list()
    for seg in segments:
        start_note_no = seg[0]
        end_note_no = seg[1]      
       
        if start_note_no not in note_no_note_id_map.keys():
            logger.warning(f"start_note_no {start_note_no} not found in note_no_note_id_map for score")
            continue

        if end_note_no not in note_no_note_id_map.keys():
            logger.warning(f"end_note_no {end_note_no} not found in note_no_note_id_map for score")
            continue
        slurred_note_ids = list()

        for i in range(start_note_no, end_note_no + 1):
            slurred_note_ids.append(note_no_note_id_map[i])

        final_segments.append(slurred_note_ids)    
 
    return final_segments


"""
Returns: OrderedDict
<measure number (str): [list of ArticulationDetails objects]>
"""
def build_unnested_measure_no_articulation_details_map(xml_tree):
    root = xml_tree.getroot()
    parts = root.findall(".//part")

    if len(parts) > 1:
        raise RuntimeError(f"build_unnested_measure_no_articulation_requirements_map currently only supports single-part score")
   
    # find all slurs from score (note => notations => slur), use fmt3x file to align chords?
    # only collect top voice notes under slur initially
    top_voice_slur_note_ids = set()
    top_voice_slur_note_segments = segment_by_slurs(xml_tree, "1", "1")

    for segment in top_voice_slur_note_segments:
        top_voice_slur_note_ids.update(segment)

    result = OrderedDict()

    for part in root.findall(".//part"):
        for i, measure in enumerate(part.findall(".//measure")):

            curr_note_no = 1

            measure_no = measure.get("number")

            result[measure_no] = list()

            for child_node in measure:
                if child_node.tag == "note":

                    # skip rest notes
                    if child_node.find(".//rest") is not None:
                        continue

                    note_id = f"P1-{measure_no}-{curr_note_no}"

                    articulation_details = ArticulationDetails()
                    articulation_details.note_id = note_id

                    if note_id in top_voice_slur_note_ids:
                        articulation_details.is_slurred = True

                    notations = child_node.find("notations")
                    if notations is not None:
                        articulations = notations.find("articulations")
                        if articulations is not None:
                            accent = articulations.find("accent")
                            if accent is not None:
                                articulation_details.articulation_marking = ArticulationMarkings.ACCENT.value

                            marcato = articulations.find("strong-accent")
                            if marcato:
                                articulation_details.articulation_marking = ArticulationMarkings.MARCATO.value
                           
                            staccato = articulations.find("staccato")
                            if staccato is not None:
                                articulation_details.articulation_marking = ArticulationMarkings.STACCATO.value
                           
                            staccatissimo = articulations.find("staccatissimo")
                            if staccatissimo is not None:
                                articulation_details.articulation_marking = ArticulationMarkings.STACCATISSIMO.value

                            tenuto = articulations.find("tenuto")
                            if tenuto is not None:
                                articulation_details.articulation_marking = ArticulationMarkings.TENUTO.value

                    result[measure_no].append(articulation_details)

                    curr_note_no += 1

    return result



if __name__ == "__main__":
    st = time.time()
    d = build_score_details("/Users/haotian/Documents/documents-local/hercules/downloaded_musicxmls/op18.xml", "")
    print(d)
   
    et = time.time() - st

    print(f"Completed in {et:.2f} seconds.")
   
   
   

