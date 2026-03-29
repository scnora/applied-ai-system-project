import streamlit as st
from pawpal_system import Owner, Pet, Task, TaskType, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state vault ───────────────────────────────────────────────────────
# Initialise once; survives every rerun for the life of the browser session.
if "owner" not in st.session_state:
    st.session_state.owner = None   # created when the owner form is submitted

# ── Section 1: Owner setup ────────────────────────────────────────────────────
st.subheader("Owner Info")

with st.form("owner_form"):
    owner_name     = st.text_input("Your name", value="Jordan")
    available_time = st.number_input("Minutes available for pet care today",
                                     min_value=30, max_value=480, value=120)
    walk_pref      = st.selectbox("Preferred walk time",
                                  ["morning", "afternoon", "evening"])
    submitted = st.form_submit_button("Save Owner")

if submitted:
    # Owner.set_preference() stores owner-level constraints used by Scheduler
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes_per_day=int(available_time),
    )
    st.session_state.owner.set_preference("walk_time", walk_pref)
    st.success(f"Owner '{owner_name}' saved.")

if st.session_state.owner is None:
    st.info("Fill in your owner info above to get started.")
    st.stop()   # halts Streamlit rendering — nothing below this line executes

owner: Owner = st.session_state.owner  # safe: st.stop() guarantees this is not None

st.divider()

# ── Section 2: Add a Pet ──────────────────────────────────────────────────────
st.subheader("Add a Pet")

with st.form("pet_form"):
    pet_name   = st.text_input("Pet name", value="Mochi")
    species    = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    breed      = st.text_input("Breed", value="Mixed")
    age        = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    condition  = st.text_input("Medical condition (optional)", value="")
    add_pet    = st.form_submit_button("Add Pet")

if add_pet:
    new_pet = Pet(name=pet_name, species=species, breed=breed, age=int(age))
    if condition.strip():
        # Pet.add_medical_condition() records conditions that boost medication priority
        new_pet.add_medical_condition(condition.strip())
    # Owner.add_pet() registers the pet so Scheduler can see all pets at once
    owner.add_pet(new_pet)
    st.success(f"Added {pet_name} the {species}!")

if owner.pets:
    st.write("**Your pets:**")
    for p in owner.pets:
        conds = f"  _(conditions: {', '.join(p.medical_conditions)})_" if p.medical_conditions else ""
        st.markdown(f"- **{p.name}** — {p.species}, {p.breed}, age {p.age}{conds}")
else:
    st.info("No pets added yet.")

st.divider()

# ── Section 3: Add a Task ─────────────────────────────────────────────────────
st.subheader("Add a Task")

if not owner.pets:
    st.warning("Add at least one pet before adding tasks.")
else:
    with st.form("task_form"):
        target_pet    = st.selectbox("Assign to pet", [p.name for p in owner.pets])
        task_name     = st.text_input("Task name", value="Morning walk")
        task_type     = st.selectbox("Task type", [t.value for t in TaskType])
        duration      = st.number_input("Duration (minutes)", min_value=1,
                                        max_value=240, value=20)
        priority      = st.slider("Priority (1 = low, 5 = critical)", 1, 5, 3)
        preferred_time = st.selectbox("Preferred time",
                                      ["morning", "afternoon", "evening", "anytime"])
        frequency     = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        notes         = st.text_input("Notes (optional)", value="")
        add_task      = st.form_submit_button("Add Task")

    if add_task:
        new_task = Task(
            name=task_name,
            task_type=TaskType(task_type),
            duration_minutes=int(duration),
            priority=priority,
            preferred_time=preferred_time,
            frequency=frequency,
            notes=notes,
        )
        # Owner.add_event_to_schedule() calls Pet.add_task() then regenerates the plan
        pet_obj = next(p for p in owner.pets if p.name == target_pet)
        owner.add_event_to_schedule(new_task, pet_obj)
        st.success(f"Task '{task_name}' added to {target_pet}.")

    # Show all current tasks across every pet
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("**All current tasks:**")
        rows = [
            {
                "Pet":      pet.name,
                "Task":     task.name,
                "Type":     task.task_type.value,
                "Duration": f"{task.duration_minutes} min",
                "Priority": task.get_priority_label(),
                "Time":     task.preferred_time,
            }
            for task, pet in all_tasks
        ]
        st.table(rows)
    else:
        st.info("No tasks added yet.")

