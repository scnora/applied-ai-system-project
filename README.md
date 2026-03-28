# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

PawPal+ goes beyond a basic task list with several algorithmic features built into the `Scheduler` class: <br>

Conflict detection — `detect_conflicts()` checks if multiple tasks are assigned to the same time slot and returns a simple warning for each overlap. It doesn’t change anything in the schedule, instead it just flags the issue so you can decide what to do. <br>

Chronological sorting — `sort_by_time()` makes sure tasks are ordered from earliest to latest. It uses a simple trick with "HH:MM" time strings so they naturally sort in the correct order. <br>

Filtering— `filter_by_pet(name)` and `filter_by_completion(bool)` Makes it so you can filter tasks by pet or by completion status using filter_by_pet() and filter_by_completion(). These don’t modify the original list, but they just give you a filtered view. <br>

Automatic recurrence —  When you complete a task, `mark_task_complete()` can automatically create the next one. Daily tasks get pushed to tomorrow, weekly tasks to next week, and “as-needed” tasks don’t repeat. The new task is added back to the pet so it shows up in future schedules. <br>

Medical priority boost — If a pet has a medical condition, their medication tasks automatically get bumped up in priority (up to a max of 5). This makes sure important care doesn’t get pushed aside by less urgent tasks. <br>

---

## Testing PawPal+

### Run the tests

```bash
python -m pytest tests/ -v
```

### What the tests cover

test_task_completion<br>
Makes sure calling complete() actually updates the task from not done → done. <br>

test_add_task_increases_pet_task_count<br>
Confirms that when you add a task to a pet, it’s really stored (count goes from 0 to 1).<br>

test_sort_by_time_returns_chronological_order<br>
Checks that even if tasks are added out of order, they come back sorted from earliest to latest.

test_recurrence_creates_next_day_task<br>
Verifies that completing a daily task both marks it done and creates a new one for the next day.<br>


test_detect_conflicts_flags_duplicate_slots<br>
Ensures that two tasks in the same time slot trigger a conflict warning, while a single task does not.<br>

### Confidence level 4/5

The main features are all tested and working—task completion, managing tasks for pets, sorting, handling recurring tasks, and detecting conflicts.

The only reason it’s not a full 5 is because some edge cases aren’t covered yet. For example: what happens if the owner has no time available, if every time slot is already filled, or if a weekly task is completed multiple times in one day. The system likely handles these, but they just aren’t tested yet.
---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
