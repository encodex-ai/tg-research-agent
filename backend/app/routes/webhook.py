import os
import logging
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from telegram import Update
from fastapi.background import BackgroundTasks
from app.services.telegram.router import TelegramRouter

router = APIRouter()


def get_telegram_service(request: Request):
    return request.app.state.telegram_service


@router.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    telegram_service=Depends(get_telegram_service),
):
    """Handle incoming webhook updates from Telegram"""
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_service.application.bot)

        # Run middleware first
        await telegram_service.run_middleware(update)

        # Schedule the update processing in the background
        background_tasks.add_task(telegram_service.application.process_update, update)

        return Response(status_code=200)
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return Response(status_code=500)


@router.get("/set_webhook")
async def set_webhook(telegram_service=Depends(get_telegram_service)):
    url = f"{os.getenv('CLOUD_RUN_SERVICE_URL')}/webhook"

    try:
        if not telegram_service.is_setup:
            # Create and register the router before setup
            router = TelegramRouter(telegram_service)
            telegram_service.register_router(router)
            await telegram_service.setup()

        success = await telegram_service.application.bot.set_webhook(url)
        if success:
            return {"message": f"Webhook successfully set to {url}"}
        else:
            raise HTTPException(
                status_code=500, detail=f"Failed to set webhook to {url}"
            )
    except Exception as e:
        logging.error(f"Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/webhook/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}
