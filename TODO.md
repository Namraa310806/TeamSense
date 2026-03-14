# Auto Attrition Update - Added

✅ Signal in backend/meetings/signals.py: post_save Meeting → if sentiment_score changed → Celery update_attrition_task(employee_id)
✅ New task backend/meetings/tasks.py: calls calculate_attrition_risk → logs risk
✅ Ready() in backend/meetings/apps.py loads signals

**Now:** Meeting transcript → sentiment update → auto attrition recalc via Celery.

**Test:** docker-compose restart backend celery-worker, upload meeting, check logs `docker logs teamsense-celery`.

Docker up, model live. ✅

