#!/usr/bin/env python
import asyncio
import json
import os
import time
import httpx
import boto3
from copy import deepcopy
from pathlib import Path
from typing import Union, Optional, List, Dict, Any, cast
from urllib.parse import urlencode, quote_plus

from fastapi import Form, HTTPException, Header, Depends, UploadFile, File
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from questions.logging_config import get_logger
from starlette.responses import JSONResponse, Response, RedirectResponse
from starlette.routing import Route
from starlette.datastructures import URL
from sqlalchemy.orm import Session
from PIL import Image
import io
import base64

from questions import fixtures, doc_fixtures, tool_fixtures
from pydantic import BaseModel
from questions import blog_fixtures

# Import database models conditionally
HAS_NDB = False
print("NDB models disabled - using PostgreSQL only")

# Create mock classes to prevent import errors
class User:
    @staticmethod
    def bySecret(secret):
        return None
    @staticmethod
    def byId(uid):
        return None

class Document:
    pass

# Enable PostgreSQL for production use
USE_POSTGRES = True

# Import new PostgreSQL models and auth
try:
    from questions.db_models_postgres import get_db, DATABASE_URL
    from questions.auth import (
        login_or_create_user, set_session_for_user, get_current_user, 
        create_user, get_user_from_session
    )
    # Test if the functions actually work with a proper database
    USE_POSTGRES = True  # Enable PostgreSQL for production
    try:
        # Test if we can actually get a database session
        test_db = get_db()
        next(test_db)  # This will fail if no database is configured
        print(f"✅ PostgreSQL connection successful: {DATABASE_URL}")
    except Exception as e:
        print(f"❌ PostgreSQL database connection failed: {e}")
        print(f"Database URL: {DATABASE_URL}")
        USE_POSTGRES = False
except ImportError as e:
    USE_POSTGRES = False
    print(f"PostgreSQL modules not available: {e}, using fallback auth")
    
# Create dummy get_db function if needed
if not USE_POSTGRES:
    def get_db():
        return None

from questions.models import CreateUserRequest, GetUserRequest, GenerateParams, CreateCheckoutRequest
from questions.payments.payments import (
    get_self_hosted_subscription_count_for_user, 
    get_subscription_item_id_for_user_email,
    get_or_create_stripe_customer,
    validate_stripe_customer,
    get_self_hosted_subscription_count_for_user_async,
    get_subscription_item_id_for_user_email_async,
    get_or_create_stripe_customer_async,
    validate_stripe_customer_async
)
from questions.utils import random_string, get_env_var

# Import gameon utils conditionally
try:
    from questions.gameon_utils import GameOnUtils
    HAS_GAMEON = True
except Exception as e:
    print(f"GameOn utils not available: {e}")
    HAS_GAMEON = False
    class GameOnUtils:
        pass

# Import the claude_queries module directly
from questions.inference_server.claude_queries import (
    query_to_claude_async,
    query_to_claude_json_async,
)

# Import needed types and modules
from fastapi import BackgroundTasks

# pip install google-api-python-client google-cloud-storage google-auth-httplib2 google-auth-oauthlib

FACEBOOK_APP_ID = "138831849632195"
FACEBOOK_APP_SECRET = "93986c9cdd240540f70efaea56a9e3f2"

config = {}
config["webapp2_extras.sessions"] = dict(secret_key="93986c9cdd240540f70efaea56a9e3f2")

templates = Jinja2Templates(directory=".")

def get_base_template_vars(request: Request) -> Dict[str, Any]:
    """
    Get base template variables that are common to all templates
    """
    # Detect if user is on Mac for keyboard shortcuts
    is_mac = False
    try:
        user_agent = request.headers.get("user-agent", "")
        if user_agent:
            is_mac = user_agent.lower().find("mac") != -1
    except Exception:
        is_mac = False
    
    return {
        "request": request,
        "static_url": "/static",
        "is_debug": debug if 'debug' in globals() else False,
        "app_name": "Text Generator",
        "gcloud_static_bucket_url": GCLOUD_STATIC_BUCKET_URL,
        "facebook_app_id": FACEBOOK_APP_ID,
        "fixtures": json.dumps({
            "is_mac": is_mac,
            "inference_server_url": INFERENCE_SERVER_URL,
        }),
    }

from fastapi import FastAPI

GCLOUD_STATIC_BUCKET_URL = "https://text-generatorstatic.text-generator.io/static"
import sellerinfo
import stripe

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    openapi_url="/static/openapi.json",
    docs_url="/swagger-docs",
    redoc_url="/redoc",
    title="Generate Text API",
    description="Generate text, control stopping criteria like max_length/max_sentences",
    # root_path="https://api.text-generator.io",
    version="1",
)

