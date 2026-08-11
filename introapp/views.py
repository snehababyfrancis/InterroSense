from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
import json
import base64
import shutil
from datetime import datetime
from .models import Report
from django.contrib import messages


# -------------------------------
# IMPORT YOUR LOGIC MODULES
# -------------------------------
from .question_generation import generate_interrogation_questions
from .video_predict import predict_image
from .audio_predict import predict_audio
from .lingustic_logic import check_linguistic_test
from django.core.paginator import Paginator



def calculate_final_result(video_pred, audio_pred, text_pred):
    """
    Calculate final result with priority: Image (Video) > Text > Audio
    Returns: dict with "result" and "percentage"
    """
    # Count LIE predictions for each modality
    lie_count = 0
    total_weight = 6  # Maximum possible weight (3+2+1)
    
    # Video/Image has highest priority (weight: 3)
    if video_pred.lower() == "lie":
        lie_count += 3
    
    # Text has medium priority (weight: 2)
    if text_pred.lower() == "lie":
        lie_count += 2
    
    # Audio has lowest priority (weight: 1)
    if audio_pred.lower() == "lie":
        lie_count += 1
    
    # Calculate percentage
    criminal_percentage = (lie_count / total_weight) * 100
    
    # Threshold: if weighted score >= 3, consider as CRIMINAL
    # This means either:
    # - Video says LIE (3 points)
    # - Text says LIE + Audio says LIE (2 + 1 = 3 points)
    # - Text says LIE (2 points) + any other indication
    result = "CRIMINAL" if lie_count >= 3 else "NOT_CRIMINAL"
    
    return {
        "result": result,
        "percentage": round(criminal_percentage, 1)
    }

def reports(request):
    reports_qs = Report.objects.all().order_by("-timestamp")
    
    # Add final_result to each report
    for report in reports_qs:
        report.final_result = calculate_final_result(
            report.video_prediction,
            report.audio_prediction, 
            report.linguistic_analysis
        )

    paginator = Paginator(reports_qs, 5)  # 5 reports per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "reports.html", {
        "page_obj": page_obj
    })

# -------------------------------
# GLOBAL STORE (REPLACED WITH SESSIONS)
# -------------------------------
# five_questions = []  <-- Removed
# accused_id = ""      <-- Removed
# ==========================================================
# BASIC PAGE VIEWS
# ==========================================================
def index(request):
    return render(request, "index.html")

def police(request):
    return render(request, "police.html")


