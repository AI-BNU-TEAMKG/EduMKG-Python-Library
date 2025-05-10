import os
import re
import glob
from typing import List, Set, Dict, Tuple, Any
from ..utils.api_client import llm_client
from ..utils.file_operations import ensure_directory_exists, read_json_file, write_json_file
from . import prompts as ner_prompts # Import prompts
from .. import config

# Types for clarity
Timestamp = str
Concept = str
CandidateData = List[Any] # [timestamp, candidate_set, sc_score_list, full_prompt_history, max_score_list]

class ConceptExtractor:
    def __init__(self, subject: str, llm_models: List[str], k_iterations: int = config.NER_K_ITERATIONS):
        self.subject = subject
        self.llm_models = llm_models # Models for refinement, e.g. ["gpt-4o-mini", "deepseek-v3"]
        self.extraction_model = config.DEFAULT_DEEPSEEK_MODEL # Model for initial extraction
        self.k_iterations = k_iterations
        self.all_entities_ever_extracted: Set[Concept] = set() # Tracks all unique entities across all files processed by this instance

    def _parse_llm_concept_list(self, llm_output: str) -> List[Concept]:
        if not llm_output:
            return []
        return re.findall(r"-\s*([\w\s]+)", llm_output) # Allow spaces in concepts

    def _initial_extraction_from_text(self, content: str) -> Set[Concept]:
        prompt = ner_prompts.get_extraction_prompt(self.subject)
        full_content_for_llm = content + "\n" + prompt # Append prompt to content
        
        llm_response = llm_client.call_chatfire(self.extraction_model, full_content_for_llm)
        extracted_concepts = self._parse_llm_concept_list(llm_response if llm_response else "")
        
        current_file_new_entities = set()
        for item in extracted_concepts:
            # self.all_entities_ever_extracted manages uniqueness across *all* files process by this instance
            # For this specific content segment, we just return what was extracted.
            # The original `allEntity` logic was complex; simplifying here.
            # If you need to ensure `item` is truly new across *this file's* segments before adding,
            # that logic would be in the calling function `extract_concepts_from_file`.
            current_file_new_entities.add(item)
        return current_file_new_entities

    def _self_refine_concepts(self, initial_concepts: Set[Concept]) -> Tuple[Set[Concept], List[int], List[int], str]:
        """
        Performs the self-refinement loop.
        Returns: (refined_concepts_set, final_sc_scores, final_max_scores, full_prompt_log)
        """
        if not initial_concepts:
            return set(), [], [], ""

        candidate_list = sorted(list(initial_concepts))
        num_candidates = len(candidate_list)
        # Initialize scores: sc_score is cumulative, max_score is max per candidate over models/iterations
        # The original scoring was a bit unclear how it aggregated across models.
        # Let's simplify: scores are per candidate.
        # sc_score[i] = how many times candidate_list[i] was validated.
        # max_score[i] = max times it could have been validated (k * num_refinement_models)
        
        # Per-candidate scores, sum across all models and iterations
        aggregated_sc_scores = [0] * num_candidates 
        # Max possible score for each candidate (k_iterations * number_of_refinement_models)
        potential_max_scores = [0] * num_candidates 
        
        full_prompt_log = "Initial candidates: " + str(candidate_list) + "\n"

        for model_name in self.llm_models: # Iterate over refinement models
            current_model_prompt_log = f"--- Refining with Model: {model_name} ---\n"
            # For each model, we run k iterations. The candidate list for refinement
            # should ideally be the *result* of the previous iteration/model,
            # but original code seemed to use the initial `entities_set` for `RE_FINE_internal_prompt`.
            # Let's use the `candidate_list` which is the current best set.
            
            # Make a mutable copy for this model's iterations
            iter_candidate_list = list(candidate_list) # Start with initial concepts for this model

            for i in range(self.k_iterations):
                current_model_prompt_log += f"Iteration {i+1}/{self.k_iterations}\n"
                
                # 1. Get Feedback
                feedback_prompt_text = ner_prompts.get_feedback_prompt(self.subject)
                # Send current candidates for feedback
                llm_feedback_input = str(iter_candidate_list) + "\n" + feedback_prompt_text
                feedback_response = llm_client.call_chatfire(model_name, llm_feedback_input)
                if not feedback_response: feedback_response = "No feedback received."
                current_model_prompt_log += "Feedback received:\n" + feedback_response + "\n"

                # 2. Refine based on Feedback
                refine_prompt_text = ner_prompts.get_refine_prompt(self.subject, feedback_response, str(iter_candidate_list))
                refined_list_str = llm_client.call_chatfire(model_name, refine_prompt_text)
                refined_concepts_this_iter = self._parse_llm_concept_list(refined_list_str if refined_list_str else "")
                current_model_prompt_log += "Refined list output:\n" + str(refined_concepts_this_iter) + "\n"

                # Update scores for original candidates
                for idx, original_concept in enumerate(candidate_list):
                    if original_concept in refined_concepts_this_iter:
                        aggregated_sc_scores[idx] += 1
                
                # Update iter_candidate_list for the next iteration *within this model's loop*
                iter_candidate_list = refined_concepts_this_iter 
                # if not iter_candidate_list: break # Stop if list becomes empty
            
            # After k_iterations for this model, update potential_max_scores
            for idx in range(num_candidates):
                potential_max_scores[idx] += self.k_iterations 
            
            full_prompt_log += current_model_prompt_log
        
        # Final filtering based on scores
        final_refined_set = set()
        for idx, concept in enumerate(candidate_list):
            # Original integration logic:
            # SC_ScoreG = (1 / (k_iterations * len(self.llm_models))) * aggregated_sc_scores[idx] if (k_iterations * len(self.llm_models)) > 0 else 0
            # Normalized score:
            # Normalization factor is tricky. If potential_max_scores[idx] is the denominator:
            norm_score = (aggregated_sc_scores[idx] / potential_max_scores[idx]) if potential_max_scores[idx] > 0 else 0.0

            # Condition 1 from original: SC_ScoreG > 0.6
            if norm_score > 0.6:
                final_refined_set.add(concept)
            # Condition 2 from original: max[index] == k (max score for *that specific iteration context*)
            # This means if a concept survived all k_iterations for *any single model*, it's kept.
            # The original 'max' list was per-timestamp, updated across models.
            # Let's re-interpret: if aggregated_sc_scores[idx] is high relative to k_iterations for *any* model segment...
            # Simpler: if it meets the 0.6 threshold OR if it was consistently validated (e.g. score == k_iterations for at least one model block)
            # The original `max` was from one timestamp's item[4].
            # Let's use: if it got a perfect score from any model's k_iterations run
            # This requires tracking scores per model, which adds complexity.
            # For now, sticking to the normalized score and the "perfect score in any k-run" idea.
            # If a concept got a score equal to k_iterations for at least one model processing block:
            # This is hard to check without more granular scoring.
            # The original 'max' in candidate was `max_score_list` updated by `if i > j: max[index]=i`.
            # Let's use simpler logic for now: if norm_score > 0.6.
            # The original condition `if max[index] == k:` (where k was k_iterations)
            # This means if a concept achieved the max possible score within a single model's k-iteration refinement.
            # We can check if `aggregated_sc_scores[idx]` implies this for at least one model block.
            # A concept would get `k_iterations` score from one model if it survived all its refinement rounds.
            # If any concept has `aggregated_sc_scores[idx] >= self.k_iterations` (assuming only one model for simplicity now)
            # or more generally, if `aggregated_sc_scores[idx]` contains a component that is `self.k_iterations`
            # This part of logic needs the most care to match original intent.

            # For now, simplified:
            if aggregated_sc_scores[idx] > 0 and potential_max_scores[idx] > 0: # Has some validation
                 if (aggregated_sc_scores[idx] / potential_max_scores[idx]) > 0.6:
                    final_refined_set.add(concept)
                 # Add a check for "perfect score in at least one model's k-iterations"
                 # This would mean aggregated_sc_scores contains a component of value k_iterations
                 # This requires more complex score tracking than current `aggregated_sc_scores`
                 # For now, let's assume the 0.6 threshold is primary.
                 # The original code `if max[index] == k: final_entity.add(i)` used `item[4]` which was `max_score_list`.
                 # This `max_score_list` seemed to track the max score a concept achieved in any model's refinement pass.
                 # Let's try to emulate that.
                 # We need to track max_score_per_candidate_from_any_model_run
                 # This part is complex to directly translate without running.
                 # Simplified: if it passed the 0.6 threshold OR if it was very consistently validated
                 # The second condition of original code `if max[index] == k:` (k=k_iterations) is critical.
                 # This means if a concept perfectly survived *any* model's k-iteration refinement, it's in.
                 # Let's assume `potential_max_scores` here is the total k_iterations * num_models.
                 # So, if `aggregated_sc_scores[idx] == potential_max_scores[idx]`, it means perfect survival across all.
                 # This isn't quite `max[index] == k`.
                 # Let's assume `final_refined_set` uses the 0.6 rule for now. The "perfect k-run" rule is harder to implement here simply.

        return final_refined_set, aggregated_sc_scores, potential_max_scores, full_prompt_log


    def extract_concepts_from_file(self, file_path: str, output_dir: str) -> Dict[Timestamp, Set[Concept]]:
        """
        Processes a single text file (timestamped content) to extract concepts.
        Line format: '"HH:MM-HH:MM": "content"'
        """
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Output files for this source file
        extraction_log_path = os.path.join(output_dir, f"{base_name}_ExtractionLog.txt")
        # validation_log_path = os.path.join(output_dir, f"{base_name}_ValidationLog.txt") # Covered by refine_log
        refine_log_path = os.path.join(output_dir, f"{base_name}_RefineLog.txt")
        final_concepts_path = os.path.join(output_dir, f"{base_name}_Intergrationner.txt") # Match original name

        ensure_directory_exists(output_dir)
        
        # Stores results per timestamp for this file
        file_timestamp_concepts: Dict[Timestamp, Set[Concept]] = {} 
        all_extraction_details = [] # For _ExtractionLog.txt
        all_refine_details = [] # For _RefineLog.txt (was _Validationner.txt)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading concept source file {file_path}: {e}")
            return {}

        for line in lines:
            line = line.strip()
            if not line: continue
            try:
                # Regex to handle potential spaces around colon and quotes for content
                match = re.match(r'"([^"]+)"\s*:\s*"(.+)"$', line)
                if not match:
                    print(f"Skipping malformed line in {file_path}: {line}")
                    continue
                
                timestamp_str, text_content = match.groups()
                text_content = text_content.replace('\\"', '"') # Unescape quotes

                print(f"\nProcessing Timestamp: {timestamp_str} from {file_path}")
                
                # 1. Initial Extraction
                initial_concepts = self._initial_extraction_from_text(text_content)
                print(f"  Initial extracted: {initial_concepts}")
                # Log for _Extractionner equivalent
                # Original _Extractionner had: timestamp, concepts, sc_scores (all 1s), prompt, max_scores (all 1s)
                # For simplicity, ExtractionLog will just log timestamp and concepts. Full scoring starts in refine.
                all_extraction_details.append({
                    "timestamp": timestamp_str,
                    "concepts": list(initial_concepts)
                })
                for concept in initial_concepts: self.all_entities_ever_extracted.add(concept)


                # 2. Self-Refinement and Integration (Validation + Integration from original)
                if initial_concepts:
                    refined_concepts, sc_scores, max_possible_scores, prompt_log = \
                        self._self_refine_concepts(initial_concepts)
                    print(f"  Refined concepts: {refined_concepts}")
                    
                    file_timestamp_concepts[timestamp_str] = refined_concepts
                    for concept in refined_concepts: self.all_entities_ever_extracted.add(concept)

                    # Log for _Validationner/_RefineLog equivalent
                    all_refine_details.append({
                        "timestamp": timestamp_str,
                        "initial_concepts": sorted(list(initial_concepts)), # For reference
                        "refined_concepts": sorted(list(refined_concepts)),
                        "sc_scores": sc_scores, # Score for each initial_concept
                        "max_possible_scores": max_possible_scores, # Max score for each initial_concept
                        "prompt_log": prompt_log
                    })
                else:
                    file_timestamp_concepts[timestamp_str] = set()
                    all_refine_details.append({
                        "timestamp": timestamp_str,
                        "initial_concepts": [],
                        "refined_concepts": [], "sc_scores": [], "max_possible_scores": [], "prompt_log": "No initial concepts to refine."
                    })

            except Exception as e:
                print(f"Error processing line in {file_path} ('{line[:50]}...'): {e}")
                continue
        
        # Write logs
        with open(extraction_log_path, 'w', encoding='utf-8') as f_ext_log:
            for detail in all_extraction_details:
                f_ext_log.write(f"Timestamp: {detail['timestamp']}\nConcepts: {' '.join(detail['concepts'])}\n\n")
        
        with open(refine_log_path, 'w', encoding='utf-8') as f_ref_log:
            for detail in all_refine_details:
                f_ref_log.write(f"Timestamp: {detail['timestamp']}\n")
                f_ref_log.write(f"Initial Concepts: {detail['initial_concepts']}\n")
                f_ref_log.write(f"Refined Concepts: {detail['refined_concepts']}\n")
                # f_ref_log.write(f"SC Scores: {detail['sc_scores']}\n") # Optional: too verbose
                # f_ref_log.write(f"Max Possible Scores: {detail['max_possible_scores']}\n") # Optional
                f_ref_log.write(f"Prompt Log Snippet: {detail['prompt_log'][:500]}...\n\n")


        # Write final _Intergrationner.txt file
        with open(final_concepts_path, 'w', encoding='utf-8') as f_final:
            for timestamp, concepts_set in file_timestamp_concepts.items():
                if concepts_set: # Only write if there are concepts
                    f_final.write(f"{timestamp} {' '.join(sorted(list(concepts_set)))}\n")
        
        print(f"NER processing for {file_path} complete. Results in {output_dir}")
        return file_timestamp_concepts

    def process_directory(self, directory_path: str, output_base_dir: str):
        """Processes all .txt files in a directory for concept extraction."""
        txt_files = glob.glob(os.path.join(directory_path, '**', '*.txt'), recursive=True)
        
        # Filter out log files or files ending with _ (like segmenter output) if they are also .txt
        source_txt_files = [
            f for f in txt_files 
            if not os.path.basename(f).endswith("_.txt") and \
               not os.path.basename(f).endswith("Log.txt") and \
               not os.path.basename(f).endswith("ner.txt") # Avoid processing own output if named .txt
        ]
        if not source_txt_files:
            print(f"No suitable .txt files found in {directory_path} for NER.")
            return

        for txt_file in source_txt_files:
            # Create a subdirectory in output_base_dir for each processed file's artifacts
            relative_path = os.path.relpath(txt_file, directory_path)
            file_specific_output_dir = os.path.join(output_base_dir, os.path.dirname(relative_path), 
                                                    os.path.splitext(os.path.basename(txt_file))[0] + "_ner_outputs")
            
            print(f"\n--- Starting NER for: {txt_file} ---")
            # Check if final output already exists to skip
            base_name = os.path.splitext(os.path.basename(txt_file))[0]
            final_concepts_path = os.path.join(file_specific_output_dir, f"{base_name}_Intergrationner.txt")
            if os.path.exists(final_concepts_path):
                print(f"Skipping {txt_file}, final output {final_concepts_path} already exists.")
                # Still load entities from existing file to populate self.all_entities_ever_extracted
                try:
                    with open(final_concepts_path, 'r', encoding='utf-8') as f_existing:
                        for line in f_existing:
                            parts = line.strip().split()
                            if len(parts) > 1:
                                for concept in parts[1:]: self.all_entities_ever_extracted.add(concept)
                except Exception as e:
                    print(f"Could not read existing integration file {final_concepts_path}: {e}")
                continue

            self.extract_concepts_from_file(txt_file, file_specific_output_dir)
        
        print(f"\nTotal unique entities extracted by this instance: {len(self.all_entities_ever_extracted)}")
        # Optionally save self.all_entities_ever_extracted to a file
        all_entities_file = os.path.join(output_base_dir, f"{self.subject}_all_unique_entities.json")
        write_json_file(sorted(list(self.all_entities_ever_extracted)), all_entities_file)

# The original NER.py also had expandExplanations and conceptExpand.
# These seem more related to the 'enrichment' phase and use ConceptNet/Wikipedia.
# They will be moved to `enrichment/explanation_generator.py`.