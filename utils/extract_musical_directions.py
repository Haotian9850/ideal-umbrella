import xml.etree.ElementTree as ET
import logging
import sys

sys.path.append("../")


from classes import MusicalDirection
from utils.Utils import Utils
from collections import OrderedDict



logger = logging.getLogger("main")


def find_next_note(node, parent):

    index = None

    if parent:
        children = parent.findall(".//note")
        index = children.index(node)

    if index >= len(children) - 1:
        logger.warning(f"find_next_note: node {str(node)} is the last node in its parent {str(parent)}")
        return None
   
    next_note = None

    for i in range(index + 1, len(children), 1):
        n = children[i]
        if n.tag == "note":
            next_note = n
            break

    return next_note

def find_staff_in_note(note)->str:
    for note_child in note:
        if note_child.tag == "staff":
            return note_child.text
       
    return None

def is_rest_note(note)->bool:
    for note_child in note:
        if note_child.tag == "rest":
            return True
       
    return False

"""
Currently supports the following closed musical directions:
- wedge
"""
# TODO support wedges that only cover 1 single note. Example: {'staff': '1', 'starting_note_identifier': 'P1-203-1_4299', 'ending_note_identifier': 'P1-203-1_4299', 'tag_name': 'wedge', 'number': '3', 'type': 'diminuendo'} for score 65d57e32233f09b53a220ffe
# returns <P1-183-1_4075, [<closed direction>]>
def build_note_identifier_closed_directions_map(xml_tree)->OrderedDict:

    root = xml_tree.getroot()
    note_no_note_id_map, _ = Utils.build_note_no_note_id_maps(xml_tree)

    start_note_identifier_directions_map = OrderedDict()

    curr_note_no = 0

    curr_measure_no = 0

    unclosed_num_staff_note_no_type_map = dict() # key: <wedge number>-<staff>, value: <note number>-<wedge type>

    curr_note = None
    curr_note_copy = None

    parts = root.findall(".//part")
    if len(parts) > 1:
        raise RuntimeError(f"build_note_identifier_closed_directions_map currently only support single-part score")
   
    part = parts[0]

    for part in parts:
        for i, measure in enumerate(part.findall(".//measure")):
            curr_measure_no = measure.get("number")

            for child_node in measure:
                tag = child_node.tag

                if tag == "note":
                    if child_node.find(".//rest") is not None:
                        continue

                    curr_note = child_node
                    curr_note_copy = child_node

                    curr_note_no += 1

                if tag == "direction" and curr_note_no > 1:
                    # reset curr_note (in case of 2 wedge starts together)
                    curr_note = curr_note_copy

                    staff = None
                    number = None

                    for direction_child_node in child_node:
                        if direction_child_node.tag == "staff":
                            staff = direction_child_node.text
                            break

                    curr_note_staff = find_staff_in_note(curr_note)
                    if not curr_note_staff:
                        logger.error(f"build_note_identifier_closed_directions_map: note {curr_note_no} does not have explicit staff")
                        continue

                    for direction_child_node in child_node:
                        if direction_child_node.tag == "direction-type":
                            for direction_type_child_node in direction_child_node:

                                if direction_type_child_node.tag == "wedge":
                                    wedge_type = direction_type_child_node.attrib.get("type")

                                    number = direction_type_child_node.attrib.get("number")

                                    if staff is None:
                                        logger.error(f"build_note_identifier_closed_directions_map: staff not found for wedge at {curr_note_no}")
                                        continue

                                    # find true note number for this wedge
                                    true_note_no = curr_note_no

                                    while curr_note is not None and (is_rest_note(curr_note) or find_staff_in_note(curr_note) != staff):
                                        logger.debug(f"build_note_identifier_closed_directions_map: curr_note {note_no_note_id_map[true_note_no]} (staff {find_staff_in_note(curr_note)}, rest {is_rest_note(curr_note)}) does not match direction staff {staff}, continue to its next note...")
                                        curr_note = find_next_note(curr_note, part)
                                        true_note_no += 1

                                    # use curr_note
                                    if not curr_note:
                                        logger.error(f"build_note_identifier_closed_directions_map: no next_note found from {curr_note_no} ({note_no_note_id_map[curr_note_no]}) matches wedge staff {staff} at measure {curr_measure_no}, investigate!")
                                        continue

                                    if true_note_no != curr_note_no:
                                        logger.debug(f"build_note_identifier_closed_directions_map: adjusting note number for wedge at {curr_note_no} (staff {curr_note_staff}, note {note_no_note_id_map[curr_note_no]}) to {true_note_no} (staff {find_staff_in_note(curr_note)}, note {note_no_note_id_map[true_note_no]}), wedge staff {staff}, wedge type {wedge_type}, measure {curr_measure_no}")

                                    key = f"{number or 'UNNUMBERED'}-{staff}"

                                    if wedge_type == "stop":
                                        if key not in unclosed_num_staff_note_no_type_map:
                                            logger.error(f"build_note_identifier_closed_directions_map: key {key} not found in map for stop direction at {curr_note_no}")
                                            break
                                       
                                        v = unclosed_num_staff_note_no_type_map[key]
                                        starting_note_no = int(v.split("-")[0])
                                        wedge_type = v.split("-")[1]

                                        starting_note_identifier = f"{note_no_note_id_map[starting_note_no]}_{starting_note_no}"

                                        # TODO track the placement together with staff. Consider staff = 2 and placement = "above" as staff 1 in downstream analysis (so that staff 1 notes get analyzed instead of staff 2 notes)
                                        w = MusicalDirection(
                                            starting_note_identifier=starting_note_identifier,
                                            ending_note_identifier=f"{note_no_note_id_map[true_note_no]}_{true_note_no}",
                                            tag_name="wedge",
                                            staff=staff,
                                            number=direction_type_child_node.attrib.get("number"),
                                            spread=direction_type_child_node.attrib.get("spread"),
                                            type=wedge_type
                                        )

                                        unclosed_num_staff_note_no_type_map.pop(key)

                                        if starting_note_identifier in start_note_identifier_directions_map.keys():
                                            start_note_identifier_directions_map[starting_note_identifier].append(w)
                                        else:
                                            start_note_identifier_directions_map[starting_note_identifier] = [ w ]

                                    else:
                                        if key in unclosed_num_staff_note_no_type_map.keys():
                                            logger.error(f"build_note_identifier_closed_directions_map: key {key} already present in map at note {true_note_no} (curr_measure_no {curr_measure_no})") 

                                        v = f"{true_note_no}-{direction_type_child_node.attrib.get('type')}"
                                        #print(f"Setting key {key} to value {v}")

                                        unclosed_num_staff_note_no_type_map[key] = v

    return start_note_identifier_directions_map
                                       
                                           
                       