st.divider()

# ── Section 4: Generate Schedule ─────────────────────────────────────────────
st.subheader("Today's Schedule")

if st.button("Generate Schedule"):
    schedule = owner.get_schedule()   # Owner.get_schedule() → Scheduler.generate_daily_plan()
    scheduler = owner._scheduler

    if not schedule:
        st.warning("No tasks could be scheduled. Add tasks above first.")
    else:

        # ── Conflict warnings ─────────────────────────────────────────────────
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            for warning in conflicts:
                st.warning(f"⚠️ {warning}")
        else:
            st.success("No scheduling conflicts detected.")

        st.divider()

        # ── Filter controls ───────────────────────────────────────────────────
        pet_names   = ["All pets"] + [p.name for p in owner.pets]
        status_opts = ["All", "Pending", "Completed"]

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_pet = st.selectbox("Filter by pet", pet_names, key="filter_pet")
        with col_f2:
            selected_status = st.selectbox("Filter by status", status_opts, key="filter_status")

        # Apply filter_by_pet() from Scheduler
        if selected_pet != "All pets":
            filtered = scheduler.filter_by_pet(selected_pet)
        else:
            filtered = schedule

        # Apply filter_by_completion() from Scheduler
        if selected_status == "Pending":
            filtered = [st_task for st_task in filtered if not st_task.task.is_completed]
        elif selected_status == "Completed":
            filtered = [st_task for st_task in filtered if st_task.task.is_completed]

        # Always display in chronological order via sort_by_time()
        sorted_plan = sorted(filtered, key=lambda st_task: st_task.scheduled_time)

        st.caption(f"Showing {len(sorted_plan)} of {len(schedule)} task(s)")
        st.divider()

        # ── Schedule cards ────────────────────────────────────────────────────
        if not sorted_plan:
            st.info("No tasks match the current filters.")
        else:
            for st_task in sorted_plan:
                priority = st_task.task.priority
                # Color-code border by priority level
                if priority == 5:
                    badge = "🔴 Critical"
                elif priority == 4:
                    badge = "🟠 High"
                elif priority == 3:
                    badge = "🟡 Medium"
                else:
                    badge = "🟢 Low"

                status_icon = "✅" if st_task.task.is_completed else "🕐"

                with st.container(border=True):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(f"### {st_task.scheduled_time}")
                        st.caption(badge)
                    with col2:
                        st.markdown(
                            f"{status_icon} **{st_task.task.name}** — {st_task.pet_name}"
                        )
                        st.caption(
                            f"{st_task.task.task_type.value} · "
                            f"{st_task.task.duration_minutes} min · "
                            f"due {st_task.task.due_date} · "
                            f"repeats {st_task.task.frequency}"
                        )
                        st.markdown(f"_Reason: {st_task.reason}_")

        st.divider()

        # ── Summary table via st.table ────────────────────────────────────────
        with st.expander("View as table"):
            rows = [
                {
                    "Time":      s.scheduled_time,
                    "Pet":       s.pet_name,
                    "Task":      s.task.name,
                    "Type":      s.task.task_type.value,
                    "Duration":  f"{s.task.duration_minutes} min",
                    "Priority":  s.task.get_priority_label(),
                    "Frequency": s.task.frequency,
                    "Done":      "✅" if s.task.is_completed else "🕐",
                }
                for s in sorted_plan
            ]
            st.table(rows)

        # ── Full text explanation ─────────────────────────────────────────────
        with st.expander("Full plan explanation"):
            st.text(scheduler.explain_plan())