# ==========================================================
# GENERATE QUESTIONS (for police interface)
# ==========================================================
@csrf_exempt
def generate_questions(request):
    """
    Generate questions for police interface review
    Returns questions without starting interrogation
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            
            scenario = data.get("scenario", "")
            accused_id = data.get("accused_id", "")
            question_count = data.get("question_count", 10)
            
            # Validate inputs
            if not scenario.strip():
                return JsonResponse({
                    "status": "error",
                    "message": "Scenario cannot be empty"
                }, status=400)
                
            if not accused_id.strip():
                return JsonResponse({
                    "status": "error", 
                    "message": "Accused ID cannot be empty"
                }, status=400)
            
            # Generate questions using existing function
            questions = generate_interrogation_questions(
                scenario=scenario,
                num_questions=question_count
            )
            
            # Store in session for later use
            request.session['temp_scenario'] = scenario
            request.session['temp_accused_id'] = accused_id
            request.session['temp_questions'] = questions
            request.session.modified = True
            
            return JsonResponse({
                "status": "success",
                "questions": questions,
                "message": f"Generated {len(questions)} questions successfully"
            })
            
        except Exception as e:
            print(f"❌ Error generating questions: {e}")
            return JsonResponse({
                "status": "error",
                "message": "Failed to generate questions. Please try again."
            }, status=500)
    
    return JsonResponse({"error": "POST required"}, status=400)


# ==========================================================
# SAVE QUESTIONS (for police interface)
# ==========================================================
@csrf_exempt
def save_questions(request):
    """
    Save customized questions and start interrogation
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            
            scenario = data.get("scenario", "")
            accused_id = data.get("accused_id", "")
            questions = data.get("questions", [])
            time_limits = data.get("time_limits", [])
            
            # Validate inputs
            if not scenario.strip():
                return JsonResponse({
                    "status": "error",
                    "message": "Scenario cannot be empty"
                }, status=400)
                
            if not accused_id.strip():
                return JsonResponse({
                    "status": "error",
                    "message": "Accused ID cannot be empty"
                }, status=400)
                
            if not questions or len(questions) == 0:
                return JsonResponse({
                    "status": "error",
                    "message": "At least one question is required"
                }, status=400)
            
            # Ensure time limits match questions length
            if not time_limits or len(time_limits) != len(questions):
                time_limits = [60] * len(questions)  # Default 60 seconds
            
            # Store in session (using same structure as load_questions)
            request.session['questions'] = questions
            request.session['five_questions'] = questions  # backward compatibility
            request.session['question_count'] = len(questions)
            request.session['seconds_per_question'] = 60  # default
            request.session['individual_times'] = time_limits
            request.session['accused_id'] = accused_id
            request.session['scenario'] = scenario
            request.session.modified = True
            
            # Clear previous fst_data
            fst_dir = os.path.join(settings.MEDIA_ROOT, "fst_data")
            if os.path.exists(fst_dir):
                shutil.rmtree(fst_dir)
            
            print(f"✅ Saved {len(questions)} questions for accused {accused_id}")
            
            return JsonResponse({
                "status": "success",
                "message": "Questions saved successfully",
                "questions_count": len(questions)
            })
            
        except Exception as e:
            print(f"❌ Error saving questions: {e}")
            return JsonResponse({
                "status": "error",
                "message": "Failed to save questions. Please try again."
            }, status=500)
    
    return JsonResponse({"error": "POST required"}, status=400)


