


def build_note_no_note_id_map(xml_tree, has_repeats:bool=False)->dict:
    root = xml_tree.getroot()
    parts = root.findall(".//part")

    result = dict()

    if len(parts) > 1:
        raise RuntimeError(f"build_note_no_note_id_map currently only supports single-part score. Score {score_id}.xml (has_repeats: {has_repeats}) has {len(parts)} parts")
    
    curr_note_no = 1

    for i, part in enumerate(root.findall(".//part")):
        part_no = i + 1 

        for j, measure in enumerate(part.findall(".//measure")):
            measure_no = measure.get("number")

            for k, note in enumerate(measure.findall(".//note")):
                # skip rest notes
                if note.find(".//rest") is not None:
                    continue

                note_no = k + 1 
                result[curr_note_no] = f"P{part_no}-{measure_no}-{note_no}"
                curr_note_no += 1 

    return result 