"""
Main LiveKit Voice Agent for Usool al-Hadith
"""
import logging
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    RoomInputOptions,
)
from livekit.plugins import openai, silero

from rag_service import RAGService
from tools import HADITH_TOOLS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HadithVoiceAgent:
    """Voice agent logic for teaching Usool al-Hadith"""

    def __init__(self):
        """Initialize the agent with RAG service"""
        self.rag_service = RAGService()

        # Get agent configuration from environment
        self.agent_name = os.getenv("AGENT_NAME", "Sheikh Abdullah")
        self.agent_personality = os.getenv(
            "AGENT_PERSONALITY",
            "You are a knowledgeable Islamic scholar specializing in Hadith sciences."
        )

    def create_initial_context(self) -> llm.ChatContext:
        """
        Create the initial chat context with system instructions

        Returns:
            Initial ChatContext for the agent
        """
        system_message = f"""You are {self.agent_name}, {self.agent_personality}

Your expertise is in Usool al-Hadith (Foundations of Hadith), which includes:
- The science of hadith authentication (Ilm al-Rijal)
- Chain of narration analysis (Isnad)
- Hadith classifications (Sahih, Hasan, Da'if, etc.)
- Narrator criticism and reliability
- Hadith terminology in both Arabic and English

You have access to a comprehensive book on Usool al-Hadith. When students ask you questions:

1. **Use your knowledge** for general explanations and teaching
2. **Search the book** when asked about specific chapters, detailed methodologies, or precise definitions
3. **Use tools** when asked about specific narrators or classification terms

Guidelines:
- Be warm, patient, and encouraging with students
- Explain complex concepts clearly, using analogies when helpful
- Include relevant Arabic terms with English translations
- Reference specific chapters or scholars when citing from the book
- If you're unsure, say so honestly and guide the student to learn together

Remember: Your goal is to make the intricate science of Hadith methodology accessible and engaging for students of all levels.
"""

        # Create ChatContext with system message using add_message
        ctx = llm.ChatContext()
        ctx.add_message(
            role="system",
            content=system_message
        )
        return ctx

    def should_use_rag(self, question: str) -> bool:
        """
        Determine if a question should trigger RAG retrieval
        Returns True for most questions to always attempt RAG lookup

        Args:
            question: User's question

        Returns:
            True if RAG should be used (almost always True)
        """
        # Skip RAG for greetings and very short questions
        skip_keywords = ["hello", "hi", "thanks", "thank you", "bye", "goodbye"]
        if any(keyword in question.lower() for keyword in skip_keywords) and len(question.split()) < 5:
            return False

        # Always use RAG for substantive questions
        # This ensures we always check the book first
        return True

    async def enhance_with_rag(self, question: str) -> str:
        """
        Enhance a question with RAG context from the book
        Summarizes the retrieved content for concise voice responses

        Args:
            question: User's question

        Returns:
            Enhanced message with summarized RAG context
        """
        logger.info(f"RAG query detected for: {question}")

        # Retrieve context from the book
        context = self.rag_service.query(question)

        # Log the raw RAG results
        logger.info("=" * 80)
        logger.info("RAG RETRIEVED CONTEXT:")
        logger.info("-" * 80)
        logger.info(context)
        logger.info("=" * 80)

        # Summarize the context using OpenAI for concise voice output
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        summary_prompt = f"""You are helping a voice agent answer questions about Usool al-Hadith.

Retrieved context from the book:
{context}

User question: {question}

Your task:
1. If the context contains relevant information, extract and summarize it concisely (2-3 sentences max)
2. If the context is NOT relevant or doesn't answer the question, respond with: "NO_RELEVANT_INFO"
3. Include key Arabic terms if relevant
4. Cite page numbers if mentioned in the context

This will be spoken aloud, so keep it brief and natural.

Response:"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap for summarization
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=200,  # Keep it short for voice
                temperature=0.3,  # Lower temperature for factual accuracy
            )

            summarized_context = response.choices[0].message.content.strip()

            # Log the summarized result
            logger.info("-" * 80)
            logger.info(f"RAG SUMMARIZED ({len(context)} chars -> {len(summarized_context)} chars):")
            logger.info("-" * 80)
            logger.info(summarized_context)
            logger.info("=" * 80)

            # Check if RAG found relevant info
            if "NO_RELEVANT_INFO" in summarized_context:
                logger.info("⚠️ RAG didn't find relevant info - agent will use its own knowledge")
                return None  # Signal to not inject RAG context

            return (
                f"[Book Reference]: {summarized_context}\n\n"
                f"Now answer the student's question using this information. "
                f"If this doesn't fully answer the question, supplement with your own knowledge."
            )

        except Exception as e:
            logger.error(f"Error summarizing RAG context: {e}")
            # Fallback to truncated original context if summarization fails
            truncated = context[:500] + "..." if len(context) > 500 else context
            return (
                f"[Retrieved from Usool al-Hadith book]\n\n{truncated}\n\n"
                f"Based on the above content, please answer briefly: {question}"
            )


class HadithAssistant(Agent):
    """Modern Agent wrapper for Hadith teaching"""

    def __init__(self, hadith_agent: HadithVoiceAgent):
        # Get the system message for instructions
        system_message = f"""You are {hadith_agent.agent_name}, {hadith_agent.agent_personality}

