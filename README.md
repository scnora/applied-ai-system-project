# PawPal+ 🐾 — AI-Enhanced Pet Care Planner


**Original project name:** PawPal+ (Modules 1–3)

PawPal+ was built as a Streamlit app to help busy pet owners manage daily care tasks across multiple pets. The original system allowed users to enter owner and pet information, add care tasks with priorities and durations, and generate a daily schedule using a rule-based `Scheduler` class. It included smart features like medical priority boosting, conflict detection, automatic task recurrence, and chronological sorting 
---

<video src="/assets/pawpet.mp4" width="400" controls></video>


## Title and Summary

**PawPal+ with RAG-powered Health Q&A**

This module adds a Retrieval-Augmented Generation (RAG) feature to the original PawPal+ scheduler. When a pet owner types a health question about their pet (e.g. *"why is my dog so tired after walks?"*), the system retrieves that pet's logged tasks, medical conditions, breed, and species from the existing data model — and passes all of it to Claude as context before generating a response. This means the AI never answers generically; it always answers with *your specific pet's data* in front of it.

This matters because general pet health advice can be misleading or even harmful if it ignores a pet's individual profile. A dog with arthritis needs very different guidance than a healthy puppy, and RAG makes that distinction automatic.

---

## Architecture Overview

The system follows a four-stage RAG pipeline:

1. **User input** — the owner types a natural language question about their pet in the Streamlit UI.
2. **Retrieval** — the app pulls two sources of context: (a) the pet's existing logged data (`tasks`, `medical_conditions`, `breed`, `age`, `species`) directly from the `Pet` dataclass, and (b) a static breed/species knowledge base stored in `pawpal_knowledge.py`.
3. **Generation** — both the retrieved context and the original question are injected into a structured prompt sent to the Claude API. Claude generates a response grounded in the pet's actual profile.
4. **Human review** — the owner reads the response and decides whether to act on it. No action is taken automatically; the owner is always the final decision-maker.


<img src="/assets/image.png" alt="Alt text" width="200">
---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/scnora/applied-ai-system-project.git
cd applied-ai-system-project
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` includes:
```
streamlit>=1.30
pytest>=7.0
anthropic
```


### 4. Run the Streamlit app

```bash
streamlit run app.py
```

### 5. Run the tests

```bash
python -m pytest tests/ -v
```

---

## Sample Interactions

### Example 1 — Dog with a medical condition

**Pet profile:** Mochi, 3-year-old Shiba Inu, medical condition: arthritis. Recent tasks: morning walk (20 min), joint medication (5 min).

**User question:**
> "Why does Mochi seem tired after walks? Should I be worried?"

**AI response (paraphrased):**
> Based on Mochi's profile, the tiredness after walks is likely related to the arthritis diagnosis on record. Shiba Inus are generally energetic, but joint inflammation causes fatigue faster than in healthy dogs. The 20-minute morning walk logged in the schedule is a reasonable duration — you might monitor whether symptoms worsen after longer sessions. It's worth raising at the next vet visit. **This is not a substitute for professional veterinary advice.**

---

### Example 2 — Cat with no medical conditions

**Pet profile:** Luna, 5-year-old Siamese cat. Recent tasks: morning feeding, evening enrichment play.

**User question:**
> "Luna has been drinking a lot more water lately. Is that normal?"

**AI response (paraphrased):**
> Increased water intake in cats — especially Siamese, who are prone to kidney and thyroid issues — can sometimes be an early sign worth monitoring. Luna's logs don't show any current medical conditions, which is a good sign, but this is one of those symptoms that warrants a vet check rather than a wait-and-see approach. You could log a vet visit task in the scheduler to stay on top of it.

---

### Example 3 — General care question

**Pet profile:** Mochi, Shiba Inu, arthritis.

**User question:**
> "What's a good enrichment activity for Mochi that won't stress his joints?"

**AI response (paraphrased):**
> Given Mochi's arthritis, high-impact activities like fetch or agility courses are best avoided. Low-strain enrichment works well for Shibas — nose work games, sniff walks (where the dog leads at their own pace), and puzzle feeders are all great options that engage the brain without putting stress on the joints. These can be added as enrichment tasks in the scheduler.

---

## Design Decisions

**Why RAG instead of a fine-tuned model?**
The pet data already exists in structured Python dataclasses (`Pet`, `Task`). Retrieving it at query time and injecting it into a prompt was the most direct path to personalized answers — no training data, no model hosting, and no re-training needed when a pet's profile changes.

**Why a static knowledge base instead of a vector database?**
For the scope of this project, a Python dictionary in `pawpal_knowledge.py` covering common breeds and species is sufficient and keeps the setup simple. A vector database (like ChromaDB or Pinecone) would be the right upgrade if the knowledge base grew to hundreds of entries.

**Why keep the human review step?**
Pet health information is sensitive. The system is designed to inform, not to prescribe. Keeping the owner as the final decision-maker reduces the risk of the AI being treated as a vet, and aligns with responsible AI design.

**Trade-off: context window size vs. detail**
The current implementation passes all of a pet's tasks as context. For pets with very long task histories, this could approach token limits. A future improvement would be to retrieve only the most recent or most relevant tasks rather than the full list.

---

## Testing Summary

**What worked:**
- The core scheduling logic tests all pass: task completion, priority sorting, conflict detection, recurrence, and filtering all behave as expected.
- The RAG prompt reliably includes the pet's medical conditions in responses when they are present in the profile.
- Claude correctly declines to give definitive medical diagnoses and consistently recommends consulting a vet for serious symptoms.

**What didn't work / limitations:**
- The AI occasionally gives advice that is slightly generic when the breed is uncommon or not in the knowledge base. Adding more breed entries would improve this.
- There is no automated test for the AI response content itself — verifying that the response mentions the pet's name or condition requires a manual check.
- Edge case: if a user adds a pet but no tasks yet, the retrieved context is sparse, and the AI response is less personalized.

**What I learned:**
- Prompt structure matters more than prompt length. A clearly labeled context block ("Here is the pet's profile: ...") produced better responses than dumping all the data as a paragraph.
- Testing AI outputs is fundamentally different from testing deterministic code. Consistency checks (does the response always mention the condition?) are more practical than exact-match assertions.

---

## Reflection

Building this project made the difference between a chatbot and a RAG system feel very concrete. Before, "retrieval-augmented generation" sounded abstract — after wiring up the retriever to pull from the existing `Pet` dataclass and watching Claude give a different answer for a dog with arthritis versus a healthy dog, the mechanism clicked.

The most surprising lesson was how much the quality of retrieved context affects the quality of the response. When the context was vague ("the dog has some health issues"), the response was vague. When it was specific ("Mochi, 3-year-old Shiba Inu, arthritis, 20-min morning walks"), the response was noticeably more useful and actionable.

It also reinforced that AI in a real product is not just a model — it's a pipeline. The retriever, the prompt structure, the output validation, and the human review step are all part of the system. Getting any one of them wrong degrades the whole experience, even if the model itself is excellent.