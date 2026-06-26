import os
import sys
from studypath import StudyPathAgent

def check_env():
    """Verify that GEMINI_API_KEY is configured."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("=" * 60)
        print("ERROR: GEMINI_API_KEY environment variable is not set!")
        print("Please set it in your environment. Example:")
        print("  export GEMINI_API_KEY='your-gemini-api-key'")
        print("=" * 60)
        sys.exit(1)
    return api_key

def clean_state_files():
    """Removes prior state files to start fresh."""
    for filename in ["student_a_state.json", "student_b_state.json"]:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Error removing {filename}: {e}")

def main():
    api_key = check_env()
    clean_state_files()

    print("=" * 80)
    print("                     STARTING STUDYPATH AGENT DEMONSTRATION")
    print("=" * 80)
    print("\nStudyPath is designed for under-resourced students. It implements:")
    print("  1. PLANNING AGENT (with visible Chain-of-Thought reasoning)")
    print("  2. TOOL USE (spaced-repetition calendar date calculator & free resource fetcher)")
    print("  3. MEMORY / STATE (JSON state tracking, adapts to progress/struggles)")
    print("  4. EVALUATOR / GUARDRAIL (reviews draft plan, checks for cognitive load & vagueness)")
    print("=" * 80)

    # ----------------------------------------------------
    # PROFILE 1: STUDENT A (Beginner, Python Basics, 1 hr/day)
    # ----------------------------------------------------
    print("\n[STUDENT A SESSION 1] - BEGINNER, PYTHON BASICS, 1 HOUR/DAY")
    print("=" * 60)
    
    agent_a = StudyPathAgent(api_key=api_key, state_file="student_a_state.json")
    
    goal_a = "Learn basic Python programming: variables, lists, loops, functions, and dictionary fundamentals."
    level_a = "beginner"
    hours_a = 1.0

    plan_a = agent_a.run_session(goal=goal_a, level=level_a, hours_per_day=hours_a)
    print(plan_a)
    print("=" * 60)

    # ----------------------------------------------------
    # PROFILE 2: STUDENT B (Advanced, PyTorch Deep Learning, 4 hrs/day)
    # ----------------------------------------------------
    print("\n[STUDENT B SESSION 1] - ADVANCED, PYTORCH DEEP LEARNING, 4 HOURS/DAY")
    print("=" * 60)
    
    agent_b = StudyPathAgent(api_key=api_key, state_file="student_b_state.json")
    
    goal_b = "Build a Deep Learning image classifier using PyTorch from scratch, covering CNN architectures, training loops, and data loaders."
    level_b = "advanced"
    hours_b = 4.0

    plan_b = agent_b.run_session(goal=goal_b, level=level_b, hours_per_day=hours_b)
    print(plan_b)
    print("=" * 60)

    # ----------------------------------------------------
    # MEMORY & ADAPTATION DEMO (Student A logs struggle on Day 1)
    # ----------------------------------------------------
    print("\n[STUDENT A SESSION 2] - LOGGING PROGRESS & TRIGGERING ADAPTIVE MEMORY")
    print("=" * 60)
    print("Student A logs their progress for Day 1:")
    print("  'I completed variables and lists, but loops are extremely confusing. I didn't finish the loop practice task.'")
    print("Let's see how StudyPath's memory system adapts Day 2 onwards to focus more on loops and reviews.")
    print("=" * 60)

    progress_log = "I completed variables and lists, but loops are extremely confusing. I didn't finish the loop practice task."
    
    # Re-run Session for Student A with the prior day's log
    adapted_plan_a = agent_a.run_session(
        goal=goal_a, 
        level=level_a, 
        hours_per_day=hours_a, 
        previous_day_log=progress_log
    )
    print(adapted_plan_a)
    print("=" * 60)

    print("\nDEMO COMPLETED SUCCESSFULLY!")
    print("Check student_a_state.json and student_b_state.json for persisted state memory files.")
    print("=" * 80)

if __name__ == "__main__":
    main()