Your expertise is in Usool al-Hadith (Foundations of Hadith), which includes:
- The science of hadith authentication (Ilm al-Rijal)
- Chain of narration analysis (Isnad)
- Hadith classifications (Sahih, Hasan, Da'if, etc.)
- Narrator criticism and reliability
- Hadith terminology in both Arabic and English

You have access to a comprehensive book on Usool al-Hadith. When students ask you questions:

1. **Use your knowledge** for general explanations and teaching
2. **Search the book** when asked about specific chapters, detailed methodologies, or precise definitions
3. **Use tools** when asked about specific narrators or classification terms

Guidelines:
- Be warm, patient, and encouraging with students
- Explain complex concepts clearly, using analogies when helpful
- Include relevant Arabic terms with English translations
- Reference specific chapters or scholars when citing from the book
- If you're unsure, say so honestly and guide the student to learn together

Remember: Your goal is to make the intricate science of Hadith methodology accessible and engaging for students of all levels.
"""

        super().__init__(
            instructions=system_message,
            # Pass the list of function tools
            tools=HADITH_TOOLS,
        )
        self.hadith_agent = hadith_agent

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        """
        Hook that runs each time the user finishes speaking.
        We plug in RAG logic here.

        Args:
            turn_ctx: Current conversation context
            new_message: User's message
        """
        logger.info(f"🎤 on_user_turn_completed called! Role: {new_message.role}")

        if new_message.role != "user":
            logger.info(f"   Skipping - not a user message")
            return

        # Safely get the question text
        question = (
            new_message.content
            if isinstance(new_message.content, str)
            else str(new_message.content)
        )

        logger.info(f"📝 User question: {question}")

        # Check if we should enhance with RAG
        if self.hadith_agent.should_use_rag(question):
            logger.info(f"✅ RAG triggered for question!")
            # Get RAG-enhanced context (now async for summarization)
            enhanced_message = await self.hadith_agent.enhance_with_rag(question)

            # Only inject RAG if it returned relevant info
            if enhanced_message:
                logger.info(f"💡 Injecting RAG context into conversation")
                # Add assistant message with RAG context using add_message
                turn_ctx.add_message(
                    role="assistant",
                    content=enhanced_message
                )
            else:
                logger.info(f"💭 No RAG context injected - agent will use its own knowledge")
        else:
            logger.info(f"❌ RAG skipped - greeting/short question")


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the LiveKit agent

    Args:
        ctx: Job context from LiveKit
    """
    logger.info("Starting Hadith Voice Agent...")

    # Initialize the agent logic
    hadith_agent = HadithVoiceAgent()

    # Connect to the room
    await ctx.connect()

    # Get configuration from environment
    model = os.getenv("LLM_MODEL", "gpt-4o")
    tts_voice = os.getenv("TTS_VOICE", "alloy")
    tts_model = os.getenv("TTS_MODEL", "tts-1")
    stt_model = os.getenv("STT_MODEL", "whisper-1")

    # Build LLM config - temperature is optional for newer models
    llm_kwargs = {"model": model}
    if os.getenv("LLM_TEMPERATURE"):
        llm_kwargs["temperature"] = float(os.getenv("LLM_TEMPERATURE"))

    # Create AgentSession with voice pipeline
    session = AgentSession(
        stt=openai.STT(model=stt_model),
        llm=openai.LLM(**llm_kwargs),
        tts=openai.TTS(model=tts_model, voice=tts_voice),
        vad=silero.VAD.load(),
    )

    # Create our custom Agent
    assistant = HadithAssistant(hadith_agent)

    # Start the session
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(),
    )

    # Send initial greeting
    greeting = (
        f"As-salamu alaykum! I am {hadith_agent.agent_name}, your guide in the noble science "
        f"of Usool al-Hadith. I'm here to help you understand the foundations of hadith "
        f"methodology, narrator criticism, and the classifications of prophetic traditions. "
        f"What would you like to learn about today?"
    )

    await session.generate_reply(instructions=greeting)

    logger.info("Agent is ready and listening...")


if __name__ == "__main__":
    # Run the agent using LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