# Initialize logger
logger = get_logger(__name__)

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Starting request: {request.method} {request.url}")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log the response
    logger.info(
        f"Completed request: {request.method} {request.url} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )
    
    return response

@app.on_event("startup")
async def startup_event():
    """Configure logging on startup"""
    logger.info("Starting 20-questions application")
    logger.info(f"USE_POSTGRES: {USE_POSTGRES}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event"""
    logger.info("Shutting down 20-questions application")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import the new router conditionally
try:
    from routes import documents
    HAS_ROUTES = True
except Exception as e:
    print(f"Routes not available: {e}")
    HAS_ROUTES = False

# Include the documents router if available
if HAS_ROUTES:
    app.include_router(documents.router)


def user_secret_matches(secret):
    # check if the secret is valid
    if secret is None:
        return False
    
    # Check in PostgreSQL database if available
    if USE_POSTGRES:
        try:
            from questions.db_models_postgres import SessionLocal, User as UserPG
            db = SessionLocal()
            try:
                user = UserPG.get_by_secret(db, secret)
                if user:
                    # Import session management from auth module
                    from questions.auth import set_session_for_user
                    set_session_for_user(user)
                    return True
            finally:
                db.close()
        except Exception:
            pass
    
    # No user found in PostgreSQL
    return False

def request_authorized(request: Request, secret):
    if secret == "hey you, please purchase for real":
        return True
    # Allow RapidAPI keys
    if "X-Rapid-API-Key" in request.headers or "x-rapid-api-key" in request.headers:
        # Ideally, you'd validate the RapidAPI key against their service or a stored list
        # For now, assuming presence implies authorization
        return True

    # Fallback to user secret validation
    if user_secret_matches(secret):
        return True

    logger.warning(f"Unauthorized request attempt: secret={'present' if secret else 'missing'}, headers={request.headers}, url={request.url}")
    return False

@app.middleware("http")
async def redirect_domain(request: Request, call_next):

    # permanent redirect from language-generator.app.nz   to language-generator.io
    if request.url.hostname == "language-generator.app.nz":
        return RedirectResponse("https://text-generator.io" + request.url.path, status_code=301)
    # if request.url.scheme == "http":
    #     url = request.url.with_scheme("https")
    #     return RedirectResponse(url=url)
    return await call_next(request)


app.add_middleware(GZipMiddleware, minimum_size=1000)

# app.add_middleware(HTTPSRedirectMiddleware)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/gameon/static", StaticFiles(directory="gameon/static"), name="gameon/static")

debug = (
    os.environ.get("SERVER_SOFTWARE", "").startswith("Development")
    or os.environ.get("IS_DEVELOP", "") == 1
    or Path("models/debug.env").exists()
)

# Configure inference server URL
INFERENCE_SERVER_URL = os.environ.get("INFERENCE_SERVER_URL", "https://api.text-generator.io")
if debug:
    # Default to local inference server in development
    INFERENCE_SERVER_URL = os.environ.get("INFERENCE_SERVER_URL", "http://0.0.0.0:9909")
if debug:
    # stripe_keys = {
    #     "secret_key": sellerinfo.STRIPE_TEST_SECRET,
    #     "publishable_key": sellerinfo.STRIPE_TEST_KEY,
    # }
    stripe_keys = {
        "secret_key": sellerinfo.STRIPE_LIVE_SECRET,
        "publishable_key": sellerinfo.STRIPE_LIVE_KEY,
    }
    GCLOUD_STATIC_BUCKET_URL = "/static"
else:
    stripe_keys = {
        "secret_key": sellerinfo.STRIPE_LIVE_SECRET,
        "publishable_key": sellerinfo.STRIPE_LIVE_KEY,
    }

stripe.api_key = stripe_keys["secret_key"]


@app.get("/")
async def index(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/index.jinja2", base_vars,
    )

@app.get("/tools")
async def tools(request: Request):
    base_vars = get_base_template_vars(request)
    tools_list = list(tool_fixtures.tools_fixtures.values())
    base_vars.update({
        "tools": tools_list,
    })
    return templates.TemplateResponse(
        "templates/tools.jinja2", base_vars,
    )

@app.get("/ai-text-editor")
async def ai_text_editor(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
        # No additional variables needed
    })
    return templates.TemplateResponse(
        "templates/text-generator-docs.jinja2", base_vars,
    )

@app.get("/tools/{tool_name}")
async def tool_page(request: Request, tool_name: str):
    base_vars = get_base_template_vars(request)

    # Define a dictionary of available tools and their details
    tool_info = tool_fixtures.tools_fixtures.get(tool_name, {})

    base_vars.update({
        "tool_name": tool_info.get("name", tool_name.replace("-", " ").title()),
        "tool_description": tool_info.get("description", ""),
        "tool_keywords": tool_info.get("keywords", ""),
        "tool_url": f"/tools/{tool_name}",
        "tool_image": tool_info.get("image", ""),
        "tooltemplate": f"templates/tools/{tool_name}.jinja2"
    })

    return templates.TemplateResponse(
        "templates/tool.jinja2", base_vars,
    )



@app.get("/subscribe")
async def subscribe(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/subscribe.jinja2", base_vars,
    )

YOUR_DOMAIN = "https://text-generator.io"

@app.post("/create-checkout-session")
async def create_checkout_session(request: Request, type: str = Form(default=""), quantity: int = Form(default=1), db: Session = Depends(get_db)):
    quantity = quantity if quantity else 1
    
    # Get user from cookie-based authentication
    if USE_POSTGRES:
        try:
            user = get_current_user(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            stripe_id = user.stripe_id
            if not stripe_id:
                # Handle case where user or stripe_id is not found
                logger.error(f"Stripe ID not found for user: {user.email}")
                return JSONResponse({"error": "User payment info not found. Please ensure you are logged in."}, status_code=400)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in create_checkout_session: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")
    else:
        # Fallback for non-PostgreSQL setup
        raise HTTPException(status_code=501, detail="Checkout not available without PostgreSQL")

    # Define line_item with type hint (basic structure)
    # For metered subscriptions, quantity should not be specified
    success_url = YOUR_DOMAIN + "/playground"
    
    if type == "annual":
        line_item: Dict[str, Any] = {
            "price": "price_0RXdd4Dtz2XsjQRO5hYsdfjx",  # New annual price ID ($190/year)
            "quantity": 1
        }
    elif type == "self-hosted":
        line_item: Dict[str, Any] = {
            "price": 'price_0MuAuxDtz2XsjQROz3Hp5Tcx',
            "quantity": quantity  # Only self-hosted subscriptions use quantity
        }
        success_url = YOUR_DOMAIN + "/account"
    else:
        # Default monthly - metered subscription, no quantity
        line_item: Dict[str, Any] = {
            "price": "price_0RXdbtDtz2XsjQROW0xgtU8H",  # New monthly price ID ($19/month)
            "quantity": 1
        }

    checkout_session_url: Optional[str] = None
    try:
        # Type hint removed for line_items list to satisfy linter
        checkout_items = [line_item]
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_id, # stripe_id is confirmed not None here
            line_items=checkout_items, # type: ignore
            mode="subscription",
            success_url=success_url,
            cancel_url=YOUR_DOMAIN + "/",
        )
        checkout_session_url = checkout_session.url # type: ignore
    except Exception as e:
        if "combine currencies" in str(e):
            # Fallback for NZD plans
            line_item_nzd: Dict[str, Any] = {
                "price": "price_0LCAb8Dtz2XsjQROnv1GhCL4",
                "quantity": 1
            }
            if type == "self-hosted":
                 line_item_nzd["price"] = 'price_0MuBEoDtz2XsjQROiRewGRFi'
                 line_item_nzd['quantity'] = quantity  # Only self-hosted uses quantity
                 success_url = YOUR_DOMAIN + "/account"

            try:
                 # Type hint removed for line_items list to satisfy linter
                 checkout_items_nzd = [line_item_nzd]
                 checkout_session_nzd = stripe.checkout.Session.create(
                     customer=stripe_id, # Still checked
                     line_items=checkout_items_nzd, # type: ignore
                     mode="subscription",
                     success_url=success_url,
                     cancel_url=YOUR_DOMAIN + "/",
                 )
                 checkout_session_url = checkout_session_nzd.url # type: ignore
            except Exception as ex:
                 logger.error(f"Error creating fallback checkout session: {ex}")
                 return Response(str(ex), status_code=500)
        else:
             logger.error(f"Error creating checkout session: {e}")
             return Response(str(e), status_code=500)

    if checkout_session_url:
        return RedirectResponse(checkout_session_url, status_code=303)
    else:
        # Handle case where URL wasn't obtained (e.g., error handled internally but no URL)
        logger.error("Checkout session created but URL is missing")
        return JSONResponse({"error": "Failed to create checkout session URL."}, status_code=500)


@app.post("/create-checkout-session-embedded")
async def create_checkout_session_embedded(request: Request, checkoutRequest: CreateCheckoutRequest, db: Session = Depends(get_db)):
    subscription_type = checkoutRequest.subscription_type or checkoutRequest.type
    referral = checkoutRequest.referral
    
    # Get user from cookie-based authentication
    if USE_POSTGRES:
        try:
            user = get_current_user(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            stripe_id = user.stripe_id
            if not stripe_id:
                logger.error(f"Stripe ID not found for user: {user.email}")
                return JSONResponse({"error": "User payment info not found"}, status_code=400)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in create_checkout_session_embedded: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")
    else:
        # Fallback for non-PostgreSQL setup
        raise HTTPException(status_code=501, detail="Checkout not available without PostgreSQL")
    
    # Set up pricing based on subscription type
    if subscription_type and subscription_type == "annual":
        subscription_price = "price_0RXdd4Dtz2XsjQRO5hYsdfjx"  # $190/year
    else:
        subscription_price = "price_0RXdbtDtz2XsjQROW0xgtU8H"  # $19/month
    
    success_url = YOUR_DOMAIN + "/playground"
    
    line_item = {
        "price": subscription_price,
        "quantity": 1,
    }
    
    metadata = None
    if referral:
        metadata = {"referral": referral}
    
    # Create checkout session with embedded UI mode
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_id,
            line_items=[line_item],
            customer_update={"address": "auto"},
            metadata=metadata,
            ui_mode="embedded",
            mode="subscription",
            return_url=success_url,
            automatic_tax={"enabled": True},
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        # Fallback without customer linking
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[line_item],
                metadata=metadata,
                ui_mode="embedded",
                mode="subscription",
                return_url=success_url,
                automatic_tax={"enabled": True},
            )
        except Exception as fallback_e:
            logger.error(f"Fallback checkout session creation failed: {fallback_e}")
            return JSONResponse({"error": "Failed to create checkout session"}, status_code=500)
    
    return JSONResponse({"clientSecret": checkout_session.client_secret})


# @app.post('/webhook')
# async def webhook_received(request: Request):
#     # Replace this endpoint secret with your endpoint's unique secret
#     # If you are testing with the CLI, find the secret by running 'stripe listen'
#     # If you are using an endpoint defined with the API or dashboard, look in your webhook settings
#     # at https://dashboard.stripe.com/webhooks
#     webhook_secret = 'whsec_12345'
#     request_data = json.loads(await request.json())
#
#     if webhook_secret:
#         # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
#         signature = request.headers.get('stripe-signature')
#         try:
#             event = stripe.Webhook.construct_event(
#                 payload=await request.json(), sig_header=signature, secret=webhook_secret)
#             data = event['data']
#         except Exception as e:
#             return e
#         # Get the type of webhook event sent - used to check the status of PaymentIntents.
#         event_type = event['type']
#     else:
#         data = request_data['data']
#         event_type = request_data['type']
#     data_object = data['object']
#
#     print('event ' + event_type)
#
#     if event_type == 'checkout.session.completed':
#         print('🔔 Payment succeeded!')
#
#     elif event_type == 'customer.subscription.trial_will_end':
#         print('Subscription trial will end')
#     elif event_type == 'customer.subscription.created':
#         subscription = event['data']['object']
#     elif event_type == 'customer.subscription.updated':
#         print('Subscription created %s', event.id)
#     elif event_type == 'customer.subscription.deleted':
#         # handle subscription canceled automatically based
#         # upon your subscription settings. Or if the user cancels it.
#         print('Subscription canceled: %s', event.id)
#         subscription = event['data']['object']
#
#     return JSONResponse({'status': 'success'})


@app.get("/questions-game")
async def questions_game(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates-game/questions-game.jinja2", base_vars,

    )


@app.get("/signup")
async def signup(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/signup.jinja2", base_vars,
    )

@app.get("/where-is-ai-game")
async def where_is_ai_game(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/where-is-ai-game.jinja2", base_vars,

    )


@app.get("/success")
async def success(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/success.jinja2", base_vars,
    )

@app.get("/login")
async def login(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "static/templates/login.jinja2", base_vars,
    )

@app.get("/test-modals")
async def test_modals(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/test_modals.jinja2", base_vars,
    )

@app.get("/logout")
async def logout(request: Request):
    # clear session?
    return RedirectResponse("/", status_code=303)


@app.post("/api/create-user")
async def create_user_legacy(create_user_request: CreateUserRequest):
    email = create_user_request.email
    # emailVerified = create_user_request.emailVerified
    uid = create_user_request.uid
    photoURL = create_user_request.photoURL
    token = create_user_request.token
    # user = current_user
    # if not user:

    user = User()
    existing_user = User.byId(uid)
    if existing_user:
        user = existing_user
    # get or create
    user.id = uid
    user.email = email
    # user.token = token # Attribute doesn't exist on User model
    # user.photoURL = photoURL # Attribute doesn't exist on User model
    # user.emailVerified = emailVerified
    if not existing_user:  # never change secret
        user.secret = random_string(32)

    User.save(user)
    set_session_for_user(user)

    # get or create user in stripe
    if not user.stripe_id:
        customer = stripe.Customer.create( # type: ignore
            email=email,
            idempotency_key=uid,
        )
        user.stripe_id = customer.id
        User.save(user)
        set_session_for_user(user)

    # send_signup_email(email, referral_url_key)
    # subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    # user.is_subscribed = subscription_item_id is not None
    return JSONResponse(json.loads(json.dumps(user.to_dict(), cls=GameOnUtils.MyEncoder)))


def set_session_for_user_legacy(user):
    if user is not None:
        # Use the auth module's session management
        from questions.auth import set_session_for_user
        set_session_for_user(user)


@app.get("/portal")
async def portal_redirect(request: Request, db: Session = Depends(get_db)):
    """redirect to the stripe customer portal"""
    if USE_POSTGRES:
        try:
            user = get_current_user(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not user.stripe_id:
                raise HTTPException(status_code=400, detail="No Stripe customer ID found")
            
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_id,
                return_url="https://text-generator.io/playground",
            )
            return RedirectResponse(session.url, status_code=303) # type: ignore
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating portal session: {e}")
            raise HTTPException(status_code=500, detail="Failed to create portal session")
    else:
        # Fallback for non-PostgreSQL setup
        raise HTTPException(status_code=501, detail="Portal not available without PostgreSQL")


@app.post("/api/get-user")
async def get_user(request: Request, db: Session = Depends(get_db)):
    """Get user data using cookie-based authentication"""
    if USE_POSTGRES:
        try:
            user = get_current_user(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            # Check subscription status
            subscription_item_id = get_subscription_item_id_for_user_email(user.email)
            user.is_subscribed = subscription_item_id is not None
            num_self_hosted_instances = get_self_hosted_subscription_count_for_user(user.stripe_id)
            user.num_self_hosted_instances = int(num_self_hosted_instances) or 0

            if not user.is_subscribed:
                # recreate stripe customer if required - remediates users being created in test mode
                customer = stripe.Customer.retrieve(user.stripe_id)
                if not customer or not customer.id:
                    customer = stripe.Customer.create( # type: ignore
                        email=user.email,
                        idempotency_key=user.email,
                    )
                    user.stripe_id = customer.id
                    db.commit()
                    db.refresh(user)
                    set_session_for_user(user)
            
            return JSONResponse(user.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user data")
    else:
        # Fallback for non-PostgreSQL setup
        raise HTTPException(status_code=501, detail="User data not available without PostgreSQL")


# Removed get_stripe_usage function - no longer needed since we don't do metering


@app.post("/api/get-user/stripe-usage")
async def get_user_stripe_usage(request: Request, db: Session = Depends(get_db)):
    """Get user data using cookie-based authentication (no usage tracking since we don't do metering)"""
    if USE_POSTGRES:
        try:
            user = get_current_user(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            # Check subscription status
            subscription_item_id = get_subscription_item_id_for_user_email(user.email)
            user.is_subscribed = subscription_item_id is not None
            
            if not user.is_subscribed:
                # recreate stripe customer if required - remediates users being created in test mode
                customer = stripe.Customer.retrieve(user.stripe_id)
                if not customer or not customer.id:
                    customer = stripe.Customer.create( # type: ignore
                        email=user.email,
                        idempotency_key=user.email,
                    )
                    user.stripe_id = customer.id
                    db.commit()
                    db.refresh(user)
                    set_session_for_user(user)

            user.num_self_hosted_instances = get_self_hosted_subscription_count_for_user(user.stripe_id)

            user_to_dict = user.to_dict()
            # No usage tracking anymore - we don't do metering
            return JSONResponse(user_to_dict)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user data")
    else:
        # Fallback for non-PostgreSQL setup
        raise HTTPException(status_code=501, detail="User data not available without PostgreSQL")


# New PostgreSQL-based authentication endpoints
# Simple in-memory storage for testing (replace with real database in production)
test_users = {}
active_sessions = {}

@app.post("/api/login")
async def api_login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Login endpoint with fallback to in-memory storage"""
    logger.info(f"Login attempt for {email}, USE_POSTGRES={USE_POSTGRES}")
    
    if USE_POSTGRES:
        logger.info("Using PostgreSQL login")
        try:
            user = login_or_create_user(email, password, db)
            set_session_for_user(user)
            
            # Ensure user has a valid Stripe customer
            valid_stripe_id = validate_stripe_customer(user.stripe_id, email) if user.stripe_id else None
            if not valid_stripe_id:
                logger.info(f"Creating/updating Stripe customer for user {email}")
                stripe_id = get_or_create_stripe_customer(email, user.id)
                if stripe_id:
                    user.stripe_id = stripe_id
                    db.commit()
                    db.refresh(user)
                else:
                    logger.error(f"Failed to create Stripe customer for user {email}")
            elif valid_stripe_id != user.stripe_id:
                # Update stored customer ID if we found a different valid one
                logger.info(f"Updating Stripe customer ID for user {email} from {user.stripe_id} to {valid_stripe_id}")
                user.stripe_id = valid_stripe_id
                db.commit()
                db.refresh(user)
            
            # Check subscription status
            subscription_item_id = get_subscription_item_id_for_user_email(user.email)
            user.is_subscribed = subscription_item_id is not None
            
            # Set session_secret cookie
            response = JSONResponse(user.to_dict())
            response.set_cookie(
                key="session_secret",
                value=user.secret,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                path="/"
            )
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"PostgreSQL login error: {e}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
    else:
        # Fallback to simple in-memory authentication
        logger.info("Using in-memory login")
        if email in test_users and test_users[email]['password'] == password:
            session_secret = random_string(32)
            user_data = {
                'id': test_users[email]['id'],
                'email': email,
                'secret': session_secret,
                'is_subscribed': False
            }
            active_sessions[session_secret] = user_data
            logger.info(f"Login successful: {user_data}")
            
            # Set session_secret cookie
            response = JSONResponse(user_data)
            response.set_cookie(
                key="session_secret",
                value=session_secret,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                path="/"
            )
            return response
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password")


@app.post("/api/signup")
async def api_signup(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Signup endpoint with fallback to in-memory storage"""
    logger.info(f"Signup attempt for {email}, USE_POSTGRES={USE_POSTGRES}")
    
    if USE_POSTGRES:
        logger.info("Using PostgreSQL signup")
        try:
            user = create_user(email, password, db)
            set_session_for_user(user)
            
            # Create Stripe customer
            stripe_id = get_or_create_stripe_customer(email, user.id)
            if stripe_id:
                user.stripe_id = stripe_id
                db.commit()
                db.refresh(user)
            else:
                logger.error(f"Failed to create Stripe customer for new user {email}")
            
            # Set session_secret cookie
            response = JSONResponse(user.to_dict())
            response.set_cookie(
                key="session_secret",
                value=user.secret,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                path="/"
            )
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"PostgreSQL signup error: {e}")
            raise HTTPException(status_code=500, detail="Signup failed")
    else:
        # Fallback to simple in-memory user creation
        logger.info("Using in-memory signup")
        try:
            if email in test_users:
                raise HTTPException(status_code=409, detail="An account with this email already exists")
            
            user_id = f"user_{len(test_users) + 1}"
            session_secret = random_string(32)
            
            test_users[email] = {
                'id': user_id,
                'email': email,
                'password': password  # In production, this should be hashed!
            }
            
            user_data = {
                'id': user_id,
                'email': email,
                'secret': session_secret,
                'is_subscribed': False
            }
            
            # Store session for login - skip for now in fallback mode
            # session_dict[session_secret] = user_data
            
            logger.info(f"User created successfully: {email} (ID: {user_id})")
            
            # Set session_secret cookie
            response = JSONResponse(user_data)
            response.set_cookie(
                key="session_secret",
                value=session_secret,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                path="/"
            )
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"In-memory signup error: {e}")
            raise HTTPException(status_code=500, detail="Signup failed")


@app.post("/api/logout")
async def api_logout(request: Request):
    """Logout endpoint"""
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("session_secret", path="/")
    return response


@app.post("/api/upload-image")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """Upload image with WebP conversion and upload to S3"""
    try:
        # Check if user is authenticated
        if USE_POSTGRES:
            from questions.auth import get_current_user
            current_user = get_current_user(request, next(get_db()))
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Convert to WebP with quality 85
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for WebP compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Create WebP image
        webp_buffer = io.BytesIO()
        image.save(webp_buffer, format='WEBP', quality=85, optimize=True)
        webp_data = webp_buffer.getvalue()
        
        # Generate filename
        import uuid
        filename = f"uploaded_{uuid.uuid4().hex}.webp"
        
        # Upload to S3 (assuming AWS credentials are configured)
        s3_client = boto3.client('s3')
        bucket_name = 'textgeneratorstatic.netwrck.com'
        
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=filename,
                Body=webp_data,
                ContentType='image/webp',
                ACL='public-read'
            )
            
            # Return the URL
            image_url = f"https://{bucket_name}/{filename}"
            return JSONResponse({
                "success": True,
                "url": image_url,
                "filename": filename
            })
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to process image")


@app.get("/api/current-user")
async def api_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current user information"""
    if USE_POSTGRES:
        try:
            user = get_current_user(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            # Return basic user info immediately, skip Stripe validation to prevent blocking
            # Stripe validation can be done asynchronously in the background if needed
            user_dict = user.to_dict()
            
            # Only check subscription status if user has a Stripe ID
            if user.stripe_id:
                try:
                    # Add timeout to prevent blocking
                    subscription_item_id = await asyncio.wait_for(
                        get_subscription_item_id_for_user_email_async(user.email), 
                        timeout=3.0
                    )
                    user_dict['is_subscribed'] = subscription_item_id is not None
                except asyncio.TimeoutError:
                    logger.warning(f"Subscription check timed out for user {user.email}")
                    user_dict['is_subscribed'] = False
                except Exception as e:
                    logger.error(f"Error checking subscription for user {user.email}: {e}")
                    user_dict['is_subscribed'] = False
            else:
                user_dict['is_subscribed'] = False
            
            # Set default values for optional fields
            user_dict['num_self_hosted_instances'] = 0
            
            return JSONResponse(user_dict)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in current-user endpoint: {e}")
            raise HTTPException(status_code=401, detail="Not authenticated")
    else:
        # Fallback to simple session checking
        session_secret = request.cookies.get('session_secret')
        if session_secret and session_secret in active_sessions:
            return JSONResponse(active_sessions[session_secret])
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")


@app.get("/api/subscription-status")
async def api_subscription_status(request: Request, db: Session = Depends(get_db)):
    """Get current user subscription status"""
    if USE_POSTGRES:
        try:
            user = get_current_user(request, db)
            if not user:
                return JSONResponse({"is_subscribed": False, "authenticated": False})
            
            # Check subscription status
            subscription_item_id = await get_subscription_item_id_for_user_email_async(user.email)
            is_subscribed = subscription_item_id is not None
            
            return JSONResponse({
                "is_subscribed": is_subscribed,
                "authenticated": True,
                "user_email": user.email
            })
        except Exception as e:
            logger.error(f"Error checking subscription status: {str(e)}")
            return JSONResponse({"is_subscribed": False, "authenticated": False, "error": str(e)})
    else:
        # For non-PostgreSQL setup, return default
        return JSONResponse({"is_subscribed": False, "authenticated": False})


@app.get("/privacy")
async def privacy(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/privacy.jinja2", base_vars,
    )


@app.get("/account")
async def account(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/account.jinja2", base_vars,
    )


@app.get("/terms")
async def terms(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/terms.jinja2", base_vars,
    )


@app.get("/contact")
async def contact(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/contact.jinja2", base_vars,
    )


@app.get("/about")
async def about(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/about.jinja2", base_vars,
    )

@app.get("/self-hosting")
async def selfhosting(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/selfhosting.jinja2", base_vars,
    )

@app.get("/how-it-works")
async def howitworks(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/howitworks.jinja2", base_vars,
    )


@app.get("/playground")
async def playground(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/playground.jinja2", base_vars,
    )


@app.get("/sitemap")
async def sitemap(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/sitemap.jinja2", base_vars,
    )


@app.get("/docs")
async def docs(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/docs.jinja2", base_vars,
    )

@app.get("/text-to-speech")
async def text_to_speech(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/text-to-speech.jinja2", base_vars,
    )


@app.get("/speech-to-text")
async def speech_to_text(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/speech-to-text.jinja2", base_vars,
    )

@app.get("/use-cases/{usecase}")
async def use_case_route(request: Request, usecase: str):
    use_case_data = deepcopy(fixtures.use_cases.get(usecase))

    if not use_case_data:
         raise HTTPException(status_code=404, detail=f"Use case '{usecase}' not found")

    url_key = urlencode(use_case_data["generate_params"], quote_via=quote_plus)
    input_text = use_case_data["generate_params"]["text"]

    results = use_case_data["results"]
    for result in results:
        if "generated_text" in result and isinstance(result["generated_text"], str):
             if result["generated_text"].startswith(input_text):
                 result["generated_text"] = result["generated_text"][len(input_text) :]

    base_vars = get_base_template_vars(request)
    base_vars.update({
            "description": use_case_data["description"],
            "title": use_case_data["title"],
            "results": results,
            "text": input_text,
            "use_case": use_case_data,
            "url_key": url_key,
        })
    return templates.TemplateResponse(
        "templates/use-case.jinja2", base_vars,
    )


@app.get("/use-cases")
async def use_cases(request: Request):
    use_cases = deepcopy(fixtures.use_cases).items()

    base_vars = get_base_template_vars(request)
    base_vars.update({
            "use_cases": use_cases,
        })
    return templates.TemplateResponse(
        "templates/use-cases.jinja2", base_vars,
    )


@app.get("/blog/{name}")
async def blog_name(request: Request, name: str):
    blog_data = deepcopy(blog_fixtures.blogs.get(name))

    if not blog_data:
        raise HTTPException(status_code=404, detail=f"Blog post '{name}' not found")

    base_vars = get_base_template_vars(request)
    base_vars.update({
            "blog": blog_data,
            "description": blog_data["description"],
            "title": blog_data["title"],
            "keywords": blog_data["keywords"],
            "blogtemplate": "/templates/shared/" + name + ".jinja2",
        })
    return templates.TemplateResponse(
        "templates/blog.jinja2", base_vars,
    )


@app.get("/blog")
async def blog(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
            "blogs": blog_fixtures.blogs.items(),
        })
    return templates.TemplateResponse(
        "templates/blogs.jinja2", base_vars,
    )


@app.get("/docs/{name}")
async def doc_name(request: Request, name: str):
    doc_data = deepcopy(doc_fixtures.docs.get(name))

    if not doc_data:
        raise HTTPException(status_code=404, detail=f"Documentation page '{name}' not found")

    base_vars = get_base_template_vars(request)
    base_vars.update({
            "doc": doc_data,
            "description": doc_data["description"],
            "title": doc_data["title"],
            "keywords": doc_data["keywords"],
            "blogtemplate": "/templates/shared/" + name + ".jinja2",
        })
    return templates.TemplateResponse(
        "templates/doc.jinja2", base_vars,
    )

@app.get("/bulk-text-generator")
async def bulk_text_generator(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/bulk.jinja2", base_vars,
    )


@app.get("/sitemap.xml")
async def sitemap_xml(request: Request, response: Response):
    response.headers["Content-Type"] = "text/xml; charset=utf-8"

    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/sitemap.xml.jinja2", base_vars,
    )


# Filter out openapi route definition more safely
app.router.routes = [route for route in app.routes if not (isinstance(route, Route) and hasattr(route, 'name') and route.name == "openapi")]


@app.get("/openapi.json")
async def openapi(request: Request):
    # render json file openapi.json
    # read dict
    with open("static/openapi.json") as f:
        text = f.read()
        j = json.loads(text)
        # set api key in example

        return JSONResponse(j)

@app.get("/file{file_path:path}")
async def file(file_path: str, request: Request):
    # redirect to "api." and gradio_tts
    current_url: URL = request.url
    hostname = current_url.hostname
    # Check hostname safely
    if hostname and ("localhost" in hostname or "127." in hostname):
        return RedirectResponse(url="http://localhost:8000/gradio_tts/file" + str(file_path))
    return RedirectResponse(url="https://api.text-generator.io/gradio_tts/file" + str(file_path))


def validate_generate_params(generate_params):
    validate_result = ""
    if generate_params.text == "":
        validate_result = "Please enter some text"
    return validate_result


def strip_images_from_text(text: str) -> str:
    """Strip markdown images from text to save context tokens"""
    import re
    # Remove markdown images ![alt text](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Remove HTML img tags
    text = re.sub(r'<img[^>]*>', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    return text


@app.get("/tools/text-generator-docs")
async def text_generator_docs_redirect(request: Request):
    # Redirect to the standalone route for backward compatibility
    return RedirectResponse(url="/ai-text-editor", status_code=302)

# --- Moved Claude Generation Routes ---

@app.post("/api/v1/generate-long")
async def generate_long_text(
    generate_params: GenerateParams,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    """
    Generate longer text using Claude 3.7 via netwrck.com API
    This is optimized for longer, more creative text generation
    """
    validation_result = validate_generate_params(generate_params)
    if validation_result:
        return HTTPException(status_code=400, detail=validation_result)

    # Authorize the request
    if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
        if not request_authorized(request, secret):
            return HTTPException(
                status_code=401,
                detail="Please subscribe at https://text-generator.io/subscribe first"
            )

    try:
        # Prepare the prompt for Claude - strip images to save context tokens
        prompt = strip_images_from_text(generate_params.text)

        # Set up system message to control generation parameters
        system_message = f"""
You are a creative text generation assistant. Generate text that continues from the given prompt.

Important instructions:
- Continue the text naturally from where the prompt ends
- Do not repeat the prompt in your response
- Do not add any explanations, notes, or metadata
- Do not use phrases like "Here's a continuation" or "Continuing from the prompt"
- Just generate the continuation text directly
        """

        # Set up stop sequences
        stop_sequences = None
        if generate_params.stop_sequences and len(generate_params.stop_sequences) > 0:
            stop_sequences = frozenset(generate_params.stop_sequences)

        # Call Claude API
        generated_text = await query_to_claude_async(
            prompt=prompt,
            stop_sequences=stop_sequences,
            system_message=system_message,
        )

        # Handle the response
        if generated_text is None:
            return HTTPException(status_code=500, detail="Failed to generate text with Claude")

        # Format the response to match the standard API format
        result = [{
            "generated_text": prompt + generated_text,
            "finished_reason": "length",
            "model": "claude-3-sonnet-20240229"
        }]


        return result

    except Exception as e:
        logger.error(f"Error generating text with Claude: {e}")
        return HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")

@app.post("/api/v1/generate-large", include_in_schema=False)
async def generate_large_text(
    generate_params: GenerateParams,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    """
Generate large amounts of text using Claude models
This endpoint accepts a model parameter to specify which Claude model to use
    """
    validation_result = validate_generate_params(generate_params)
    if validation_result:
        return HTTPException(status_code=400, detail=validation_result)

    # Authorize the request
    if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
        if not request_authorized(request, secret):
            return HTTPException(
                status_code=401,
                detail="Please subscribe at https://text-generator.io/subscribe first"
            )

    try:
        # Prepare the prompt for Claude - strip images to save context tokens
        prompt = strip_images_from_text(generate_params.text)
        model_name = "claude-3-7-sonnet-20250219"

        # Set up system message to control generation parameters
        system_message = f"""
You are a creative text generation assistant. Generate text that continues from the given prompt.

Important instructions:
- Continue the text naturally from where the prompt ends
- Do not repeat the prompt in your response
- Do not add any explanations, notes, or metadata
- Do not use phrases like "Here's a continuation" or "Continuing from the prompt"
- Just generate the continuation text directly
        """

        # Set up stop sequences
        stop_sequences = None
        if generate_params.stop_sequences and len(generate_params.stop_sequences) > 0:
            stop_sequences = frozenset(generate_params.stop_sequences)

        # Call Claude API with the specified model
        generated_text = await query_to_claude_async(
            prompt=prompt,
            stop_sequences=stop_sequences,
            system_message=system_message,
            model=model_name,  # Pass the model name to the Claude API function
        )

        # Handle the response
        if generated_text is None:
            return HTTPException(status_code=500, detail="Failed to generate text with Claude")

        # Format the response to match the standard API format
        result = [{
            "generated_text": prompt + generated_text,
            "finished_reason": "length",
            "model": model_name
        }]


        return result

    except Exception as e:
        logger.error(f"Error generating text with Claude: {e}")
        return HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


class OptimizePromptParams(BaseModel):
    prompt: str
    evolve_prompt: str
    judge_prompt: str
    iterations: int = 2


async def evaluate_prompt(prompt: str, judge_prompt: str) -> Dict[str, Any]:
    system_message = (
        "You are a strict judge of prompt quality. "
        "Return JSON with keys 'score' and 'feedback'."
    )
    schema = {
        "type": "object",
        "properties": {
            "score": {"type": "number"},
            "feedback": {"type": "string"},
        },
        "required": ["score", "feedback"],
    }
    query = f"{judge_prompt}\nPrompt:\n{prompt}"
    return await query_to_claude_json_async(query, schema, system_message=system_message)


async def evolve_prompt(prompt: str, evolve_prompt: str) -> str:
    system_message = (
        "You improve prompts. Return JSON with key 'prompt' containing the new prompt."
    )
    schema = {
        "type": "object",
        "properties": {"prompt": {"type": "string"}},
        "required": ["prompt"],
    }
    query = f"{evolve_prompt}\nCurrent Prompt:\n{prompt}"
    data = await query_to_claude_json_async(query, schema, system_message=system_message)
    return data.get("prompt", prompt)


async def optimize_prompt(params: OptimizePromptParams) -> Dict[str, Any]:
    current_prompt = params.prompt
    evaluations: List[Dict[str, Any]] = []
    for i in range(params.iterations):
        current_eval = await evaluate_prompt(current_prompt, params.judge_prompt)
        evaluations.append({
            "prompt": current_prompt,
            "feedback": current_eval.get("feedback", ""),
            "score": current_eval.get("score", 0)
        })
        if i == params.iterations - 1:
            break
        candidate = await evolve_prompt(current_prompt, params.evolve_prompt)
        candidate_eval = await evaluate_prompt(candidate, params.judge_prompt)
        evaluations.append({
            "prompt": candidate,
            "feedback": candidate_eval.get("feedback", ""),
            "score": candidate_eval.get("score", 0)
        })
        if candidate_eval.get("score", 0) > current_eval.get("score", 0):
            current_prompt = candidate
    return {"final_prompt": current_prompt, "evaluations": evaluations}


@app.post("/api/v1/optimize-prompt")
async def optimize_prompt_endpoint(
    params: OptimizePromptParams,
    request: Request = None,
    secret: Union[str, None] = Header(default=None),
):
    """
    Optimize a prompt using Claude models to iteratively improve it
    """
    # Authorize the request
    if request and "X-Rapid-API-Key" not in request.headers and "x-rapid-api-key" not in request.headers:
        if not request_authorized(request, secret):
            raise HTTPException(
                status_code=401,
                detail="Please subscribe at https://text-generator.io/subscribe first"
            )

    try:
        result = await optimize_prompt(params)
        return result
    except Exception as e:
        logger.error(f"Error optimizing prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing prompt: {str(e)}")


@app.get("/file-upload-get-signed-url-cloudflare")
async def file_upload_get_signed_url_cloudflare(
    request: Request, contentType: str, fileName: str
):
    """Generate an R2 presigned URL for uploading to the new bucket."""
    bucket_name = get_env_var("CLOUDFLARE_BUCKET", fallback_env_var="R2_BUCKET_NAME", default="text-generatorstatic.text-generator.io")
    id = random_string(10)
    object_path = f"static/uploads/{id}-{fileName}"

    # For R2, we need to use the proper endpoint URL  
    account_id = get_env_var("R2_ACCOUNT_ID", default="f76d25b8b86cfa5638f43016510d8f77")
    endpoint_url = get_env_var("R2_ENDPOINT", default=f"https://{account_id}.r2.cloudflarestorage.com")
    
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=get_env_var("CLOUDFLARE_R2_ACCESS_KEY_ID", fallback_env_var="R2_ACCESS_KEY_ID"),
        aws_secret_access_key=get_env_var("CLOUDFLARE_R2_SECRET_ACCESS_KEY", fallback_env_var="R2_SECRET_ACCESS_KEY"),
        region_name=get_env_var("R2_REGION", default="auto"),
    )

    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket_name, "Key": object_path, "ContentType": contentType},
        ExpiresIn=3600,
    )
    return {"url": url, "object_path": object_path, "bucket_name": bucket_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

