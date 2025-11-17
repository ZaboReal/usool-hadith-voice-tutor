"""
Custom tools for the Hadith Voice Agent
"""
from typing import Annotated
from livekit.agents import function_tool
import logging

logger = logging.getLogger(__name__)


@function_tool(
    description="Search for authentic hadith narrators and their reliability grades. "
                "Use this when the user asks about specific narrators (like Bukhari, Muslim, "
                "Abu Hurairah, etc.) or hadith authenticity classifications."
)
async def get_narrator_info(
    narrator_name: Annotated[
        str,
        "The name of the hadith narrator to look up"
    ],
) -> str:
    """
    Retrieve information about a hadith narrator's reliability

    Args:
        narrator_name: Name of the narrator

    Returns:
        Information about the narrator's reliability grade
    """
    logger.info(f"Looking up narrator: {narrator_name}")

    # Simulated database of narrators (in production, this could be a real database)
    narrators_db = {
        "bukhari": {
            "full_name": "Muhammad ibn Ismail al-Bukhari",
            "grade": "Highly Trustworthy (Thiqa)",
            "era": "3rd century AH",
            "known_for": "Compiler of Sahih al-Bukhari, one of the most authentic hadith collections",
            "student_of": "Imam Ahmad, Ali ibn al-Madini"
        },
        "muslim": {
            "full_name": "Muslim ibn al-Hajjaj",
            "grade": "Highly Trustworthy (Thiqa)",
            "era": "3rd century AH",
            "known_for": "Compiler of Sahih Muslim",
            "student_of": "Imam Ahmad, Ishaq ibn Rahawayh"
        },
        "abu hurairah": {
            "full_name": "Abd al-Rahman ibn Sakhr al-Dawsi",
            "grade": "Companion (Sahabi) - Highest Grade",
            "era": "1st century AH",
            "known_for": "Most prolific narrator of hadith, narrated over 5,000 hadiths",
            "companion_of": "Prophet Muhammad (peace be upon him)"
        },
        "tirmidhi": {
            "full_name": "Muhammad ibn Isa at-Tirmidhi",
            "grade": "Trustworthy (Thiqa)",
            "era": "3rd century AH",
            "known_for": "Compiler of Jami' at-Tirmidhi, one of the six canonical hadith collections",
            "student_of": "Imam Bukhari"
        },
        "ibn majah": {
            "full_name": "Muhammad ibn Yazid ibn Majah",
            "grade": "Trustworthy (Thiqa)",
            "era": "3rd century AH",
            "known_for": "Compiler of Sunan Ibn Majah",
            "student_of": "Abu Bakr ibn Abi Shaybah"
        }
    }

    # Normalize the narrator name for lookup
    narrator_key = narrator_name.lower().strip()

    if narrator_key in narrators_db:
        info = narrators_db[narrator_key]
        return (
            f"**{info['full_name']}**\n"
            f"Reliability Grade: {info['grade']}\n"
            f"Era: {info['era']}\n"
            f"Known for: {info['known_for']}\n"
            f"Teacher/Connection: {info.get('student_of', info.get('companion_of', 'N/A'))}"
        )
    else:
        return (
            f"I don't have detailed information about '{narrator_name}' in my database. "
            f"However, I can help you understand the general principles of narrator criticism "
            f"(Ilm al-Rijal) from Usool al-Hadith if you'd like."
        )


@function_tool(
    description="Get the classification and grading of hadith authenticity levels. "
                "Use this when discussing hadith classifications like Sahih, Hasan, Da'if, etc."
)
async def get_hadith_classification(
    classification: Annotated[
        str,
        "The hadith classification term (e.g., Sahih, Hasan, Da'if, Mawdu)"
    ],
) -> str:
    """
    Get detailed information about hadith authenticity classifications

    Args:
        classification: The type of classification to explain

    Returns:
        Detailed explanation of the classification
    """
    logger.info(f"Looking up hadith classification: {classification}")

    classifications = {
        "sahih": {
            "arabic": "صحيح",
            "meaning": "Authentic/Sound",
            "definition": "A hadith with a continuous chain of trustworthy narrators, "
                         "no defects, and no irregularities",
            "usage": "Can be used as proof in Islamic law",
            "example": "Hadiths in Sahih Bukhari and Sahih Muslim"
        },
        "hasan": {
            "arabic": "حسن",
            "meaning": "Good",
            "definition": "Similar to Sahih but with slightly less strict narrator reliability",
            "usage": "Can be used as proof, though slightly weaker than Sahih",
            "example": "Many hadiths in Jami' at-Tirmidhi"
        },
        "daif": {
            "arabic": "ضعيف",
            "meaning": "Weak",
            "definition": "A hadith with a break in the chain or unreliable narrator",
            "usage": "Cannot be used as primary proof, but may be used for virtuous deeds",
            "example": "Some hadiths in Sunan Ibn Majah"
        },
        "mawdu": {
            "arabic": "موضوع",
            "meaning": "Fabricated/Forged",
            "definition": "A hadith that is completely fabricated and falsely attributed",
            "usage": "Completely rejected and cannot be used",
            "example": "Various fabricated hadiths identified by hadith critics"
        },
        "mutawatir": {
            "arabic": "متواتر",
            "meaning": "Continuously Recurrent",
            "definition": "Narrated by so many people at each level that fabrication is impossible",
            "usage": "Highest level of certainty, equivalent to definitive knowledge",
            "example": "The five daily prayers"
        }
    }

    class_key = classification.lower().strip()

    if class_key in classifications:
        info = classifications[class_key]
        return (
            f"**{classification.upper()} ({info['arabic']})**\n"
            f"Meaning: {info['meaning']}\n\n"
            f"Definition: {info['definition']}\n\n"
            f"Usage in Islamic Law: {info['usage']}\n\n"
            f"Example: {info['example']}"
        )
    else:
        return (
            f"I don't have specific information about '{classification}' classification. "
            f"The main classifications are: Sahih (Authentic), Hasan (Good), Da'if (Weak), "
            f"Mawdu' (Fabricated), and Mutawatir (Continuously Recurrent). "
            f"Would you like to know about any of these?"
        )


# Export tools as a list
HADITH_TOOLS = [get_narrator_info, get_hadith_classification]
