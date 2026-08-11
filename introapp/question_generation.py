from groq import Groq


# -----------------------------------------
# Initialize Groq Client
# -----------------------------------------
client = client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Interrogation Question Generator
# -----------------------------------------
def generate_interrogation_questions(
    scenario: str,
    num_questions: int,
    temperature: float = 0.6
):
    """
    Generates continuation-based interrogation questions
    with NO reasoning, NO <think>, NO explanations.
    """

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert criminal interrogation AI.\n"
                "STRICT OUTPUT RULES:\n"
                "- Output ONLY ONE interrogation question.\n"
                "- Do NOT explain.\n"
                "- Do NOT reason.\n"
                "- Do NOT include <think>.\n"
                "- Each question must logically continue.\n"
                "- Increase pressure progressively."
            )
        },
        {
            "role": "user",
            "content": (
                f"Scenario:\n{scenario}\n\n"
                "Generate the first interrogation question."
            )
        }
    ]

    questions = []

    for i in range(num_questions):
        stream = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=messages,
            temperature=temperature,
            top_p=0.95,
            max_completion_tokens=100,
            reasoning_effort="none",   # 🔥 THIS IS THE KEY FIX
            stream=True
        ) 

        question_text = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                question_text += delta

        question_text = question_text.strip()
        questions.append(question_text)

        # Save assistant response
        messages.append({
            "role": "assistant",
            "content": question_text
        })

        # Ask for continuation
        messages.append({
            "role": "user",
            "content": (
                "Generate the next interrogation question. "
                "It must directly follow the previous one. "
                "Output ONLY the question."
            )
        })

    return questions




# -----------------------------------------
# MAIN EXECUTION
# -----------------------------------------
if __name__ == "__main__":

    scenario = """
    A suspect is being questioned about their whereabouts during a warehouse robbery
    that occurred at 11:30 PM. CCTV footage places a person of similar appearance near
    the location, but the suspect claims to have been at home.
    """

    num_questions = 5

    questions = generate_interrogation_questions(
        scenario=scenario,
        num_questions=num_questions
    )

    print("\n--- Interrogation Questions ---\n")
    for idx, q in enumerate(questions, start=1):
        print(f"Q{idx}: {q}\n")