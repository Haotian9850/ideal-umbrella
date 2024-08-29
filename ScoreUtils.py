import xml.etree.ElementTree as ET
import logging
from collections import OrderedDict
import sys 
import Utils

from ArticulationMarkings import ArticulationMarkings

logger = logging.getLogger("main")

class ArticulationDetails():
    def __init__(self, **kwargs):
        self.note_id = kwargs.get("note_id")
        self.is_slurred = kwargs.get("is_under_slur")   # legato articulation?
        self.articulation_marking = kwargs.get("articulation_marking")
        self.staff = kwargs.get("staff")

    def __str__(self):
        return str(vars(self))


def segment_by_slurs(xml_tree, staff_no:str, voice_no:str)->list:
    root = xml_tree.getroot()

    unclosed_slur_start_no_note_no_map = dict()     # key: slur number, value: note number

    segments = list()

    curr_note_no = 0
    curr_measure_no = None

    for measure in root.findall(".//measure"):

        curr_measure_no = measure.get("number")

        # TODO skip rest notes
        for note in measure.findall(".//note"):
            
            if note.find(".//rest") is not None:
                print(f"Skipping rest note at measure {curr_measure_no}")
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


    note_no_note_id_map = Utils.build_note_no_note_id_map(xml_tree)

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

    print(final_segments)
 
    return final_segments


"""
Returns: OrderedDict
<measure number (str): [list of ArticulationDetails objects]>
"""
def build_unnested_measure_no_articulation_details_map(unnested_score_xml_path:str):
    tree = ET.parse(unnested_score_xml_path)
    root = tree.getroot()
    parts = root.findall(".//part")

    if len(parts) > 1:
        raise RuntimeError(f"build_unnested_measure_no_articulation_requirements_map currently only supports single-part score. Score {unnested_score_xml_path} has {len(parts)} parts")
    
    # find all slurs from score (note => notations => slur), use fmt3x file to align chords?
    # only collect top voice notes under slur initially
    top_voice_slur_note_ids = set()
    top_voice_slur_note_segments = segment_by_slurs(unnested_score_xml_path, "1", "1")

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
    #segment_by_slurs("../downloaded_musicxmls/op10_no3.xml", "1", "1")
    m = build_unnested_measure_no_articulation_details_map("../downloaded_musicxmls/op10_no3.xml", dict())

    for measure_no, articulation_details in m.items():
        print(f"Measure {measure_no}:")
        for d in articulation_details:
            print(str(d))

    
    
    
    

