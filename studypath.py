import os
import json
import datetime
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


# ==========================================
# 1. MEMORY & STATE SYSTEM
# ==========================================

class StudentState:
    """
    Manages the persistent state of the student.
    Stores their goal, level, hours per day, the current day of the plan,
    and a history of daily progress logs to support adaptive memory.
    """
    def __init__(self, state_file="student_state.json"):
        self.state_file = state_file
        self.goal = ""
        self.current_level = ""
        self.hours_per_day = 1.0
        self.current_day = 1
        self.history_logs = []  # list of {"day": int, "log": str, "adapted": bool}
        self.current_plan = ""
        self.spaced_repetition = ""
        self.resources = ""

    def load(self):
        """Loads state from JSON file if it exists."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.goal = data.get("goal", "")
                    self.current_level = data.get("current_level", "")
                    self.hours_per_day = data.get("hours_per_day", 1.0)
                    self.current_day = data.get("current_day", 1)
                    self.history_logs = data.get("history_logs", [])
                    self.current_plan = data.get("current_plan", "")
                    self.spaced_repetition = data.get("spaced_repetition", "")
                    self.resources = data.get("resources", "")
            except Exception as e:
                print(f"Warning: Could not load state file: {e}")

    def save(self):
        """Saves current state to JSON file."""
        data = {
            "goal": self.goal,
            "current_level": self.current_level,
            "hours_per_day": self.hours_per_day,
            "current_day": self.current_day,
            "history_logs": self.history_logs,
            "current_plan": self.current_plan,
            "spaced_repetition": self.spaced_repetition,
            "resources": self.resources,
        }
        try:
            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state file: {e}")

    def log_progress(self, day_num: int, log_text: str):
        """Logs student's progress for a day and increments the day counter."""
        self.history_logs.append({
            "day": day_num,
            "log": log_text,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self.current_day = day_num + 1
        self.save()


# ==========================================
# 2. LOCAL AGENTIC TOOLS
# ==========================================

def compute_spaced_repetition_dates(start_date_str: str, topics: list[str]) -> str:
    """
    Tool: Computes a spaced-repetition schedule (1-day, 3-day, 7-day, 14-day review offsets)
    from a starting date for a list of topics.
    Returns a formatted Markdown table.
    """
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        start_date = datetime.datetime.today()

    intervals = [1, 3, 7, 14]
    lines = []
    lines.append("| Day Learned | Topic | Review 1 (Day+1) | Review 2 (Day+3) | Review 3 (Day+7) | Review 4 (Day+14) |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

    for i, topic in enumerate(topics):
        learned_date = start_date + datetime.timedelta(days=i)
        learned_str = learned_date.strftime("%Y-%m-%d")
        
        row = f"| **Day {i+1}** ({learned_date.strftime('%b %d')}) | {topic} |"
        for interval in intervals:
            review_date = learned_date + datetime.timedelta(days=interval)
            row += f" {review_date.strftime('%b %d')} |"
        lines.append(row)

    return "\n".join(lines)


def fetch_free_resources(topics: list[str]) -> str:
    """
    Tool: Matches plan topics against a high-quality local curated database of
    100% free educational platforms (FreeCodeCamp, MDN, Kaggle, Fast.ai, etc.)
    and returns direct, real URLs (never generic placeholders).
    """
    db = {
        "python": [
            {"name": "Python for Everybody (FreeCodeCamp)", "url": "https://www.freecodecamp.org/news/python-for-everybody-dataset-course/"},
            {"name": "Official Python Tutorial", "url": "https://docs.python.org/3/tutorial/"},
            {"name": "Kaggle Python Course", "url": "https://www.kaggle.com/learn/python"}
        ],
        "pandas": [
            {"name": "Kaggle Pandas Course", "url": "https://www.kaggle.com/learn/pandas"},
            {"name": "Pandas Getting Started Guide", "url": "https://pandas.pydata.org/docs/getting_started/index.html"}
        ],
        "machine learning": [
            {"name": "Kaggle Intro to Machine Learning", "url": "https://www.kaggle.com/learn/intro-to-machine-learning"},
            {"name": "Fast.ai Practical Deep Learning for Coders", "url": "https://course.fast.ai/"}
        ],
        "pytorch": [
            {"name": "PyTorch Official Tutorials", "url": "https://pytorch.org/tutorials/"},
            {"name": "PyTorch for Deep Learning (FreeCodeCamp)", "url": "https://www.freecodecamp.org/news/learn-pytorch-for-deep-learning-in-day/"}
        ],
        "tensorflow": [
            {"name": "TensorFlow Core Tutorials", "url": "https://www.tensorflow.org/tutorials/pages"}
        ],
        "deep learning": [
            {"name": "Fast.ai Deep Learning Course", "url": "https://course.fast.ai/"},
            {"name": "MIT OpenCourseWare Deep Learning", "url": "https://ocw.mit.edu/courses/res-9-001-mit-deep-learning-clinic-spring-2020/"}
        ],
        "html": [
            {"name": "MDN Web Docs HTML Guide", "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML"},
            {"name": "Responsive Web Design (FreeCodeCamp)", "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/"}
        ],
        "css": [
            {"name": "MDN Web Docs CSS Guide", "url": "https://developer.mozilla.org/en-US/docs/Learn/CSS"},
            {"name": "CSS Grid & Flexbox (FreeCodeCamp)", "url": "https://www.freecodecamp.org/news/css-grid-vs-flexbox-infographic/"}
        ],
        "javascript": [
            {"name": "MDN Web Docs JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"},
            {"name": "JavaScript Algorithms & Data Structures (FreeCodeCamp)", "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/"}
        ],
        "sql": [
            {"name": "Kaggle SQL Courses", "url": "https://www.kaggle.com/learn/intro-to-sql"},
            {"name": "SQLZoo Interactive Tutorials", "url": "https://sqlzoo.net/"}
        ],
        "git": [
            {"name": "GitHub Git Guides", "url": "https://training.github.com/"},
            {"name": "Git & GitHub Crash Course (FreeCodeCamp)", "url": "https://www.freecodecamp.org/news/git-and-github-crash-course/"}
        ],
        "data visualization": [
            {"name": "Kaggle Data Visualization", "url": "https://www.kaggle.com/learn/data-visualization"}
        ]
    }

    general_resources = [
        {"name": "FreeCodeCamp Learn Platform", "url": "https://www.freecodecamp.org/learn/"},
        {"name": "Kaggle Learn Hub", "url": "https://www.kaggle.com/learn"},
        {"name": "Khan Academy Computer Science", "url": "https://www.khanacademy.org/computing"},
        {"name": "MIT OpenCourseWare Computer Science", "url": "https://ocw.mit.edu/departments/electrical-engineering-and-computer-science/"}
    ]

    matched_urls = []
    seen = set()

    for topic in topics:
        topic_lower = topic.lower()
        matched_any = False
        for key, res_list in db.items():
            if key in topic_lower or topic_lower in key:
                for res in res_list:
                    if res["url"] not in seen:
                        matched_urls.append(res)
                        seen.add(res["url"])
                        matched_any = True
        
    # If no specific matches or too few, pad with general high-quality resources
    if len(matched_urls) < 3:
        for res in general_resources:
            if res["url"] not in seen and len(matched_urls) < 5:
                matched_urls.append(res)
                seen.add(res["url"])

    output = ["### Recommended Free Resources (100% Free & Open-Access)"]
    for res in matched_urls:
        output.append(f"- **[{res['name']}]({res['url']})**: High-quality tutorials and interactive modules.")
    
    return "\n".join(output)


# ==========================================
# 3. STUDYPATH ORCHESTRATOR
# ==========================================

class StudyPathAgent:
    """
    Orchestrator for the StudyPath Agent.
    Handles the execution flow: State Loading -> Planning -> Tool calls -> Evaluation -> Final Output.
    """
    def __init__(self, api_key: str = None, state_file: str = "student_state.json"):
        # Initialize Gemini Client using the new Google GenAI SDK
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment variables.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.state = StudentState(state_file)
        # We use gemini-2.5-flash as the standard, fast, capable model
        self.model_name = "gemini-2.5-flash"

    def run_session(self, goal: str, level: str, hours_per_day: float, previous_day_log: str = None) -> str:
        """
        Executes a study planning/updating session.
        If previous_day_log is provided, it updates memory/state and adapts the plan.
        """
        self.state.load()
        
        # Capture profile details
        self.state.goal = goal
        self.state.current_level = level
        self.state.hours_per_day = hours_per_day

        # Update progress log if student provides history
        if previous_day_log:
            day_just_finished = self.state.current_day
            self.state.log_progress(day_just_finished, previous_day_log)
            print(f"\n--- [Memory Event] Logged Day {day_just_finished} Progress: '{previous_day_log}' ---")
            print(f"--- [Memory Event] Incrementing active target day to Day {self.state.current_day} ---\n")

        self.state.save()

        # Step 1: Planning Agent creates the draft plan
        print("--- [Agent Action] Planning Agent generating Draft Study Plan (CoT) ---")
        draft_plan, extracted_topics = self._call_planning_agent()
        
        print(f"--- [Agent Action] Planner output complete. Extracted Topics: {extracted_topics} ---")

        # Step 2: Call tools on the extracted topics
        print("--- [Agent Action] Executing local-friendly calendar and resource tools ---")
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        spaced_rep_schedule = compute_spaced_repetition_dates(today_str, extracted_topics)
        resources_list = fetch_free_resources(extracted_topics)

        # Step 3: Evaluator reviews the draft plan and tools output, then revises
        print("--- [Agent Action] Evaluator Agent reviewing draft & resources for load limit and specificity ---")
        final_output = self._call_evaluator_agent(draft_plan, spaced_rep_schedule, resources_list)
        
        # Save plan elements back to state
        self.state.current_plan = final_output
        self.state.spaced_repetition = spaced_rep_schedule
        self.state.resources = resources_list
        self.state.save()

        print("--- [Agent Action] Session completed successfully. ---\n")
        return final_output

    def _call_planning_agent(self) -> tuple[str, list[str]]:
        """
        Calls the first LLM instance as the Planning Agent.
        Requires explicit Chain of Thought.
        Returns the raw markdown draft and a parsed list of daily topics.
        """
        # Read historical logs to allow adaptation
        history_context = ""
        if self.state.history_logs:
            history_context += "\nHere is the progress log of what the student did previously:\n"
            for log in self.state.history_logs:
                history_context += f"- Day {log['day']}: {log['log']}\n"
            history_context += f"The student is currently starting Day {self.state.current_day}. If they struggled or missed topics, adjust the remaining days of the plan to accommodate (e.g. review days or slower pace)."

        system_prompt = (
            "You are the Planning Agent for StudyPath, an elite career-transition study coach. "
            "Your job is to decompose a student's learning goal into a highly structured, realistic 7-day study plan. "
            "You MUST show your chain of thought reasoning first before generating the plan. "
            "You must adapt the plan specifically to their level, study hours, and historical progress log."
        )

        user_prompt = f"""
Goal: {self.state.goal}
Student Level: {self.state.current_level}
Available Study Time: {self.state.hours_per_day} hours/day
Current Day of study: Day {self.state.current_day}
{history_context}

Please generate the study plan. 

STRUCTURE REQUIREMENT:
1. Start your response with a section called '## Chain-of-Thought Planning Reasoning' where you explicitly analyze the goal, difficulty, time constraints, and adaptation requirements. Show your step-by-step logic.
2. Provide '## Course Phases' showing the overall milestones.
3. Provide a '## 7-Day Schedule'. For each day (Day 1 through Day 7), outline:
   - **Day X Theme**: [A brief title for the day's focus]
   - **Topic**: [Specific focus topic]
   - **Study Time Block**: [Realistic study blocks fitting their hours_per_day]
   - **Practice Task**: [A highly specific, hands-on, non-generic task or project problem]
4. End your plan with a raw JSON block called 'EXTRACTED_TOPICS' containing a list of exactly 7 strings representing the main topic for each day. This is critical for our calendar tools.
   Format:
   ```json
   {{"topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5", "Topic 6", "Topic 7"]}}
   ```
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )
        )
        
        content = response.text
        
        # Parse out topics list
        topics = []
        try:
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group(1))
                topics = json_data.get("topics", [])
            else:
                # Fallback simple line regex if JSON matching failed
                topics_lines = re.findall(r'"topics"\s*:\s*\[(.*?)\]', content, re.DOTALL)
                if topics_lines:
                    topics = [t.strip().strip('"') for t in topics_lines[0].split(",")]
        except Exception as e:
            print(f"Error parsing topics JSON: {e}")

        # If extraction failed, generate default topics from the goal
        if len(topics) < 7:
            topics = [f"Topic {i+1} for {self.state.goal}" for i in range(7)]
            # Clean up topics count
            topics = topics[:7]

        # Clean the EXTRACTED_TOPICS JSON block from the draft to keep it clean
        draft_clean = re.sub(r"EXTRACTED_TOPICS.*$", "", content, flags=re.DOTALL)

        return draft_clean, topics

    def _call_evaluator_agent(self, draft_plan: str, spaced_rep: str, resources: str) -> str:
        """
        Calls the second LLM instance as the Evaluator Agent (Guardrail step).
        Takes the draft, checks for overload and vagueness, critiques it, and outputs
        the final revised version containing the integrated tool outputs.
        """
        system_prompt = (
            "You are the Evaluator and Guardrail Agent for StudyPath. "
            "Your job is to audit draft study plans for educational quality, cognitive overload, and vagueness. "
            "You must ensure that the student is not overloaded (e.g., trying to learn deep learning from scratch in 1 hour/day), "
            "and that the practice tasks are highly actionable, specific, and level-appropriate. "
            "You will write a visible self-check critique and then output a revised, integrated plan that includes "
            "the computed spaced-repetition schedules and resource links."
        )

        user_prompt = f"""
Student Profile:
- Goal: {self.state.goal}
- Level: {self.state.current_level}
- Hours/Day: {self.state.hours_per_day}

Draft Study Plan:
{draft_plan}

Computed Spaced-Repetition Schedule:
{spaced_rep}

Curated Resource Links:
{resources}

Please critique the draft plan. 

Your response MUST follow this structure:
1. Start with a header: '## Evaluator Self-Critique & Guardrails Log'
   Under this, write a paragraph analyzing if the draft plan has any overload (too much for the available hours/day) or vagueness (generic practice tasks), and describe what you are changing to fix it.
2. Write a header: '## Adjustments Made'
   Detail a list of specific changes made (e.g. simplified Day 2 practice task, reduced scope of Day 4, integrated tool calendar).
3. Write a header: '## Final StudyPath Personalized Plan'
   Provide the full, revised, polished plan. Make sure it contains:
   - The original Chain of Thought Reasoning (so the student sees it).
   - The revised phases and 7-day schedule with highly concrete practice tasks.
   - The Spaced-Repetition table (exactly as computed by the tool).
   - The Curated Resource links (exactly as returned by the tool).
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
            )
        )
        return response.text
