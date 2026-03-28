from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, TaskType, Scheduler, ScheduledTask


def test_task_completion():
    """Calling complete() should flip is_completed from False to True."""
    task = Task(
        name="Morning Medication",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=5,
    )

    assert task.is_completed is False  # starts incomplete
    task.complete()
    assert task.is_completed is True   # flipped after complete()


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)

    assert len(pet.tasks) == 0  # starts with no tasks

    pet.add_task(Task(
        name="Morning Walk",
        task_type=TaskType.WALK,
        duration_minutes=20,
        priority=4,
    ))

    assert len(pet.tasks) == 1  # one task added


# ── Helper: build a minimal Owner + Scheduler with tasks already slotted ──────
def _make_scheduler_with_slots(slots: list[tuple[str, str, str]]) -> Scheduler:
    """
    Build a Scheduler whose daily_plan is pre-populated without calling
    generate_daily_plan(). Each tuple is (task_name, pet_name, time_slot).
    This isolates the tests from scheduling logic — we only test the method
    under test, not the whole pipeline.
    """
    owner = Owner(name="Test Owner")
    pet = Pet(name="TestPet", species="dog", breed="Mixed", age=2)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    for task_name, _, time_slot in slots:
        task = Task(
            name=task_name,
            task_type=TaskType.OTHER,
            duration_minutes=10,
            priority=3,
        )
        task.scheduled_time = time_slot
        # ScheduledTask pairs the task with a slot and an explanation string
        scheduled = ScheduledTask(task=task, scheduled_time=time_slot,
                                  pet=pet, reason="test")
        scheduler.daily_plan.append(scheduled)

    return scheduler


def test_sort_by_time_returns_chronological_order():
    """sort_by_time() must return tasks earliest-to-latest regardless of insertion order."""
    # Tasks are added in reverse order on purpose to prove sorting isn't
    # just reflecting insertion order.
    scheduler = _make_scheduler_with_slots([
        ("Evening Task",   "TestPet", "19:00"),
        ("Morning Task",   "TestPet", "07:00"),
        ("Afternoon Task", "TestPet", "13:00"),
    ])

    sorted_plan = scheduler.sort_by_time()

    # Extract the scheduled times from the result in the order they came back
    times = [st.scheduled_time for st in sorted_plan]

    # Each time must be less than or equal to the next — i.e. ascending order
    assert times == sorted(times), f"Expected ascending order but got {times}"


def test_recurrence_creates_next_day_task():
    """mark_task_complete() on a daily task must add a new Task due tomorrow."""
    owner = Owner(name="Test Owner")
    pet = Pet(name="TestPet", species="dog", breed="Mixed", age=2)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    today = date.today()
    task = Task(
        name="Daily Medication",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=5,
        frequency="daily",   # this is what triggers recurrence
        due_date=today,
    )
    task.scheduled_time = "08:00"
    pet.add_task(task)

    # Wrap the task in a ScheduledTask so mark_task_complete() can reference the pet
    scheduled = ScheduledTask(task=task, scheduled_time="08:00", pet=pet, reason="test")

    task_count_before = len(pet.tasks)          # should be 1
    scheduler.mark_task_complete(scheduled)     # completes task + queues next occurrence
    task_count_after = len(pet.tasks)           # should be 2

    assert task.is_completed is True, "Original task should be marked complete"
    assert task_count_after == task_count_before + 1, "A new task should have been added"

    # The new task's due_date must be exactly one day after today
    new_task = pet.tasks[-1]
    assert new_task.due_date == today + timedelta(days=1), (
        f"Expected due date {today + timedelta(days=1)}, got {new_task.due_date}"
    )


def test_detect_conflicts_flags_duplicate_slots():
    """detect_conflicts() must return a warning when two tasks share a time slot."""
    scheduler = _make_scheduler_with_slots([
        ("Walk",      "TestPet", "09:00"),
        ("Grooming",  "TestPet", "09:00"),  # ← deliberate duplicate
        ("Feeding",   "TestPet", "12:00"),  # no conflict
    ])

    warnings = scheduler.detect_conflicts()

    # Exactly one conflict slot (09:00) — the 12:00 task is alone so no warning
    assert len(warnings) == 1, f"Expected 1 conflict warning, got {len(warnings)}"

    # The warning text must mention the conflicting slot
    assert "09:00" in warnings[0], "Warning should identify the conflicting slot"
