# fsm/state_registry.py

import os
import importlib
from session_states import S


def load_state_handlers():
    """
    Dynamically load all state handlers from the fsm/states/ directory.
    
    Returns:
        dict: Mapping of State enum values to their handler functions
    """
    state_table = {}
    
    # Get the directory where this file is located
    current_dir = os.path.dirname(__file__)
    states_dir = os.path.join(current_dir, "states")
    
    # Mapping of state names to their enum values
    # This allows us to match filenames like "intro.py" to S.INTRO
    state_mapping = {
        "intro": S.INTRO,
        "pockets": S.POCKETS_Q,
        "confession_inquiry": S.CONFESSION_INQUIRY,
        "confession_record": S.CONFESSION_RECORD,
        "confession_record_and_transcribe": S.CONFESSION_RECORD_AND_TRANSCRIBE,
        "post_confession_info_request": S.POST_CONFESSION_INFO_REQUEST,
        "post_confession_info_record": S.POST_CONFESSION_INFO_RECORD,
        "ready_to_go_inquiry": S.READY_TO_GO_INQUIRY,
    }
    
    # Auto-discover and load handlers
    for filename in os.listdir(states_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            # Get the module name without .py extension
            module_name = filename[:-3]
            
            # Skip if we don't have a mapping for this state
            if module_name not in state_mapping:
                print(f"Warning: Found state file '{filename}' but no corresponding enum mapping")
                continue
            
            try:
                # Import the module
                module = importlib.import_module(f"fsm.states.{module_name}")
                
                # Get the handler function (assumes naming convention: handle_<state>)
                handler_name = f"handle_{module_name}"
                if hasattr(module, handler_name):
                    handler_func = getattr(module, handler_name)
                    state_enum = state_mapping[module_name]
                    state_table[state_enum] = handler_func
                    print(f"Loaded state handler: {state_enum.name} -> {handler_name}")
                else:
                    print(f"Warning: Module '{module_name}' does not have handler function '{handler_name}'")
                    
            except ImportError as e:
                print(f"Failed to import state module '{module_name}': {e}")
                continue
    
    return state_table 