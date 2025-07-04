"""Progress calculation helper for multi-stage document processing."""

from enum import Enum


class ProcessingStages(Enum):
    """Document processing stages with their progress ranges."""
    TEXT_EXTRACTION = (0.0, 0.33)      # 0% - 33%
    EMBEDDING_GENERATION = (0.33, 0.66) # 33% - 66%
    SUMMARY_GENERATION = (0.66, 1.0)    # 66% - 100%


def calculate_global_progress(stage: ProcessingStages, local_progress: float) -> float:
    """
    Calculate global progress based on current stage and local progress.
    
    Args:
        stage: Current processing stage
        local_progress: Progress within the current stage (0.0 to 1.0)
        
    Returns:
        Global progress (0.0 to 1.0)
    """
    # Clamp local progress to 0-1 range
    local_progress = max(0.0, min(1.0, local_progress))
    
    # Get stage range
    start, end = stage.value
    
    # Calculate global progress
    stage_range = end - start
    global_progress = start + (stage_range * local_progress)
    
    return global_progress


def get_stage_info(global_progress: float) -> tuple[ProcessingStages, float]:
    """
    Determine current stage and local progress from global progress.
    
    Args:
        global_progress: Global progress (0.0 to 1.0)
        
    Returns:
        Tuple of (current_stage, local_progress)
    """
    for stage in ProcessingStages:
        start, end = stage.value
        if start <= global_progress <= end:
            # Calculate local progress within this stage
            stage_range = end - start
            local_progress = (global_progress - start) / stage_range
            return stage, local_progress
    
    # Default to last stage if progress > 1.0
    return ProcessingStages.SUMMARY_GENERATION, 1.0