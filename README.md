# StudyPath — AI Agent for Under-Resourced Students

**Track:** Agents for Good | Kaggle AI Agents Intensive Capstone 2026

## Problem

Students without access to career counselors, paid courses, or mentors
struggle to turn a learning goal into a structured, trackable plan. They
either give up from overwhelm or follow generic advice that doesn't adapt
to their actual progress.

## Solution

StudyPath is an AI agent that takes a student's goal, skill level, and
available study time, then generates a personalized 7-day study plan —
and *adapts* that plan based on what the student actually struggled with,
session after session.

## Architecture — 4 Agentic Concepts Demonstrated

1. **Planning Agent** — decomposes the goal into phases and a 7-day plan
   using visible chain-of-thought reasoning (shown in output, not hidden).
2. **Tool Use** — two real Python functions are called by the agent:
   - `compute_spaced_repetition_dates()` — calculates a 1/3/7/14-day
     review schedule from real calendar dates.
   - `fetch_free_resources()` — matches topics against a curated database
     of real, free learning resources (Kaggle Learn, FreeCodeCamp, MDN,
     PyTorch docs, etc.) and returns direct URLs.
3. **Memory / State** — student profile and daily progress logs persist
   in a local JSON file (`student_state.json`) and are read back in on
   the next session, so the plan adapts instead of starting fresh.
4. **Evaluator / Guardrail Agent** — a second LLM call audits the draft
   plan for cognitive overload (too much content for the available hours)
   and vagueness (generic tasks), then outputs a revised, integrated
   final plan. This self-critique is shown visibly in the output.

## Setup Instructions

### Prerequisites
- Python 3.11+
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Installation

```bash
git clone https://github.com/SanthoshJ007/ai-study-mentor-capstone.git
cd ai-study-mentor-capstone
pip install google-genai pydantic python-dotenv
```

### Configure your API key

Create a `.env` file in the project root:

```bash
echo "GEMINI_API_KEY=your_key_here" > .env
```

### Run the demo

```bash
python3 demo.py
```

This runs two contrasting student profiles (a beginner learning Python
basics, and an advanced student building a PyTorch image classifier),
then demonstrates the memory/adaptation system by logging a struggle
for Student A and showing how Day 2 onwards adapts in response.

## Example Output

The demo prints, for each session:
- The Planning Agent's chain-of-thought reasoning
- A 7-day schedule with specific practice tasks
- A computed spaced-repetition table
- Curated free resource links
- The Evaluator Agent's self-critique and final adjustments

State is saved to `student_a_state.json` and `student_b_state.json`
(git-ignored — these regenerate fresh on each run).

## Future Improvements

- Web UI instead of terminal output
- Persistent cloud-hosted memory (currently local JSON)
- Multi-student dashboard for educators/mentors to track several students
- Integration with real course platforms (Khan Academy, Coursera APIs)
  for live progress syncing instead of manual logs

## License

MIT

