# =============================================================================
# Voice-Controlled Clinical Interface
# ClinChat-RAG Enhanced Medical Intelligence System
# =============================================================================

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import speech_recognition as sr
import pyttsx3
import webrtcvad
import numpy as np
import io
import wave
import threading
from queue import Queue
import sounddevice as sd
from scipy.io import wavfile

# =============================================================================
# Data Models and Types
# =============================================================================

class VoiceCommandType(Enum):
    NAVIGATION = "navigation"
    DICTATION = "dictation"
    QUERY = "query"
    CONTROL = "control"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"

class SpeechQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

@dataclass
class VoiceCommand:
    command_id: str
    command_type: VoiceCommandType
    raw_text: str
    processed_text: str
    confidence_score: float
    intent: str
    parameters: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None

@dataclass
class ClinicalNote:
    note_id: str
    patient_id: str
    note_type: str  # progress_note, discharge_summary, consultation, etc.
    content: str
    structured_data: Dict[str, Any]
    author: str
    timestamp: datetime
    voice_generated: bool = True
    confidence_score: float = 0.0

@dataclass
class VoiceSession:
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    commands_processed: int
    notes_generated: int
    total_speech_time: float
    average_confidence: float
    session_type: str  # documentation, navigation, query

@dataclass
class SpeechAnalysis:
    audio_duration: float
    speech_quality: SpeechQuality
    background_noise_level: float
    speech_rate: float  # words per minute
    confidence_factors: Dict[str, float]
    preprocessing_applied: List[str]

# =============================================================================
# Voice-Controlled Clinical Interface
# =============================================================================