# ==========================================================
# LOAD QUESTIONS
# ==========================================================
@csrf_exempt
def load_questions(request):
    # global five_questions, accused_id  <-- Removed globals
    # five_questions.clear()             <-- Removed globals

    if request.method == "POST":
        try:
            # Clear previous fst_data
            fst_dir = os.path.join(settings.MEDIA_ROOT, "fst_data")
            if os.path.exists(fst_dir):
                shutil.rmtree(fst_dir)
            
            data = json.loads(request.body.decode("utf-8"))

            scenario = data.get("scenario", "default")
            accused_id = data.get("accused_id", "")
            question_count = data.get("question_count", 5)
            seconds_per_question = data.get("seconds_per_question", 30)
            
            # Handle custom questions and individual times
            questions = data.get("questions", [])
            individual_times = data.get("individual_times", [])

            # Coerce + clamp session configuration
            try:
                question_count = int(question_count)
            except Exception:
                question_count = 5
            try:
                seconds_per_question = int(seconds_per_question)
            except Exception:
                seconds_per_question = 30

            question_count = max(1, min(question_count, 20))
            seconds_per_question = max(5, min(seconds_per_question, 600))

            print("✅ Accused ID received:", accused_id)

            # If custom questions are provided, use them; otherwise generate
            if questions and len(questions) > 0:
                final_questions = questions
                final_times = individual_times if individual_times and len(individual_times) == len(questions) else [seconds_per_question] * len(questions)
            else:
                final_questions = generate_interrogation_questions(
                    scenario=scenario,
                    num_questions=question_count
                )
                final_times = [seconds_per_question] * len(final_questions)

            # Store in session
            request.session['questions'] = final_questions
            request.session['five_questions'] = final_questions  # backward compatibility
            request.session['question_count'] = len(final_questions)
            request.session['seconds_per_question'] = seconds_per_question
            request.session['individual_times'] = final_times
            request.session['accused_id'] = accused_id
            request.session['scenario'] = scenario
            request.session.modified = True 

            return JsonResponse({
                "status": "success",
                "questions": final_questions,
                "individual_times": final_times
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST required"}, status=400)


# ACCUSED PAGE
# ==========================================================
def accused(request):
    questions = request.session.get('questions') or request.session.get('five_questions', [])
    question_count = request.session.get('question_count', len(questions))
    individual_times = request.session.get('individual_times', [])
    
    # Use individual times if available, otherwise use default seconds_per_question
    if individual_times and len(individual_times) == len(questions):
        times_to_use = individual_times
    else:
        default_time = request.session.get('seconds_per_question', 30)
        times_to_use = [default_time] * len(questions)
    
    return render(request, "accused.html", {
        "questions_json": json.dumps(questions),
        "question_count": question_count,
        "individual_times": json.dumps(times_to_use),
    })

# ==========================================================
# COLLECT FRAMES + AUDIO + TEXT
# ==========================================================
@csrf_exempt
def collect_fst(request):
    BASE_DIR = os.path.join(settings.MEDIA_ROOT, "fst_data")
    os.makedirs(BASE_DIR, exist_ok=True)

    # ---------------- VIDEO FRAMES ----------------
    if request.content_type == "application/json":
        data = json.loads(request.body.decode("utf-8"))

        if data.get("type") != "frame":
            return JsonResponse({"status": "ignored"})

        q_idx = data.get("question_index")
        frame_data = data.get("frame")

        frame_dir = os.path.join(BASE_DIR, f"question_{q_idx}", "frames")
        os.makedirs(frame_dir, exist_ok=True)

        header, encoded = frame_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(frame_dir, f"frame_{ts}.jpg")

        with open(path, "wb") as f:
            f.write(img_bytes)

        # Optional: realtime visual inference for the interrogation UI.
        # This is used to populate live emotion labels while the accused answers.
        realtime_emotion = bool(data.get("realtime_emotion"))
        if realtime_emotion:
            try:
                emotion_visual = predict_image(path)
                print(f"✅ Realtime emotion prediction: {emotion_visual}")
            except Exception as e:
                print(f"❌ Realtime emotion prediction failed: {e}")
                emotion_visual = {
                    "prediction": "ERROR",
                    "confidence": 0,
                    "error": str(e)
                }
            return JsonResponse({
                "status": "frame_saved",
                "emotionVisual": emotion_visual
            })

        return JsonResponse({"status": "frame_saved"})

    # ---------------- AUDIO + TEXT ----------------
    if request.method == "POST":
        if request.POST.get("type") != "audio_text":
            return JsonResponse({"status": "ignored"})

        q_idx = request.POST.get("question_index")
        transcript = request.POST.get("transcript", "")
        audio_file = request.FILES.get("audio_file")

        q_dir = os.path.join(BASE_DIR, f"question_{q_idx}")
        audio_dir = os.path.join(q_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        audio_path = os.path.join(audio_dir, "answer.wav")
        with open(audio_path, "wb") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        with open(os.path.join(q_dir, "transcript.txt"), "w", encoding="utf-8") as f:
            f.write(transcript)

        return JsonResponse({"status": "audio_text_saved"})

    return JsonResponse({"error": "Invalid request"}, status=400)

# ==========================================================
# ANALYSIS LOGIC
# ==========================================================
def analyze_video_frames(frames_dir):
    total = 0
    lie_count = 0

    # Check if frames directory exists
    if not os.path.exists(frames_dir):
        print(f"⚠️  Frames directory not found: {frames_dir}")
        return {"prediction": "NO_DATA", "lie_percentage": 0, "total_frames": 0}

    # Get list of frames
    try:
        frames = [img for img in os.listdir(frames_dir) if img.endswith(".jpg")]
        if not frames:
            print(f"⚠️  No .jpg frames found in: {frames_dir}")
            return {"prediction": "NO_DATA", "lie_percentage": 0, "total_frames": 0}
    except Exception as e:
        print(f"❌ Error reading frames directory: {e}")
        return {"prediction": "ERROR", "lie_percentage": 0, "total_frames": 0}

    for img in frames:
        try:
            total += 1
            result = predict_image(os.path.join(frames_dir, img))
            
            if result is None:
                print(f"⚠️  predict_image returned None for {img}")
                continue
            
            pred = result.get("prediction", "").lower()
            if pred == "lie":
                lie_count += 1
                
        except Exception as e:
            print(f"❌ Error processing frame {img}: {e}")
            continue

    if total == 0:
        return {"prediction": "NO_DATA", "lie_percentage": 0, "total_frames": 0}

    lie_percentage = (lie_count / total) * 100
    final = "LIE" if lie_percentage >= 50 else "TRUTH"

    print(f"✅ Video Analysis: {total} frames, {lie_count} lies, {lie_percentage}% → {final}")

    return {
        "prediction": final,
        "lie_percentage": round(lie_percentage, 2),
        "total_frames": total
    }

def analyze_question(q_idx, question_text=None):
    BASE_DIR = os.path.join(settings.MEDIA_ROOT, "fst_data")
    q_dir = os.path.join(BASE_DIR, f"question_{q_idx}")

    print(f"\n🔍 Analyzing Question {q_idx}...")
    print(f"   Directory: {q_dir}")
    if question_text:
        print(f"   Question: {question_text[:50]}...")

    # VIDEO
    frames_dir = os.path.join(q_dir, "frames")
    video = analyze_video_frames(frames_dir)

    # AUDIO
    audio_path = os.path.join(q_dir, "audio", "answer.wav")
    if not os.path.exists(audio_path):
        print(f"⚠️  Audio file not found: {audio_path}")
        audio = {"prediction": "NO_DATA", "confidence": 0}
    else:
        try:
            audio = predict_audio(audio_path)
            if audio is None:
                audio = {"prediction": "NO_DATA", "confidence": 0}
            print(f"✅ Audio Analysis: {audio.get('prediction')} ({audio.get('confidence')}%)")
        except Exception as e:
            print(f"❌ Audio analysis error: {e}")
            audio = {"prediction": "ERROR", "confidence": 0}

    # TEXT
    transcript_path = os.path.join(q_dir, "transcript.txt")
    if not os.path.exists(transcript_path):
        print(f"⚠️  Transcript file not found: {transcript_path}")
        text = {"classification": "NO_DATA", "lie_score": 0}
    else:
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript_content = f.read()
            
            if not transcript_content.strip():
                print(f"⚠️  Transcript is empty")
                text = {"classification": "NO_DATA", "lie_score": 0}
            else:
                text = check_linguistic_test(transcript_content, question=question_text)
                if text is None:
                    text = {"classification": "NO_DATA", "lie_score": 0}
                print(f"✅ Text Analysis: {text.get('classification')} (score={text.get('lie_score')})")
        except Exception as e:
            print(f"❌ Text analysis error: {e}")
            text = {"classification": "ERROR", "lie_score": 0}

    return {
        "video": video,
        "audio": audio,
        "text": text
    }

# ==========================================================
# FINAL REPORT (QUESTION-WISE)
# ==========================================================
def analyze_all_questions(accused_id, scenario='', questions=None):
    if questions is None:
        questions = []
    question_count = len(questions) if questions else 0
    if question_count <= 0:
        # Backward compatible fallback for older sessions
        question_count = 5

    lie_threshold = (question_count + 1) // 2  # majority (3/5 => 3)
    
    print("\n" + "="*60)
    print("FINAL INTERROGATION REPORT - ANALYSIS IN PROGRESS")
    print("="*60 + "\n")
    
    lie_count_of_video = 0
    lie_count_of_audio = 0
    lie_count_of_text = 0
    result_details = {}
    questions_with_data = 0
    
    for i in range(question_count):
        try:
            # Get the question text for contextual analysis
            question_text = None
            if questions and i < len(questions):
                question_text = questions[i]
            
            r = analyze_question(i, question_text=question_text)

            print(f"\n📋 Question {i+1} Results:")

            # VIDEO
            video_pred = r.get("video", {}).get("prediction", "NO_DATA")
            video_pct = r.get("video", {}).get("lie_percentage", 0.0)
            video_frames = r.get("video", {}).get("total_frames", 0)

            print(f"   🎥 Video  : {video_pred} ({video_pct}% from {video_frames} frames)")

            # AUDIO
            audio_pred = r.get("audio", {}).get("prediction", "NO_DATA")
            audio_conf = r.get("audio", {}).get("confidence", 0.0)

            print(f"   🎤 Audio  : {audio_pred} ({audio_conf}% confidence)")

            # TEXT
            text_label = r.get("text", {}).get("classification", "NO_DATA")
            text_score = r.get("text", {}).get("lie_score", 0.0)

            print(f"   📝 Text   : {text_label} (score={text_score})")

            # Store complete analysis including markers for question-by-question detail
            text_analysis = r.get("text", {})
            result_details[f"question_{i+1}"] = {
                "video": video_pred,
                "audio": audio_pred,
                "text": text_label,
                "text_full": text_analysis  # Include full analysis with markers
            }
            
            # Only count valid predictions (exclude NO_DATA and ERROR)
            if video_pred not in ["NO_DATA", "ERROR"]:
                lie_count_of_video += 1 if video_pred.lower() == "lie" else 0
                questions_with_data += 1
            
            if audio_pred not in ["NO_DATA", "ERROR"]:
                lie_count_of_audio += 1 if audio_pred.lower() == "lie" else 0
            
            if text_label not in ["NO_DATA", "ERROR"]:
                lie_count_of_text += 1 if text_label.lower() == "lie" else 0

        except Exception as e:
            print(f"❌ Question {i+1}: ERROR during analysis -> {str(e)}")
            result_details[f"question_{i+1}"] = {
                "video": "ERROR",
                "audio": "ERROR",
                "text": "ERROR"
            }
        
    # Generate final verdicts
    print("\n" + "-"*60)
    print("FINAL VERDICTS:")
    print("-"*60)
    
    # Video verdict
    if lie_count_of_video >= lie_threshold:
        final_result_video = "LIE"
    else:
        final_result_video = "TRUTH"
    print(f"🎥 Video Verdict: {final_result_video} ({lie_count_of_video}/{question_count} questions)")
    
    # Audio verdict
    if lie_count_of_audio >= lie_threshold:
        final_result_audio = "LIE"
    else:
        final_result_audio = "TRUTH"
    print(f"🎤 Audio Verdict: {final_result_audio} ({lie_count_of_audio}/{question_count} questions)")
    
    # Text verdict
    if lie_count_of_text >= lie_threshold:
        final_result_text = "LIE"
    else:
        final_result_text = "TRUTH"
    print(f"📝 Text Verdict: {final_result_text} ({lie_count_of_text}/{question_count} questions)")
    
    overall_results = {
        "video_result": final_result_video,
        "audio_result": final_result_audio,
        "text_result": final_result_text,
        "questions_analyzed": questions_with_data
    }

    try:
        report = Report.objects.create(
            accused_id=accused_id,
            overall_result=overall_results,
            video_prediction=final_result_video,
            audio_prediction=final_result_audio,
            linguistic_analysis=final_result_text,
            detailed_report=result_details,  # Django JSONField handles serialization
            scenario=scenario,
            questions=questions
        )
        print(f"\n✅ Report saved successfully (ID: {report.id})")
    except Exception as e:
        print(f"\n❌ Error saving report: {e}")

    print("="*60 + "\n")


@csrf_exempt
def analyze_results(request):
    if request.method == "POST":
        accused_id = request.session.get('accused_id', 'UNKNOWN')
        scenario = request.session.get('scenario', '')
        questions = request.session.get('questions') or request.session.get('five_questions', [])
        
        analyze_all_questions(accused_id, scenario, questions)
        messages.success(
            request,
            f"Interrogation report saved successfully for Accused ID: {accused_id}"
        )
        return JsonResponse({
            "status": "analysis_completed",
            "message": "All questions analyzed successfully"
        })
    return JsonResponse({"error": "POST required"}, status=400)