# returns <P1-183-1_4075, [<musical direction>]>
def build_note_identifier_directions_map(xml_tree:str)->OrderedDict:

    root = xml_tree.getroot()
    parts = root.findall(".//part")

    if len(parts) > 1:
        raise RuntimeError(f"build_note_identifier_direction_map currently only supports single-part score")
   
    curr_note_no = 1

    note_no_note_id_map, _ = Utils.build_note_no_note_id_maps(xml_tree)
    note_identifier_directions_map = OrderedDict() # key: note identifier, value: list of musical directions
   
    for part in root.findall(".//part"):
        for i, measure in enumerate(part.findall(".//measure")):
            # iterate each child node of measure

            first_note_no_in_measure = None

            directions_before_first_note = []

            # seek to first note before checking directions, in case the direction node is the first node in <measure>
            for child_node in measure:
                if child_node.tag == "note" and child_node.find(".//rest") is None:
                    #print(f"First note found for measure {measure.get('number')}, directions_before_first_note {len(directions_before_first_note)}")
                    # first note found
                    break

                if child_node.tag == "direction":
                    staff = child_node.find("staff").text

                    for direction_child_node in child_node:

                        if direction_child_node.tag == "direction-type":
                            for direction_type_child_node in direction_child_node:
                                t = direction_type_child_node.tag

                                if t == "words":
                                    directions_before_first_note.append(
                                        MusicalDirection(
                                            starting_note_identifier=None,
                                            tag_name="words",
                                            staff=staff,
                                            text=direction_type_child_node.text
                                        )
                                    )  
                                elif t == "dynamics":
                                    for cn in direction_type_child_node:
                                       
                                        if cn.tag != "other-dynamics":
                                            directions_before_first_note.append(
                                                MusicalDirection(
                                                    starting_note_identifier=None,
                                                    tag_name="dynamics",
                                                    staff=staff,  
                                                    child_tag_name=cn.tag
                                                )
                                            )
                       

            for child_node in measure:
                tag = child_node.tag

                if tag == "note":

                    if child_node.find(".//rest") is not None:
                        continue

                    if not first_note_no_in_measure:
                        first_note_no_in_measure = curr_note_no
                        print(f"first_note_no_in_measure for measure {measure.get('number')} is {first_note_no_in_measure}")

                    # when last note is reached, stop incrementing the pointer
                    if curr_note_no < max(note_no_note_id_map.keys()):
                        curr_note_no += 1


                if tag == "direction":

                    if curr_note_no not in note_no_note_id_map.keys():
                        raise RuntimeError(f"build_note_identifier_directions_map: curr_note_no {curr_note_no} not found in note_no_note_id_map: {note_no_note_id_map}")

                    note_id = note_no_note_id_map[curr_note_no]
                    note_identifier = f"{note_id}_{curr_note_no}"

                    if not note_identifier_directions_map.get(note_identifier):
                        note_identifier_directions_map[note_identifier] = list()

                    staff = None
                    # find staff
                    for direction_child_node in child_node:
                        if direction_child_node.tag == "staff":
                            staff = direction_child_node.text
                   
                    if not staff:
                        logger.error(f"build_note_identifier_directions_map: staff not found for direction at {note_identifier}, skipping...")
                        continue
                   
                    for direction_child_node in child_node:
                        if direction_child_node.tag == "direction-type":
                            for direction_type_child_node in direction_child_node:
                                t = direction_type_child_node.tag

                                if t == "words":
                                    print(f"words direction {direction_type_child_node.text} found at {note_identifier}")

                                    note_identifier_directions_map[note_identifier].append(
                                        MusicalDirection(
                                            starting_note_identifier=note_identifier,
                                            tag_name="words",
                                            staff=staff,
                                            text=direction_type_child_node.text
                                        )
                                    )
                               
                                elif t == "metronome":
                                    # FIXME correctly populate beat_unit and per_minute
                                    note_identifier_directions_map[note_identifier].append(
                                        MusicalDirection(
                                            starting_note_identifier=note_identifier,
                                            tag_name="metronome",
                                            staff=staff,
                                            beat_unit=direction_type_child_node.find("beat-unit").text if direction_type_child_node.find("beat-unit") else None,
                                            per_minute=direction_type_child_node.find("per-minute").text if direction_type_child_node.find("per-minute") else None
                                        )
                                    )

                                elif t == "dynamics":
                                    for cn in direction_type_child_node:
                                        note_identifier_directions_map[note_identifier].append(
                                            MusicalDirection(
                                                starting_note_identifier=note_identifier,
                                                tag_name="dynamics",
                                                staff=staff,
                                                child_tag_name=cn.tag
                                            )
                                        )

                                elif t == "bracket":
                                    note_identifier_directions_map[note_identifier].append(
                                        MusicalDirection(
                                            starting_note_identifier=note_identifier,
                                            tag_name="bracket",
                                            staff=staff,
                                            line_end=direction_type_child_node.attrib.get("line-end"),
                                            line_type=direction_type_child_node.attrib.get("line-type"),
                                            number=direction_type_child_node.attrib.get("number"),
                                            type=direction_type_child_node.attrib.get("type")
                                        )
                                    )
                               
                                elif t == "octave-shift":
                                    note_identifier_directions_map[note_identifier].append(
                                        MusicalDirection(
                                            starting_note_identifier=note_identifier,
                                            tag_name="octave_shift",
                                            staff=staff,
                                            number=direction_type_child_node.attrib.get("number"),
                                            size=direction_type_child_node.attrib.get("size"),
                                            type=direction_type_child_node.attrib.get("type")
                                        )
                                    )

                                elif t == "pedal":
                                    note_identifier_directions_map[note_identifier].append(
                                        MusicalDirection(
                                            starting_note_identifier=note_identifier,
                                            tag_name="pedal",
                                            staff=staff,
                                            type=direction_type_child_node.attrib.get("type"),
                                            line=direction_type_child_node.attrib.get("line")
                                        )
                                    )

                                else:
                                    if t != "wedge":
                                        logger.warning(f"build_note_identifier_directions_map: unsupported direction tag {t} at {note_identifier}")

            # assign any directions before first note to the first note
            if directions_before_first_note:
                first_note_id = note_no_note_id_map[first_note_no_in_measure]
                first_note_identifier = f"{first_note_id}_{first_note_no_in_measure}"

                print(f"directions_before_first_note found in measure {measure.get('number')}, first_note_identifier {first_note_identifier}")

                for d in directions_before_first_note:
                    print(f"Adding direction before first note to {first_note_identifier}: {str(d)}")
                    d.starting_note_identifier = first_note_identifier

                note_identifier_directions_map[first_note_identifier] = directions_before_first_note

    # remove empty lists from result
    note_identifier_directions_map = OrderedDict((k, v) for k, v in note_identifier_directions_map.items() if v)

    # add closed musical directions
    m = build_note_identifier_closed_directions_map(xml_tree)
    for note_identifier, directions in m.items():
        for direction in directions:
            if direction.starting_note_identifier in note_identifier_directions_map.keys():
                note_identifier_directions_map[note_identifier].append(direction)
            else:
                note_identifier_directions_map[note_identifier] = [ direction ]

    sorted_note_identifiers = Utils.sort_note_identifiers(list(note_identifier_directions_map.keys()))
    result = OrderedDict()
    for note_identifier in sorted_note_identifiers:
        result[note_identifier] = note_identifier_directions_map[note_identifier]

    return result
   