import os
import anthropic
from pawpal_system import Pet
from pawpal_knowledge import BREED_KNOWLEDGE
from dotenv import load_dotenv
load_dotenv()

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def ask_pawpal_advisor(pet: Pet, question: str) -> str:
    recent_tasks = [
        f"{t.name} ({t.task_type.value})" for t in pet.tasks[-5:]
    ]

    breed_key = pet.breed.lower().strip()
    species_key = pet.species.lower().strip()
    breed_context = (
        BREED_KNOWLEDGE.get(breed_key)
        or BREED_KNOWLEDGE.get(species_key)
        or "No specific breed information available."
    )

    conditions_text = (
        ", ".join(pet.medical_conditions) if pet.medical_conditions else "None"
    )
    tasks_text = (
        "\n  - ".join(recent_tasks) if recent_tasks else "No recent tasks recorded."
    )

    prompt = f"""PET PROFILE
Name: {pet.name}
Species: {pet.species}
Breed: {pet.breed}
Age: {pet.age} year(s)
Medical conditions: {conditions_text}
Recent tasks:
  - {tasks_text}

BREED / SPECIES KNOWLEDGE
{breed_context}

USER QUESTION
{question}"""

    system_prompt = (
        "You are PawPal+, a knowledgeable and caring pet health assistant. "
        "When answering, always reference the specific pet's name, breed, age, and "
        "any medical conditions provided in the pet profile — never give generic advice "
        "without grounding it in the pet's individual data. Use the breed knowledge "
        "section to add relevant context. Keep your response concise and practical. "
        "Always end your response with: "
        "'⚠️ This is not a substitute for professional veterinary advice. "
        "Please consult your vet for any health concerns.'"
    )

    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as exc:
        return (
            f"Sorry, I couldn't reach the AI advisor right now. "
            f"Please check your ANTHROPIC_API_KEY and try again.\n\nError: {exc}"
        )
