from constants.Constants import Constants
import logging
import shutil
import xml.etree.ElementTree as ET
from collections import OrderedDict
import subprocess
import os
import json 
from google.cloud import storage
from google.cloud import pubsub_v1

import sys 
sys.path.append("../")


class Utils():

    logger = logging.getLogger("main")

    gcs_client = storage.Client() if Constants.USE_GCS else None 
    pubsub_client = pubsub_v1.PublisherClient()
    background_job_topic_path = pubsub_client.topic_path(Constants.GCP_PROJECT_ID, Constants.BACKGROUND_PUBSUB_TOPIC)


    @staticmethod
    def publish_background_job_message_sync(message:dict):
        data = json.dumps(message).encode("utf-8")
        future = Utils.pubsub_client.publish(Utils.background_job_topic_path, data)
        Utils.logger.info(f"publish_pubsub_message_sync: result for message {str(message)}: {future.result()}")

    @staticmethod
    def check_file_exists_gcs(file_name):
        # Create a client
        client = storage.Client()

        # Get the bucket
        bucket = client.bucket(Constants.GCS_BUCKET_NAME)

        # Get the blob (file object)
        blob = bucket.blob(file_name)

        # Check if the blob exists
        return blob.exists()
    
    @staticmethod
    def delete_file_in_gcs(file_name:str):
        bucket = Utils.gcs_client.bucket(Constants.GCS_BUCKET_NAME)
        blob = bucket.blob(file_name)

        Utils.logger.info(f"Deleting {file_name} in GCS bucket {Constants.GCS_BUCKET_NAME}")
        blob.delete()


    @staticmethod
    def download_file_to_tmp_dir(file_name:str, gcs_bucket_name=None):
        if Constants.USE_GCS:
            bucket = Utils.gcs_client.bucket(Constants.GCS_BUCKET_NAME if not gcs_bucket_name else gcs_bucket_name)
            blob = bucket.blob(file_name)
            Utils.logger.info(f"Downloading file {file_name} from GCS bucket {Constants.GCS_BUCKET_NAME if not gcs_bucket_name else gcs_bucket_name} to {Constants.TMP_DIR}")
            blob.download_to_filename(f"{Constants.TMP_DIR}/{file_name}")

        else:
            Utils.logger.info(f"Downloading file {file_name} from {Constants.LOCAL_DATA_PATH} to {Constants.TMP_DIR}")
            src = f"{Constants.LOCAL_DATA_PATH}/{file_name}"
            dest = f"{Constants.TMP_DIR}/{file_name}"
            shutil.copyfile(src, dest)



    @staticmethod
    def upload_file(file_name:str=None, dest_file_name:str=None, src_path=None, dest_path=None, gcs_bucket:str=Constants.GCS_BUCKET_NAME):
        if Constants.USE_GCS:
            bucket = Utils.gcs_client.bucket(gcs_bucket)

            if not dest_file_name:
                blob = bucket.blob(file_name)
                Utils.logger.info(f"Uploading file {file_name} to GCS bucket {Constants.GCS_BUCKET_NAME}")

                if not src_path:
                    blob.upload_from_filename(f"{Constants.TMP_DIR}/{file_name}")
                else:
                    blob.upload_from_filename(src_path)
            
            else:
                blob = bucket.blob(dest_file_name)
                Utils.logger.info(f"Uploading file {file_name} as {dest_file_name} to GCS bucket {Constants.GCS_BUCKET_NAME}")

                if not src_path:
                    blob.upload_from_filename(f"{Constants.TMP_DIR}/{file_name}")
                else:
                    blob.upload_from_filename(src_path)

        else:
            Utils.logger.info(f"Uploading file {file_name} from {Constants.TMP_DIR} to {Constants.LOCAL_DATA_PATH}")

            src = src_path if src_path else f"{Constants.TMP_DIR}/{file_name}"
            dest = dest_path if dest_path else f"{Constants.LOCAL_DATA_PATH}/{file_name}"
            
            shutil.copyfile(src, dest)

    
    @staticmethod
    def join_text(s:str)->str:
        parts = [p.strip().rstrip() for p in s.split(" ")]
        return "_".join(parts)


    @staticmethod
    def sort_measure_ids(measure_ids:list)->list:
        return sorted(list(measure_ids), key=lambda x: (int(x.split("-")[0].replace("P", "")), int(x.split("-")[1])))
    
    @staticmethod
    def sort_note_ids(note_ids:list)->list:
        processed_note_ids = [n.replace("P", "") for n in note_ids]

        # omit note IDs in implicit measures
        processed_note_ids = [i for i in processed_note_ids if not i.split("-")[1].startswith("X")]

        temp = sorted(processed_note_ids, key=lambda n : (
            int(n.split("-")[0]),
            int(n.split("-")[1]),
            int(n.split("-")[2])
        ))
        return [f"P{t}" for t in temp]
    
    @staticmethod
    def sort_note_identifiers(note_identifiers:list):
        """
        Sort a list of note identifiers in ascending order.

        Args:
            note_identifiers (list): A list of note identifiers in the format "P1-183-1_4075".

        Returns:
            list: The sorted list of note identifiers.
        """
        return sorted(note_identifiers, key=lambda x: int(x.split("_")[1]))

    @staticmethod
    def extract_note_number_from_note_identifier(i:str):
        parts = i.split("_")
        if len(parts) != 2:
            raise RuntimeError(f"extract_note_number_from_note_identifier: malformed identifier {i}")
        
        return int(parts[1])

    @staticmethod
    def extract_note_id_from_note_identifier(i:str):
        parts = i.split("_")
        if len(parts) != 2:
            raise RuntimeError(f"extract_note_id_from_note_identifier: malformed identifier {i}")
        
        return parts[0]
    
    @staticmethod
    def extract_measure_number_from_note_identifier(i:str):
        note_id = Utils.extract_note_id_from_note_identifier(i)
        parts = note_id.split("-")
        if len(parts) != 3:
            raise RuntimeError(f"extract_measure_number_from_note_identifier: malformed note_id {note_id}")
        
        return int(parts[1])
    
    @staticmethod
    def extract_measure_number_from_note_id(note_id:str):
        parts = note_id.split("-")
        if len(parts) != 3:
            raise RuntimeError(f"extract_measure_number_from_note_id: malformed note_id {note_id}")
        
        if not parts[1].isdigit():
            Utils.logger.warning(f"extract_measure_number_from_note_id: possible implicit measure in {note_id}")
            return parts[1]

        return int(parts[1])
    
    
    # key: P1-1, value: 1
    # note that some score starts from measure 0 instead of measure 1
    @staticmethod
    def get_measure_id_map_from_score(score_id:str, has_repeats:bool=False, ignore_implicit_measure:bool=True)->OrderedDict:
        result = OrderedDict()
        tree = ET.parse(f"{Constants.TMP_DIR}/{score_id}.xml" if not has_repeats else f"{Constants.TMP_DIR}/unnested_{score_id}.xml")
        root = tree.getroot()

        for i, part in enumerate(root.findall(".//part")):
            part_no = i + 1

            for j, measure in enumerate(root.findall(".//measure")):
                measure_no = Utils.find_measure_no(measure)

                measure_id = f"P{part_no}-{measure_no}"
                result[measure_id] = measure_no

        return result
    
    @staticmethod
    def combine_intervals(intervals, threshold):
        if not intervals:
            return []

        combined_intervals = []
        current_start, current_end = intervals[0]

        for i in range(1, len(intervals)):
            next_start, next_end = intervals[i]

            # Merge intervals if the current interval size is below the threshold
            if current_end - current_start < threshold:
                if next_start <= current_end:
                    current_end = max(current_end, next_end)
                else:
                    current_end = next_end
            else:
                combined_intervals.append([current_start, current_end])
                current_start, current_end = next_start, next_end

        # Add the last interval
        if current_end - current_start < threshold and combined_intervals:
            combined_intervals[-1][1] = max(combined_intervals[-1][1], current_end)
        else:
            combined_intervals.append([current_start, current_end])

        return combined_intervals

    


    # returns <note number, note ID (P1-2-3)>
    @staticmethod
    def build_note_no_note_id_map(score_id:str, has_repeats:bool=False)->dict:
        tree = ET.parse(f"{Constants.TMP_DIR}/{score_id}.xml" if not has_repeats else f"{Constants.TMP_DIR}/unnested_{score_id}.xml")
        root = tree.getroot()
        parts = root.findall(".//part")

        result = dict()

        if len(parts) > 1:
            raise RuntimeError(f"build_note_no_note_id_map currently only supports single-part score. Score {score_id}.xml (has_repeats: {has_repeats}) has {len(parts)} parts")
        
        curr_note_no = 1

        for i, part in enumerate(root.findall(".//part")):
            part_no = i + 1 

            for j, measure in enumerate(part.findall(".//measure")):
                measure_no = Utils.find_measure_no(measure)

                for k, note in enumerate(measure.findall(".//note")):
                    note_no = k + 1 
                    result[curr_note_no] = f"P{part_no}-{measure_no}-{note_no}"
                    curr_note_no += 1 

        return result 
    

    @staticmethod
    def filter_notes(xml_tree, voice:str, staff:str, is_chord:bool)->list:

        root = xml_tree.getroot()
        parts = root.findall(".//part")

        result = list()

        if len(parts) > 1:
            raise RuntimeError(f"filter_notes currently only supports single-part score")
    
        for i, part in enumerate(root.findall(".//part")):
            part_no = i + 1

            for j, measure in enumerate(part.findall(".//measure")):
                measure_no = int(measure.get("number"))

                if measure_no == -1:
                    continue

                note_no_in_measure = 1

                for _, note in enumerate(measure.findall(".//note")):
                    if note.find(".//rest") is not None:
                        continue

                    note_no = note_no_in_measure
                    note_id = f"P{part_no}-{measure_no}-{note_no}"

                    note_is_chord = False
                    note_staff = None
                    note_voice = None

                    for note_child in note:
                        if note_child.tag == "voice":
                            note_voice = note_child.text
                        if note_child.tag == "staff":
                            note_staff = note_child.text
                        if note_child.tag == "chord":
                            note_is_chord = True

                    if not note_staff or not note_voice:
                        print(f"filter_notes: note {note_id} does not have staff or voice")

                    # only check voice for right hand notes
                    if staff == "1":
                        if voice is not None and note_voice != voice:
                            continue

                    if staff is not None and note_staff != staff:
                        continue

                    if is_chord is not None and note_is_chord != is_chord:
                        continue

                    result.append(note_id)

                    note_no_in_measure += 1

        return result


    @staticmethod
    def is_note_identifier_in_range(i:str, start_note_identifier:str, end_note_identifier:str)->bool:
        if not len(i.split("_")) == 2:
            Utils.logger.error(f"is_note_identifier_in_range: invalid note identifier {i}")
            return False 
        
        if not len(start_note_identifier.split("_")) == 2:
            Utils.logger.error(f"is_note_identifier_in_range: invalid start_note_identifier {start_note_identifier}")
            return False 
        
        if not len(end_note_identifier.split("_")) == 2:
            Utils.logger.error(f"is_note_identifier_in_range: invalid end_note_identifier {end_note_identifier}")
            return False 
        
        return int(start_note_identifier.split("_")[1]) <= int(i.split("_")[1]) < int(end_note_identifier.split("_")[1])
    

    # FIXME currently only supports staff = 1, voice = 1
    # TODO skipping counting last note's duration
    @staticmethod
    def find_musical_duration_between_note_ids(start_note_id:str, end_note_id:str, score_id:str, tree_cache=None, has_repeats:bool=False):
        if not tree_cache:
            score_xml = f"{score_id}.xml" if not has_repeats else f"unnested_{score_id}.xml"
            tree_cache = ET.parse(f"{Constants.TMP_DIR}/{score_xml}")

        root = tree_cache.getroot()

        total_durations = 0
        counting = False
        counting_done = False

        for i, part in enumerate(root.findall(".//part")):
            part_no = i + 1

            for j, measure in enumerate(part.findall(".//measure")):
                measure_no = Utils.find_measure_no(measure)

                for k, note in enumerate(measure.findall(".//note")):
                    note_no = k + 1

                    note_id = f"P{part_no}-{measure_no}-{note_no}"                
                    is_chord_note = False
                    staff = None 
                    voice = None 
                    duration = None 

                    for note_child in note:
                        if note_child.tag == "staff":
                            staff = int(note_child.text)

                        if note_child.tag == "voice":
                            voice = int(note_child.text)

                        if note_child.tag == "chord":
                            is_chord_note = True 

                        if note_child.tag == "duration":
                            duration = int(note_child.text)

                    if note_id == start_note_id:
                        counting = True 

                    if note_id == end_note_id:
                        counting = False 
                        counting_done = True
                        break

                    if counting:
                        if staff == 1 and voice == 1 and not is_chord_note:
                            total_durations += duration or 0
                
                if counting_done:
                    break
            
            if counting_done: 
                break
        
        return total_durations
    

    @staticmethod
    def find_measure_no(measure)->int:
        if not measure:
            raise RuntimeError(f"find_measure_no: invalid measure {measure}")
        
        if not "number" in measure.attrib:
            raise RuntimeError(f"find_measure_no: node {str(measure)} does have number, investigate!")
        
        if measure.attrib.get("number").startswith("X"):
            # implicit measure
            Utils.logger.warning(f"find_measure_no: implicit measure {measure.attrib.get('number')}")
            return measure.attrib.get("number")

        return int(measure.attrib.get("number"))
    
    @staticmethod
    def find_normalized_diff(a:float, b:float)->float:
        if a is None or b is None:
            return -1
        
        if a == b:
            return 1.0

        abs_diff = abs(a - b)
        max_possible_diff = max(abs(a), abs(b))
        
        normalized_diff = abs_diff / max_possible_diff
        
        score = 1.0 - normalized_diff
        
        return score
    
    # TODO add support for nested scores
    @staticmethod
    def generate_piano_roll_from_xml(score_id:str, has_repeats:bool=False)->bool:
        piano_roll_result = subprocess.run(
            [
                "./MusicXMLToPianoRoll.sh",
                score_id if not has_repeats else f"unnested_{score_id}"
            ],
            stdout=subprocess.PIPE,  
            stderr=subprocess.PIPE, 
            check=True, 
            text=True, 
            cwd="./AlignmentTool"
        )

        Utils.logger.info(f"generate_piano_roll_from_xml: stdout for piano_roll_result for score_id {score_id}: {piano_roll_result.stdout}")

        if has_repeats:
            if os.path.exists(f"{Constants.TMP_DIR}/unnested_{score_id}_hmm.txt"):
                os.rename(f"{Constants.TMP_DIR}/unnested_{score_id}_hmm.txt", f"{Constants.TMP_DIR}/{score_id}_hmm.txt")
                os.rename(f"{Constants.TMP_DIR}/unnested_{score_id}_fmt3x.txt", f"{Constants.TMP_DIR}/{score_id}_fmt3x.txt")
                Utils.upload_file(f"{score_id}_hmm.txt")
                Utils.upload_file(f"{score_id}_fmt3x.txt")
                return True 
            else:
                Utils.logger.error(f"generate_piano_roll_from_xml: failed to generate hmm file for unnested score unnested_{score_id}, investigate!")
                return False
            
        else:

            if os.path.exists(f"{Constants.TMP_DIR}/{score_id}_hmm.txt"):
                Utils.upload_file(f"{score_id}_hmm.txt")
                Utils.upload_file(f"{score_id}_fmt3x.txt")
                return True 
            else:
                Utils.logger.error(f"generate_piano_roll_from_xml: failed to generate hmm file for score {score_id}, investigate!")
                return False

    
    @staticmethod
    def merge_intervals(intervals:list)->list:
        if not intervals:
            return []

        # Sort the array on the basis of start values of intervals.
        intervals.sort()
        stack = []
        # insert first interval into stack
        stack.append(intervals[0])
        for i in intervals[1:]:
            # Check for overlapping interval,
            # if interval overlap
            if stack[-1][0] <= i[0] <= stack[-1][-1]:
                stack[-1][-1] = max(stack[-1][-1], i[-1])
            else:
                stack.append(i)
    
        return stack
    
    @staticmethod
    def build_id_map(dict_list:list, id_key:str="_id")->dict:
        result = dict()
        for d in dict_list:
            if not d.get(id_key):
                raise RuntimeError(f"build_id_map: invalid list entry {str(d)}")
            
            result[str(d[id_key])] = d
        return result 

    # TODO remove and use stored scores from SegmentComparisonReport
    @staticmethod
    def calculate_score(onset_time_trend_right_player:float, onset_time_trend_right_master:float, corr_right:float):
        onset_time_trend_score = Utils.find_normalized_diff(onset_time_trend_right_player, onset_time_trend_right_master)

        corr_right_score = 1 if corr_right >= 0.5 else 0.75

        return onset_time_trend_score * 0.5 + corr_right_score * 0.5


    @staticmethod
    def calculate_score_w_pedal(onset_time_trend_right_player:float, onset_time_trend_right_master:float, corr_right:float, num_sus_pedal_event_player:int, num_sus_pedal_event_master:int):
        onset_time_trend_score = Utils.find_normalized_diff(onset_time_trend_right_player, onset_time_trend_right_master)

        pedal_score = Utils.find_normalized_diff(num_sus_pedal_event_player, num_sus_pedal_event_master)
        corr_right_score = 1 if corr_right >= 0.5 else 0.75

        return (onset_time_trend_score + pedal_score + corr_right_score) / 3
    
    @staticmethod
    def calculate_score_dynamics_only(dynamics_trend_player:float, dynamics_trend_master:float):
        # FIXME this score may be negative
        return Utils.find_normalized_diff(dynamics_trend_player, dynamics_trend_master)
    
    # Function to add commas between the key-value pairs
    @staticmethod
    def fix_json_string(json_string):
        # Find the positions where commas should be added
        json_string = json_string.replace("```json", "").replace("```", "")

        positions = []
        inside_quotes = False
        for i in range(len(json_string) - 1):
            if json_string[i] == '"':
                inside_quotes = not inside_quotes
            if not inside_quotes and json_string[i] == '"' and json_string[i+1] in {" ", "\n"}:
                positions.append(i + 1)
        
        # Add commas at the identified positions
        fixed_json_list = list(json_string)

        if positions:
            for pos in reversed(positions[:-1]):
                fixed_json_list.insert(pos, ',')
            
            return ''.join(fixed_json_list)

        return json_string
    
    @staticmethod
    def get_first_last_measure(xml_tree)->tuple:
        root = xml_tree.getroot()
        parts = root.findall(".//part")
        if len(parts) > 1:
            raise RuntimeError(f"get_first_last_note currently only supports single-part score")

        measures = parts[0].findall(".//measure")
        first_measure = int(measures[0].get("number"))
        last_measure = int(measures[-1].get("number"))

        return first_measure, last_measure

    # TODO handle //DuplicateOnsets
    @staticmethod
    def get_measure_no_num_notes_map(score_id:str)->dict:
        duplicate_onsets = list()
        seen_duplicate_onsets = list()

        result = dict()
        Utils.download_file_to_tmp_dir(f"{score_id}_hmm.txt")

        with open(f"{Constants.TMP_DIR}/{score_id}_hmm.txt", "r") as f:
            for line in f:

                if line.startswith("//DuplicateOnsets:"):
                    d = set()
                    parts = line.split("\t")

                    for p in reversed(parts):
                        p_parts = p.split("-")
                        if len(p_parts) == 3:
                            d.add(p)
            
                    duplicate_onsets.append(d)

                elif not line.startswith("//"):
                
                    parts = line.split("\t")
                    for p in reversed(parts):
                        p_parts = p.split("-")
                        if len(p_parts) == 3:

                            # check if note ID is already seen in seen_duplicate_onsets
                            is_seen_duplicate = False
                            for s in seen_duplicate_onsets:
                                if p in s:
                                    is_seen_duplicate = True 
                                    break

                            if is_seen_duplicate:
                                continue

                            for s in duplicate_onsets:
                                if p in s:
                                    seen_duplicate_onsets.append(s)
                                    break
                        
                            measure_no = p_parts[1]
                            if measure_no in result.keys():
                                result[measure_no] += 1
                            else:
                                result[measure_no] = 1

        return result

    @staticmethod
    def find_first_key_for_value(map:dict, v:str, throw_err:bool=True):
        for key, val in map.items():
            if val == v:
                return key 

        if not throw_err:
            return -1 
        else:
            raise RuntimeError(f"find_first_key_for_value: value {v} not found in provided map {str(map)}, investigate!") 
                        
    @staticmethod
    def find_last_key_for_value(map:dict, v:str):
        result = None
        for key, val in map.items():
            if val == v:
                result = key 

        if not result:
            raise RuntimeError(f"find_last_key_for_value: value {v} not found in provided map {str(map)}, investigate!")

        return result
    
    @staticmethod
    def convert_decimal_to_seconds(decimal_time:float):
        # Split the number into integer (minutes) and fractional (fractional minutes) parts
        minutes = int(decimal_time)  # Get the integer part, representing minutes
        fractional_minutes = decimal_time - minutes  # Calculate the fractional part
        
        # Convert fractional minutes to seconds
        seconds_from_fraction = fractional_minutes * 100  # Convert to seconds
        
        # Calculate total seconds
        total_seconds = minutes * 60 + seconds_from_fraction
        
        return total_seconds
                
    @staticmethod
    def is_strictly_ascending(lst):
        for i in range(1, len(lst)):
            if lst[i] <= lst[i - 1]:
                return False
        return True
    

    @staticmethod
    def convert_to_unnested_measures(score:dict, original_start:int, original_end:int)->tuple:
        if score.get("unnested_original_measure_map") and len(score["unnested_original_measure_map"]) > 1:  
            is_end_on_repeated_end = False

            for range in score["repeated_measure_ranges"]:
                if original_end == range[1]:
                    is_end_on_repeated_end = True 
                    break

            if is_end_on_repeated_end:
                return int(Utils.find_first_key_for_value(score["unnested_original_measure_map"], str(original_start))), int(Utils.find_last_key_for_value(score["unnested_original_measure_map"], str(original_end)))
            
            else:
                return int(Utils.find_first_key_for_value(score["unnested_original_measure_map"], str(original_start))), int(Utils.find_first_key_for_value(score["unnested_original_measure_map"], str(original_end)))


        else:
            return original_start, original_end
        

    @staticmethod
    def find_between_note_ids(start_note_id:str, end_note_id:str, from_note_ids:list, note_id_note_no_map:OrderedDict, include_start:bool=True, include_end:bool=True)->list:
        start_note_no = note_id_note_no_map[start_note_id]
        end_note_no = note_id_note_no_map[end_note_id]

        result = []
        for note_id in from_note_ids:
            note_no = note_id_note_no_map[note_id]
        
            if include_start and include_end:
                if start_note_no <= note_no <= end_note_no:
                    result.append(note_id)

            elif include_start:
                if start_note_no <= note_no < end_note_no:
                    result.append(note_id)
        
            elif include_end:
                if start_note_no < note_no <= end_note_no:
                    result.append(note_id)

            else:
                if start_note_no < note_no < end_note_no:
                    result.append(note_id)

        return result
    
    @staticmethod
    def build_note_id_note_xml_node_map(xml_tree)->OrderedDict:
        root = xml_tree.getroot()
        parts = root.findall(".//part")

        result = OrderedDict()

        if len(parts) > 1:
            raise RuntimeError(f"build_note_id_note_xml_node_map currently only supports single-part score")

        for i, part in enumerate(root.findall(".//part")):
            part_no = i + 1

            for j, measure in enumerate(part.findall(".//measure")):
                measure_no = measure.get("number")

                for k, note in enumerate(measure.findall(".//note")):
                    # skip rest notes
                    if note.find(".//rest") is not None:
                        continue

                    note_no = k + 1
                    note_id = f"P{part_no}-{measure_no}-{note_no}"
                    result[note_id] = note

        return result
        
    
    @staticmethod
    def build_note_no_note_id_maps(xml_tree)->tuple:
        root = xml_tree.getroot()
        parts = root.findall(".//part")

        note_no_note_id_map = OrderedDict()
        note_id_note_no_map = OrderedDict()

        if len(parts) > 1:
            raise RuntimeError(f"build_note_no_note_id_maps currently only supports single-part score")
    
        curr_note_no = 1

        for i, part in enumerate(root.findall(".//part")):
            part_no = i + 1

            for j, measure in enumerate(part.findall(".//measure")):
                measure_no = measure.get("number")

                curr_note_no_in_measure = 1

                for _, note in enumerate(measure.findall(".//note")):
                    # skip rest notes
                    if note.find(".//rest") is not None:
                        continue

                    note_no = curr_note_no_in_measure
                    note_no_note_id_map[curr_note_no] = f"P{part_no}-{measure_no}-{note_no}"
                    note_id_note_no_map[f"P{part_no}-{measure_no}-{note_no}"] = curr_note_no
                    curr_note_no += 1
                    curr_note_no_in_measure += 1

        return note_no_note_id_map, note_id_note_no_map
    

    @staticmethod
    def find_last_note_id_in_measure(note_id_note_no_map:OrderedDict, measure:int, last_measure:int)->str:
        true_measure = measure
        if measure > last_measure:
            true_measure = last_measure
        
        target_note_id = f"P1-{true_measure}-1"

        while target_note_id not in note_id_note_no_map.keys() and true_measure < last_measure:
            true_measure += 1
            target_note_id = f"P1-{true_measure}-1"

        return target_note_id if target_note_id in note_id_note_no_map.keys() else None

    @staticmethod
    def find_first_note_id_in_measure(note_id_note_no_map:OrderedDict, measure:int, first_measure:int=1)->str:

        true_measure = measure
        if true_measure < first_measure:
            true_measure = first_measure

        target_note_id = f"P1-{true_measure}-1"

        while target_note_id not in note_id_note_no_map.keys() and true_measure > first_measure:
            true_measure -= 1
            target_note_id = f"P1-{true_measure}-1"

        return target_note_id if target_note_id in note_id_note_no_map.keys() else None
    
    @staticmethod
    def search_for_consecutive_sequences(lst, min_squence_size, max_gap=1):
        consecutive_sequences = []

        curr_gap = 0
        while not consecutive_sequences and curr_gap <= max_gap:
            consecutive_sequences = Utils.find_consecutive_sequences_in_list(lst, max_gap, min_squence_size)
            print(f"search_for_consecutive_sequences: {len(consecutive_sequences)} consecutive sequences found with max_gap {max_gap}, min_sequence_size {min_squence_size}")
            curr_gap += 1

        return consecutive_sequences

    @staticmethod
    def find_consecutive_sequences_in_list(lst, max_gap, min_sequence_size):
        if not lst:
            return []

        sequences = []
        current_sequence = [lst[0]]

        for i in range(1, len(lst)):
            if lst[i] - lst[i - 1] <= max_gap + 1:
                current_sequence.append(lst[i])
            else:
                if len(current_sequence) >= min_sequence_size:
                    sequences.append(current_sequence)
                current_sequence = [lst[i]]
    
        if len(current_sequence) >= min_sequence_size:
            sequences.append(current_sequence)
    
        return sequences




    

        
            

    

        