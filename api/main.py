from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Depends
import fitz


@app.post("/onboard", status_code=201)
async def onboard(
    background_tasks: BackgroundTasks,
    resume: UploadFile = File(...),
    preferences: str = Form(...),  # JSON string
    db: AsyncSession = Depends(get_db),
):
    prefs = UserPreferences.model_validate_json(preferences)

    user = User(name=prefs.name, email=prefs.email)
    db.add(user); await db.flush()

    file_bytes = await resume.read()
    raw_text   = extract_raw_text(file_bytes)
    sections   = split_into_sections(raw_text)
    bullets    = extract_bullets(sections.get("experience",""))

    resume_rec = Resume(
        user_id=user.id, filename=resume.filename,
        raw_text=raw_text, sections=sections,
        bullets=bullets, preferences=prefs.model_dump(),
    )
    db.add(resume_rec); await db.flush()

    background_tasks.add_task(
        start_job_search,
        resume_id=str(resume_rec.id),
        preferences=prefs.model_dump()
    )
    return {"resume_id": str(resume_rec.id), "user_id": str(user.id)}