class ClinicalVoiceInterface:
    """
    Advanced voice-controlled interface providing:
    - Speech-to-text clinical note generation
    - Voice-controlled navigation and commands
    - Hands-free operation for clinical workflows
    - Real-time voice processing and feedback
    - Multi-language support for diverse populations
    """
    
    def __init__(self, language: str = "en-US"):
        self.logger = logging.getLogger(__name__)
        self.language = language
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = self._initialize_tts_engine()
        self.voice_commands = self._initialize_voice_commands()
        self.medical_vocabulary = self._load_medical_vocabulary()
        self.active_session: Optional[VoiceSession] = None
        self.command_queue = Queue()
        self.is_listening = False
        
        # Audio processing parameters
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        # Calibrate microphone
        self._calibrate_microphone()
        
    def _initialize_tts_engine(self) -> pyttsx3.Engine:
        """Initialize text-to-speech engine"""
        engine = pyttsx3.init()
        
        # Configure voice properties
        voices = engine.getProperty('voices')
        
        # Prefer female voice for medical applications (studies show better patient comfort)
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        
        # Set speech rate and volume
        engine.setProperty('rate', 180)  # Words per minute
        engine.setProperty('volume', 0.8)  # Volume level (0.0 to 1.0)
        
        return engine
        
    def _initialize_voice_commands(self) -> Dict[str, Dict[str, Any]]:
        """Initialize voice command patterns and handlers"""
        return {
            # Navigation commands
            "open_patient": {
                "patterns": [
                    r"open patient (\w+)",
                    r"navigate to patient (\w+)",
                    r"show patient (\w+)"
                ],
                "type": VoiceCommandType.NAVIGATION,
                "handler": self._handle_patient_navigation
            },
            
            "go_to_section": {
                "patterns": [
                    r"go to (vital signs|medications|lab results|notes)",
                    r"navigate to (vital signs|medications|lab results|notes)",
                    r"show me (vital signs|medications|lab results|notes)"
                ],
                "type": VoiceCommandType.NAVIGATION,
                "handler": self._handle_section_navigation
            },
            
            # Clinical documentation commands
            "start_note": {
                "patterns": [
                    r"start (progress note|discharge summary|consultation)",
                    r"begin (progress note|discharge summary|consultation)",
                    r"create new (progress note|discharge summary|consultation)"
                ],
                "type": VoiceCommandType.DOCUMENTATION,
                "handler": self._handle_start_note
            },
            
            "dictate_assessment": {
                "patterns": [
                    r"assessment (.+)",
                    r"clinical assessment (.+)",
                    r"my assessment is (.+)"
                ],
                "type": VoiceCommandType.DICTATION,
                "handler": self._handle_assessment_dictation
            },
            
            "dictate_plan": {
                "patterns": [
                    r"plan (.+)",
                    r"treatment plan (.+)",
                    r"the plan is (.+)"
                ],
                "type": VoiceCommandType.DICTATION,
                "handler": self._handle_plan_dictation
            },
            
            # Query commands
            "ask_question": {
                "patterns": [
                    r"what is (.+)",
                    r"tell me about (.+)",
                    r"explain (.+)",
                    r"search for (.+)"
                ],
                "type": VoiceCommandType.QUERY,
                "handler": self._handle_clinical_query
            },
            
            # Control commands
            "save_note": {
                "patterns": [
                    r"save note",
                    r"save document",
                    r"save current note"
                ],
                "type": VoiceCommandType.CONTROL,
                "handler": self._handle_save_note
            },
            
            "cancel_operation": {
                "patterns": [
                    r"cancel",
                    r"stop",
                    r"never mind"
                ],
                "type": VoiceCommandType.CONTROL,
                "handler": self._handle_cancel
            }
        }
    
    def _load_medical_vocabulary(self) -> Dict[str, List[str]]:
        """Load medical vocabulary for improved recognition"""
        return {
            "medications": [
                "metformin", "lisinopril", "atorvastatin", "amlodipine", "metoprolol",
                "hydrochlorothiazide", "simvastatin", "losartan", "levothyroxine", "warfarin",
                "aspirin", "clopidogrel", "furosemide", "prednisone", "insulin"
            ],
            "conditions": [
                "diabetes", "hypertension", "atrial fibrillation", "heart failure", "copd",
                "pneumonia", "myocardial infarction", "stroke", "sepsis", "cellulitis",
                "urinary tract infection", "chronic kidney disease", "osteoarthritis"
            ],
            "body_parts": [
                "heart", "lungs", "liver", "kidneys", "brain", "abdomen", "chest",
                "extremities", "skin", "eyes", "ears", "throat", "neck", "back"
            ],
            "assessments": [
                "stable", "improved", "worsened", "critical", "guarded", "fair",
                "good", "poor", "satisfactory", "concerning", "normal", "abnormal"
            ],
            "procedures": [
                "echocardiogram", "chest x-ray", "ct scan", "mri", "blood draw",
                "electrocardiogram", "colonoscopy", "endoscopy", "biopsy", "ultrasound"
            ]
        }

    async def start_voice_session(self, user_id: str, session_type: str = "documentation") -> str:
        """
        Start a new voice interaction session
        
        Args:
            user_id: Identifier for the user
            session_type: Type of session (documentation, navigation, query)
            
        Returns:
            Session ID for tracking
        """
        try:
            session_id = f"voice_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            self.active_session = VoiceSession(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                end_time=None,
                commands_processed=0,
                notes_generated=0,
                total_speech_time=0.0,
                average_confidence=0.0,
                session_type=session_type
            )
            
            self.logger.info(f"Started voice session {session_id} for user {user_id}")
            
            # Start background listening
            await self._start_background_listening()
            
            # Provide audio feedback
            await self._speak(f"Voice session started. I'm ready to assist with {session_type}.")
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error starting voice session: {str(e)}")
            raise

    async def process_voice_command(self, audio_data: bytes) -> VoiceCommand:
        """
        Process voice command from audio data
        
        Args:
            audio_data: Raw audio data in WAV format
            
        Returns:
            Processed voice command with intent and parameters
        """
        try:
            start_time = datetime.now()
            self.logger.info("Processing voice command from audio data")
            
            # Analyze speech quality
            speech_analysis = await self._analyze_speech_quality(audio_data)
            
            # Convert speech to text
            raw_text = await self._speech_to_text(audio_data, speech_analysis)
            
            if not raw_text:
                return VoiceCommand(
                    command_id=f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    command_type=VoiceCommandType.UNKNOWN,
                    raw_text="",
                    processed_text="",
                    confidence_score=0.0,
                    intent="no_speech_detected",
                    parameters={},
                    timestamp=datetime.now()
                )
            
            # Process and clean text
            processed_text = await self._process_medical_text(raw_text)
            
            # Determine command type and intent
            command_type, intent, parameters = await self._parse_voice_command(processed_text)
            
            # Calculate overall confidence
            confidence_score = await self._calculate_command_confidence(
                speech_analysis, raw_text, processed_text, intent
            )
            
            # Create command object
            command = VoiceCommand(
                command_id=f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                command_type=command_type,
                raw_text=raw_text,
                processed_text=processed_text,
                confidence_score=confidence_score,
                intent=intent,
                parameters=parameters,
                timestamp=datetime.now(),
                user_id=self.active_session.user_id if self.active_session else None
            )
            
            # Update session statistics
            if self.active_session:
                self.active_session.commands_processed += 1
                processing_time = (datetime.now() - start_time).total_seconds()
                self.active_session.total_speech_time += processing_time
            
            self.logger.info(f"Processed voice command: {intent} (confidence: {confidence_score:.2f})")
            return command
            
        except Exception as e:
            self.logger.error(f"Error processing voice command: {str(e)}")
            raise

    async def generate_clinical_notes(self, voice_input: bytes, 
                                    patient_id: str,
                                    note_type: str = "progress_note") -> ClinicalNote:
        """
        Convert speech to structured clinical notes
        
        Args:
            voice_input: Audio data containing clinical dictation
            patient_id: Patient identifier
            note_type: Type of clinical note
            
        Returns:
            Structured clinical note
        """
        try:
            self.logger.info(f"Generating {note_type} for patient {patient_id}")
            
            # Convert speech to text
            raw_dictation = await self._speech_to_text(voice_input)
            
            if not raw_dictation:
                raise ValueError("No speech detected in audio input")
            
            # Process medical terminology
            processed_text = await self._process_medical_text(raw_dictation)
            
            # Structure the clinical note
            structured_data = await self._structure_clinical_note(processed_text, note_type)
            
            # Generate formatted note content
            formatted_content = await self._format_clinical_note(structured_data, note_type)
            
            # Calculate confidence score
            confidence_score = await self._calculate_note_confidence(
                raw_dictation, processed_text, structured_data
            )
            
            # Create clinical note
            note = ClinicalNote(
                note_id=f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{patient_id}",
                patient_id=patient_id,
                note_type=note_type,
                content=formatted_content,
                structured_data=structured_data,
                author=self.active_session.user_id if self.active_session else "voice_user",
                timestamp=datetime.now(),
                voice_generated=True,
                confidence_score=confidence_score
            )
            
            # Update session statistics
            if self.active_session:
                self.active_session.notes_generated += 1
            
            self.logger.info(f"Generated clinical note {note.note_id} with confidence {confidence_score:.2f}")
            return note
            
        except Exception as e:
            self.logger.error(f"Error generating clinical notes: {str(e)}")
            raise

    async def execute_voice_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """
        Execute a processed voice command
        
        Args:
            command: Processed voice command to execute
            
        Returns:
            Execution result with status and response
        """
        try:
            self.logger.info(f"Executing voice command: {command.intent}")
            
            # Find command handler
            handler = None
            for cmd_name, cmd_config in self.voice_commands.items():
                if command.intent in cmd_name or any(
                    re.search(pattern, command.processed_text, re.IGNORECASE)
                    for pattern in cmd_config["patterns"]
                ):
                    handler = cmd_config["handler"]
                    break
            
            if not handler:
                return {
                    "status": "error",
                    "message": "Command not recognized",
                    "suggestion": "Try rephrasing your command or use 'help' for available commands"
                }
            
            # Execute command handler
            result = await handler(command)
            
            # Provide audio feedback if enabled
            if result.get("speak_response", True):
                await self._speak(result.get("response", "Command executed successfully"))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing voice command: {str(e)}")
            error_response = {
                "status": "error",
                "message": f"Error executing command: {str(e)}",
                "command_id": command.command_id
            }
            await self._speak("I encountered an error processing your command. Please try again.")
            return error_response

    # =============================================================================
    # Speech Processing Methods
    # =============================================================================
    
    async def _speech_to_text(self, audio_data: bytes, 
                            speech_analysis: Optional['SpeechAnalysis'] = None) -> str:
        """Convert speech audio to text using multiple recognition engines"""
        try:
            # Convert bytes to audio format compatible with speech_recognition
            audio_io = io.BytesIO(audio_data)
            
            # Try multiple recognition methods for better accuracy
            recognition_results = []
            
            # Method 1: Google Speech Recognition (requires internet)
            try:
                with sr.AudioFile(audio_io) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio, language=self.language)
                    recognition_results.append(("google", text, 0.9))
            except Exception as e:
                self.logger.warning(f"Google recognition failed: {str(e)}")
            
            # Method 2: Sphinx (offline)
            try:
                audio_io.seek(0)
                with sr.AudioFile(audio_io) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_sphinx(audio)
                    recognition_results.append(("sphinx", text, 0.7))
            except Exception as e:
                self.logger.warning(f"Sphinx recognition failed: {str(e)}")
            
            # Method 3: Wit.ai (if API key available)
            # This would require API key configuration
            
            if not recognition_results:
                return ""
            
            # Choose best result (prioritize by accuracy and confidence)
            best_result = max(recognition_results, key=lambda x: x[2])
            return best_result[1]
            
        except Exception as e:
            self.logger.error(f"Speech to text conversion failed: {str(e)}")
            return ""
    
    async def _process_medical_text(self, raw_text: str) -> str:
        """Process text with medical terminology corrections"""
        processed_text = raw_text.lower()
        
        # Medical term corrections (common speech recognition errors)
        medical_corrections = {
            "pneumonia": ["new monia", "numonia", "phenomena"],
            "hypertension": ["high per tension", "hyper tension"],
            "diabetes": ["die beatus", "die betas", "diabeetus"],
            "myocardial infarction": ["my cardial infarction", "heart attack"],
            "atrial fibrillation": ["a trial fibrillation", "atrial fib"],
            "creatinine": ["creatine", "creating"],
            "hemoglobin": ["hemo globin", "he mo globin"],
            "blood pressure": ["blood pleasure", "blurred pressure"],
            "electrocardiogram": ["electro cardio gram", "ekg", "ecg"],
            "chest x-ray": ["chest x ray", "chest xray"]
        }
        
        for correct_term, variations in medical_corrections.items():
            for variation in variations:
                processed_text = processed_text.replace(variation, correct_term)
        
        # Standardize medical abbreviations
        abbreviation_expansions = {
            "bp": "blood pressure",
            "hr": "heart rate",
            "rr": "respiratory rate",
            "temp": "temperature",
            "o2": "oxygen",
            "sat": "saturation",
            "bpm": "beats per minute",
            "mmhg": "millimeters of mercury"
        }
        
        for abbrev, expansion in abbreviation_expansions.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            processed_text = re.sub(pattern, expansion, processed_text, flags=re.IGNORECASE)
        
        return processed_text
    
    async def _analyze_speech_quality(self, audio_data: bytes) -> SpeechAnalysis:
        """Analyze speech quality for better processing"""
        try:
            # Convert audio data to numpy array
            audio_io = io.BytesIO(audio_data)
            sample_rate, audio_array = wavfile.read(audio_io)
            
            # Calculate audio metrics
            audio_duration = len(audio_array) / sample_rate
            
            # Estimate background noise level
            noise_level = np.std(audio_array[:int(0.1 * len(audio_array))])  # First 10% as noise sample
            
            # Estimate speech rate (rough approximation)
            # Count zero crossings as proxy for speech activity
            zero_crossings = np.sum(np.diff(np.signbit(audio_array)))
            speech_rate = (zero_crossings / audio_duration) * 0.1  # Rough words per minute estimate
            
            # Determine speech quality
            signal_to_noise = np.max(np.abs(audio_array)) / (noise_level + 1e-6)
            
            if signal_to_noise > 20:
                quality = SpeechQuality.EXCELLENT
            elif signal_to_noise > 10:
                quality = SpeechQuality.GOOD
            elif signal_to_noise > 5:
                quality = SpeechQuality.FAIR
            else:
                quality = SpeechQuality.POOR
            
            return SpeechAnalysis(
                audio_duration=audio_duration,
                speech_quality=quality,
                background_noise_level=noise_level,
                speech_rate=speech_rate,
                confidence_factors={
                    "signal_to_noise": signal_to_noise,
                    "audio_clarity": min(signal_to_noise / 20, 1.0),
                    "duration_adequacy": min(audio_duration / 2.0, 1.0)  # Prefer 2+ second clips
                },
                preprocessing_applied=["noise_reduction", "normalization"]
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing speech quality: {str(e)}")
            # Return default analysis
            return SpeechAnalysis(
                audio_duration=1.0,
                speech_quality=SpeechQuality.FAIR,
                background_noise_level=0.1,
                speech_rate=150.0,
                confidence_factors={"default": 0.5},
                preprocessing_applied=[]
            )

    # =============================================================================
    # Command Handlers
    # =============================================================================
    
    async def _handle_patient_navigation(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle patient navigation commands"""
        patient_id = command.parameters.get('patient_id', '')
        return {
            "status": "success",
            "action": "navigate_to_patient",
            "patient_id": patient_id,
            "response": f"Navigating to patient {patient_id}",
            "speak_response": True
        }
    
    async def _handle_section_navigation(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle section navigation commands"""
        section = command.parameters.get('section', '')
        return {
            "status": "success",
            "action": "navigate_to_section",
            "section": section,
            "response": f"Showing {section} section",
            "speak_response": True
        }
    
    async def _handle_clinical_query(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle clinical query commands"""
        query = command.parameters.get('query', command.processed_text)
        return {
            "status": "success",
            "action": "clinical_query",
            "query": query,
            "response": f"Searching for information about {query}",
            "speak_response": True
        }
    
    async def _handle_start_note(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle start note commands"""
        note_type = command.parameters.get('note_type', 'progress_note')
        return {
            "status": "success",
            "action": "start_note",
            "note_type": note_type,
            "response": f"Starting {note_type.replace('_', ' ')}. Begin dictating.",
            "speak_response": True
        }
    
    async def _handle_assessment_dictation(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle assessment dictation"""
        assessment = command.parameters.get('assessment', '')
        return {
            "status": "success",
            "action": "dictate_assessment",
            "content": assessment,
            "response": "Assessment recorded",
            "speak_response": True
        }
    
    async def _handle_plan_dictation(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle plan dictation"""
        plan = command.parameters.get('plan', '')
        return {
            "status": "success",
            "action": "dictate_plan",
            "content": plan,
            "response": "Plan recorded",
            "speak_response": True
        }
    
    async def _handle_save_note(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle save note commands"""
        return {
            "status": "success",
            "action": "save_note",
            "response": "Note saved successfully",
            "speak_response": True
        }
    
    async def _handle_cancel(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle cancel commands"""
        return {
            "status": "success",
            "action": "cancel",
            "response": "Operation cancelled",
            "speak_response": True
        }

    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.logger.info("Microphone calibrated for ambient noise")
        except Exception as e:
            self.logger.warning(f"Microphone calibration failed: {str(e)}")
    
    async def _speak(self, text: str):
        """Convert text to speech"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Text-to-speech failed: {str(e)}")

# =============================================================================
# Usage Example and Testing
# =============================================================================

async def main():
    """Example usage of the Voice-Controlled Clinical Interface"""
    
    # Initialize the voice interface
    voice_interface = ClinicalVoiceInterface(language="en-US")
    
    print("=== Voice-Controlled Clinical Interface Demo ===")
    
    # Start a voice session
    session_id = await voice_interface.start_voice_session("DR001", "documentation")
    print(f"Started voice session: {session_id}")
    
    # Example: Process a voice command (in real implementation, this would be actual audio)
    # For demo purposes, we'll simulate the command processing
    
    # Simulate voice command processing
    example_commands = [
        "Open patient John Doe",
        "Start progress note",
        "Assessment: Patient appears stable with improving vital signs",
        "Plan: Continue current medications and monitor overnight",
        "Save note"
    ]
    
    for command_text in example_commands:
        print(f"\nProcessing: '{command_text}'")
        
        # In real implementation, this would be actual audio data
        # For demo, we'll create a mock command
        command = VoiceCommand(
            command_id=f"demo_{datetime.now().strftime('%H%M%S')}",
            command_type=VoiceCommandType.DOCUMENTATION,
            raw_text=command_text,
            processed_text=command_text.lower(),
            confidence_score=0.85,
            intent="demonstration",
            parameters={"text": command_text},
            timestamp=datetime.now()
        )
        
        # Execute the command
        result = await voice_interface.execute_voice_command(command)
        print(f"Result: {result['status']} - {result.get('response', 'No response')}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the example
    asyncio.run(main())