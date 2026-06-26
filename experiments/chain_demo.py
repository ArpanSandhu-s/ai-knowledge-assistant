from langchain_ollama import ChatOllama

# ====================================
# Load Local Ollama Model
# ====================================

llm = ChatOllama(
    model="gemma3:latest",
    temperature=0
)

# ====================================
# Step 1: Cleaner
# ====================================

def clean_text(text):
    prompt = f"""
You are a text cleaner.

Clean the following text:
- Remove excessive punctuation
- Remove repetition
- Fix formatting

Text:
{text}

Return only the cleaned text.
"""

    return llm.invoke(prompt).content


# ====================================
# Step 2: Summarizer
# ====================================

def summarize(text):
    prompt = f"""
Summarize the following text in one sentence.

Text:
{text}
"""

    return llm.invoke(prompt).content


# ====================================
# Step 3: Answerer
# ====================================

def answer(summary):
    prompt = f"""
Answer the user's concern based on the summary below.

Summary:
{summary}

Provide a helpful answer.
"""

    return llm.invoke(prompt).content


# ====================================
# Step 4: Critic
# ====================================

def critic(answer_text):
    prompt = f"""
Review the following answer.

Check:
- Accuracy
- Clarity
- Completeness

Answer:
{answer_text}

Provide a short review.
"""

    return llm.invoke(prompt).content


# ====================================
# User Input
# ====================================

user_input = """
OMG!!!! AI IS TAKING OVER THE WORLD!!!!!!
WHAT IS HAPPENING???????
"""


# ====================================
# Run Chain
# ====================================

print("\nRunning Chain...\n")

cleaned = clean_text(user_input)

summary = summarize(cleaned)

final_answer = answer(summary)

review = critic(final_answer)


# ====================================
# Display Results
# ====================================

print("=" * 60)
print("STEP 1 : CLEANED TEXT")
print("=" * 60)
print(cleaned)

print("\n" + "=" * 60)
print("STEP 2 : SUMMARY")
print("=" * 60)
print(summary)

print("\n" + "=" * 60)
print("STEP 3 : ANSWER")
print("=" * 60)
print(final_answer)

print("\n" + "=" * 60)
print("STEP 4 : CRITIC REVIEW")
print("=" * 60)
print(review)