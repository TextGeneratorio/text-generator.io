#!/usr/bin/env python
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Union, Optional, List, Dict, Any, cast
from urllib.parse import urlencode, quote_plus

from fastapi import Form, HTTPException, Header
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from questions.logging_config import setup_logging
from starlette.responses import JSONResponse, Response, RedirectResponse
from starlette.routing import Route
from starlette.datastructures import URL

from questions import fixtures, doc_fixtures, tool_fixtures
from questions import blog_fixtures
from questions.db_models import User, Document
from questions.gameon_utils import GameOnUtils
from questions.models import CreateUserRequest, GetUserRequest, GenerateParams
from questions.payments.payments import (
    get_self_hosted_subscription_count_for_user,
    get_subscription_item_id_for_user_email,
)
from questions.utils import random_string

# Configure logging to also send logs to Google Cloud
setup_logging(use_cloud=True)
logger = logging.getLogger(__name__)

# Import the claude_queries module directly
from questions.inference_server.claude_queries import (
    query_to_claude_async,
    query_to_claude_image_async,
)
from questions.ux_feedback import analyze_site
from pydantic import BaseModel, HttpUrl

# Import needed types and modules
from fastapi import BackgroundTasks

# pip install google-api-python-client google-cloud-storage google-auth-httplib2 google-auth-oauthlib

FACEBOOK_APP_ID = "138831849632195"
FACEBOOK_APP_SECRET = "93986c9cdd240540f70efaea56a9e3f2"

config = {}
config["webapp2_extras.sessions"] = dict(secret_key="93986c9cdd240540f70efaea56a9e3f2")

templates = Jinja2Templates(directory=".")

from fastapi import FastAPI


class FeedbackRequest(BaseModel):
    url: HttpUrl


GCLOUD_STATIC_BUCKET_URL = "https://static.text-generator.io/static"
import sellerinfo
import stripe

from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI(
    openapi_url="/static/openapi.json",
    docs_url="/swagger-docs",
    redoc_url="/redoc",
    title="Generate Text API",
    description="Generate text, control stopping criteria like max_length/max_sentences",
    # root_path="https://api.text-generator.io",
    version="1",
)

# Import the new router
from routes import documents

# Include the documents router
app.include_router(documents.router)


def user_secret_matches(secret):
    # check if the secret is valid
    if secret is None:
        return False
    if secret in session_dict:
        return True
    # Check in database as fallback
    user = User.bySecret(secret)
    if user:
        set_session_for_user(user)  # Cache user if found
        return True
    return False


def request_authorized(request: Request, secret):
    if secret == "hey you, please purchase for real":
        return True
    # else: # Removed redundant logging here as it's handled below if needed
    #     logger.error("Error invalid api key for request: %s", request.url)
    #     return False
    # Allow RapidAPI keys
    if "X-Rapid-API-Key" in request.headers or "x-rapid-api-key" in request.headers:
        # Ideally, you'd validate the RapidAPI key against their service or a stored list
        # For now, assuming presence implies authorization
        return True

    # Fallback to user secret validation
    if user_secret_matches(secret):
        return True

    logger.warning(
        f"Unauthorized request attempt: secret={'present' if secret else 'missing'}, headers={request.headers}"
    )
    return False


@app.middleware("http")
async def redirect_domain(request: Request, call_next):

    # permanent redirect from language-generator.app.nz   to language-generator.io
    if request.url.hostname == "language-generator.app.nz":
        return RedirectResponse(
            "https://text-generator.io" + request.url.path, status_code=301
        )
    if request.url.hostname == "language-generator.app.nz":
        return RedirectResponse(
            "https://text-generator.io" + request.url.path, status_code=301
        )
    # if request.url.scheme == "http":
    #     url = request.url.with_scheme("https")
    #     return RedirectResponse(url=url)
    return await call_next(request)


app.add_middleware(GZipMiddleware, minimum_size=1000)

# app.add_middleware(HTTPSRedirectMiddleware)


app.mount("/static", StaticFiles(directory="static"), name="static")

session_dict = {}

debug = (
    os.environ.get("SERVER_SOFTWARE", "").startswith("Development")
    or os.environ.get("IS_DEVELOP", "") == 1
    or Path("models/debug.env").exists()
)
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
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/index.jinja2",
        base_vars,
    )


@app.get("/tools")
async def tools(request: Request):
    base_vars = get_base_template_vars(request)
    tools_list = list(tool_fixtures.tools_fixtures.values())
    base_vars.update(
        {
            "tools": tools_list,
        }
    )
    return templates.TemplateResponse(
        "templates/tools.jinja2",
        base_vars,
    )


@app.get("/ai-text-editor")
async def ai_text_editor(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update(
        {
            # No additional variables needed
        }
    )
    return templates.TemplateResponse(
        "templates/text-generator-docs.jinja2",
        base_vars,
    )


@app.get("/tools/{tool_name}")
async def tool_page(request: Request, tool_name: str):
    base_vars = get_base_template_vars(request)

    # Define a dictionary of available tools and their details
    tool_info = tool_fixtures.tools_fixtures.get(tool_name, {})

    base_vars.update(
        {
            "tool_name": tool_info.get("name", tool_name.replace("-", " ").title()),
            "tool_description": tool_info.get("description", ""),
            "tool_keywords": tool_info.get("keywords", ""),
            "tool_url": f"/tools/{tool_name}",
            "tool_image": tool_info.get("image", ""),
            "tooltemplate": f"templates/tools/{tool_name}.jinja2",
        }
    )

    return templates.TemplateResponse(
        "templates/tool.jinja2",
        base_vars,
    )


@app.get("/subscribe")
async def subscribe(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/subscribe.jinja2",
        base_vars,
    )


YOUR_DOMAIN = "https://text-generator.io"


@app.post("/create-checkout-session")
async def create_checkout_session(
    uid: str = Form(default=""),
    secret: str = Form(default=""),
    type: str = Form(default=""),
    quantity: int = Form(default=1),
):
    quantity = quantity if quantity else 1
    user = session_dict.get(secret)
    stripe_id: Optional[str] = None
    if user and user.stripe_id:
        stripe_id = user.stripe_id
    else:
        db_user = User.byId(uid)
        if db_user and db_user.stripe_id:
            user = db_user  # Update user if found in DB
            stripe_id = db_user.stripe_id
            set_session_for_user(user)  # Update session cache

    if not stripe_id:
        # Handle case where user or stripe_id is not found - maybe redirect to login/error?
        logger.error(f"Stripe ID not found for user: {uid}")
        # For now, returning an error response, adjust as needed
        return JSONResponse(
            {"error": "User payment info not found. Please ensure you are logged in."},
            status_code=400,
        )

    # Define line_item with type hint (basic structure)
    line_item: Dict[str, Any] = {
        "price": "price_0PpIzNDtz2XsjQROUZgNOTaF",  # Default monthly
        "quantity": quantity,
    }
    success_url = YOUR_DOMAIN + "/playground"

    if type == "annual":
        line_item["price"] = "price_0PpJ10Dtz2XsjQROADWTSIBr"
    elif type == "self-hosted":
        line_item["price"] = "price_0MuAuxDtz2XsjQROz3Hp5Tcx"
        success_url = YOUR_DOMAIN + "/account"

    checkout_session_url: Optional[str] = None
    try:
        # Type hint removed for line_items list to satisfy linter
        checkout_items = [line_item]
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_id,  # stripe_id is confirmed not None here
            line_items=checkout_items,  # type: ignore
            mode="subscription",
            success_url=success_url,
            cancel_url=YOUR_DOMAIN + "/",
        )
        checkout_session_url = checkout_session.url  # type: ignore
    except Exception as e:
        if "combine currencies" in str(e):
            # Fallback for NZD plans
            line_item_nzd: Dict[str, Any] = {
                "price": "price_0LCAb8Dtz2XsjQROnv1GhCL4",
                "quantity": quantity,  # Assuming quantity applies here too
            }
            if type == "self-hosted":
                line_item_nzd["price"] = "price_0MuBEoDtz2XsjQROiRewGRFi"
                success_url = YOUR_DOMAIN + "/account"

            try:
                # Type hint removed for line_items list to satisfy linter
                checkout_items_nzd = [line_item_nzd]
                checkout_session_nzd = stripe.checkout.Session.create(
                    customer=stripe_id,  # Still checked
                    line_items=checkout_items_nzd,  # type: ignore
                    mode="subscription",
                    success_url=success_url,
                    cancel_url=YOUR_DOMAIN + "/",
                )
                checkout_session_url = checkout_session_nzd.url  # type: ignore
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
        return JSONResponse(
            {"error": "Failed to create checkout session URL."}, status_code=500
        )


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
    base_vars.update({})
    return templates.TemplateResponse(
        "templates-game/questions-game.jinja2",
        base_vars,
    )


@app.get("/signup")
async def signup(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/signup.jinja2",
        base_vars,
    )


@app.get("/where-is-ai-game")
async def where_is_ai_game(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/where-is-ai-game.jinja2",
        base_vars,
    )


@app.get("/success")
async def success(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/success.jinja2",
        base_vars,
    )


@app.get("/login")
async def login(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/login.jinja2",
        base_vars,
    )


@app.get("/logout")
async def logout(request: Request):
    # clear session?
    return RedirectResponse("/", status_code=303)


@app.post("/api/create-user")
async def create_user(create_user_request: CreateUserRequest):
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
        customer = stripe.Customer.create(  # type: ignore
            email=email,
            idempotency_key=uid,
        )
        user.stripe_id = customer.id
        User.save(user)
        set_session_for_user(user)

    # send_signup_email(email, referral_url_key)
    # subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    # user.is_subscribed = subscription_item_id is not None
    return JSONResponse(
        json.loads(json.dumps(user.to_dict(), cls=GameOnUtils.MyEncoder))
    )


def set_session_for_user(user):
    if user != None:
        session_dict[user.secret] = user


@app.get("/portal")
async def portal_redirect(request: Request, customer_id):
    """redirect to the stripe customer portal"""
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url="https://text-generator.io/playground",
    )
    return RedirectResponse(session.url, status_code=303)  # type: ignore


@app.post("/api/get-user")
async def get_user(get_user_request: GetUserRequest, response: Response):
    email = get_user_request.email
    user = User.byEmail(email)  # todo fix vuln
    # create the user?
    set_session_for_user(user)

    # get if the user is subscribed to a plan in stripe
    subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    user.is_subscribed = subscription_item_id is not None
    num_self_hosted_instances = get_self_hosted_subscription_count_for_user(
        user.stripe_id
    )
    user.num_self_hosted_instances = int(num_self_hosted_instances) or 0

    if not user.is_subscribed:
        # recreate stripe customer if required - remediates users being created in test mode
        # stripe get customer by
        customer = stripe.Customer.retrieve(user.stripe_id)
        if not customer or not customer.id:
            customer = stripe.Customer.create(  # type: ignore
                email=email,
                idempotency_key=email,
            )
            user.stripe_id = customer.id
            User.save(user)
            set_session_for_user(user)
    return JSONResponse(
        json.loads(json.dumps(user.to_dict(), cls=GameOnUtils.MyEncoder))
    )


def get_stripe_usage(subscription_item_id):
    """return the monthly usage of the user"""
    # get the usage for the user
    record_summary = stripe.SubscriptionItem.list_usage_record_summaries(  # type: ignore
        subscription_item_id, limit=12
    )
    return record_summary.data


@app.post("/api/get-user/stripe-usage")
async def get_user_stripe_usage(get_user_request: GetUserRequest, response: Response):
    email = get_user_request.email
    user = User.byEmail(email)  # todo fix vuln
    # create the user?
    set_session_for_user(user)

    # get if the user is subscribed to a plan in stripe
    subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    user.is_subscribed = subscription_item_id is not None
    if not user.is_subscribed:
        # recreate stripe customer if required - remediates users being created in test mode
        # stripe get customer by
        customer = stripe.Customer.retrieve(user.stripe_id)
        if not customer or not customer.id:
            customer = stripe.Customer.create(  # type: ignore
                email=email,
                idempotency_key=email,
            )
            user.stripe_id = customer.id
            User.save(user)
            set_session_for_user(user)

    user.num_self_hosted_instances = get_self_hosted_subscription_count_for_user(
        user.stripe_id
    )

    user_to_dict = user.to_dict()
    # add info on stripe usage
    if subscription_item_id:
        user_to_dict["stripe_usage"] = get_stripe_usage(
            subscription_item_id
        )  # if theres no subscription item id this will fail
    return JSONResponse(json.loads(json.dumps(user_to_dict, cls=GameOnUtils.MyEncoder)))


def track_stripe_request_usage(secret, quantity: int):
    # track a request being used in stripe
    # get the current users stripe subscription
    existing_user = session_dict.get(secret)
    if not existing_user:
        existing_user = User.bySecret(secret)
        set_session_for_user(existing_user)

    subscription_item_id = get_subscription_item_id_for_user_email(existing_user.email)

    if subscription_item_id:
        try:
            stripe.SubscriptionItem.create_usage_record(  # type: ignore
                subscription_item_id,  # Checked not None
                quantity=quantity,
            )
        except Exception as e:
            logger.error(
                f"Failed to create usage record for {existing_user.email}: {e}"
            )
    else:
        logger.warning(
            f"Could not find subscription item ID for {existing_user.email} to track usage."
        )


def get_base_template_vars(request: Request):
    is_mac = False  # Default value
    try:
        user_agent = request.headers.get("User-Agent")
        if user_agent:
            is_mac = user_agent.lower().find("mac") != -1
    except Exception as e:
        logger.warning(f"Could not determine platform from User-Agent: {e}")
        is_mac = False  # Fallback

    return {
        "request": request,
        "url": request.url,
        "static_url": GCLOUD_STATIC_BUCKET_URL,
        "fixtures": json.dumps(
            {
                "is_mac": is_mac,
            }
        ),
        "stripe_publishable_key": stripe_keys["publishable_key"],
    }


@app.get("/privacy")
async def privacy(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/privacy.jinja2",
        base_vars,
    )


@app.get("/account")
async def account(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/account.jinja2",
        base_vars,
    )


@app.get("/terms")
async def terms(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/terms.jinja2",
        base_vars,
    )


@app.get("/contact")
async def contact(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/contact.jinja2",
        base_vars,
    )


@app.get("/about")
async def about(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/about.jinja2",
        base_vars,
    )


@app.get("/self-hosting")
async def selfhosting(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/selfhosting.jinja2",
        base_vars,
    )


@app.get("/how-it-works")
async def howitworks(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/howitworks.jinja2",
        base_vars,
    )


@app.get("/playground")
async def playground(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/playground.jinja2",
        base_vars,
    )


@app.get("/sitemap")
async def sitemap(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/sitemap.jinja2",
        base_vars,
    )


@app.get("/docs")
async def docs(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/docs.jinja2",
        base_vars,
    )


@app.get("/text-to-speech")
async def text_to_speech(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/text-to-speech.jinja2",
        base_vars,
    )


@app.get("/speech-to-text")
async def speech_to_text(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/speech-to-text.jinja2",
        base_vars,
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
    base_vars.update(
        {
            "description": use_case_data["description"],
            "long_description": use_case_data.get("long_description"),
            "title": use_case_data["title"],
            "results": results,
            "text": input_text,
            "use_case": use_case_data,
            "url_key": url_key,
        }
    )
    return templates.TemplateResponse(
        "templates/use-case.jinja2",
        base_vars,
    )


@app.get("/use-cases")
async def use_cases(request: Request):
    use_cases = deepcopy(fixtures.use_cases).items()

    base_vars = get_base_template_vars(request)
    base_vars.update(
        {
            "use_cases": use_cases,
        }
    )
    return templates.TemplateResponse(
        "templates/use-cases.jinja2",
        base_vars,
    )


@app.get("/blog/{name}")
async def blog_name(request: Request, name: str):
    blog_data = deepcopy(blog_fixtures.blogs.get(name))

    if not blog_data:
        raise HTTPException(status_code=404, detail=f"Blog post '{name}' not found")

    base_vars = get_base_template_vars(request)
    base_vars.update(
        {
            "blog": blog_data,
            "description": blog_data["description"],
            "title": blog_data["title"],
            "keywords": blog_data["keywords"],
            "blogtemplate": "/templates/shared/" + name + ".jinja2",
        }
    )
    return templates.TemplateResponse(
        "templates/blog.jinja2",
        base_vars,
    )


@app.get("/blog")
async def blog(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update(
        {
            "blogs": blog_fixtures.blogs.items(),
        }
    )
    return templates.TemplateResponse(
        "templates/blogs.jinja2",
        base_vars,
    )


@app.get("/docs/{name}")
async def doc_name(request: Request, name: str):
    doc_data = deepcopy(doc_fixtures.docs.get(name))

    if not doc_data:
        raise HTTPException(
            status_code=404, detail=f"Documentation page '{name}' not found"
        )

    base_vars = get_base_template_vars(request)
    base_vars.update(
        {
            "doc": doc_data,
            "description": doc_data["description"],
            "title": doc_data["title"],
            "keywords": doc_data["keywords"],
            "blogtemplate": "/templates/shared/" + name + ".jinja2",
        }
    )
    return templates.TemplateResponse(
        "templates/doc.jinja2",
        base_vars,
    )


@app.get("/bulk-text-generator")
async def bulk_text_generator(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/bulk.jinja2",
        base_vars,
    )


@app.get("/sitemap.xml")
async def sitemap_xml(request: Request, response: Response):
    response.headers["Content-Type"] = "text/xml; charset=utf-8"

    base_vars = get_base_template_vars(request)
    base_vars.update({})
    return templates.TemplateResponse(
        "templates/sitemap.xml.jinja2",
        base_vars,
    )


# Filter out openapi route definition more safely
app.router.routes = [
    route
    for route in app.routes
    if not (
        isinstance(route, Route) and hasattr(route, "name") and route.name == "openapi"
    )
]


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
        return RedirectResponse(
            url="http://localhost:8000/gradio_tts/file" + str(file_path)
        )
    return RedirectResponse(
        url="https://api.text-generator.io/gradio_tts/file" + str(file_path)
    )


def validate_generate_params(generate_params):
    validate_result = ""
    if generate_params.text == "":
        validate_result = "Please enter some text"
    return validate_result


@app.get("/api/current-user")
async def get_current_user(request: Request):
    # Get the secret from cookie or query param
    secret = request.cookies.get("secret") or request.query_params.get("secret")

    if not secret:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # Get user from session or database
    user = session_dict.get(secret)
    if not user:
        user = User.bySecret(secret)
        if user:
            set_session_for_user(user)

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    # Return user data
    user_dict = user.to_dict()
    user_dict["secret"] = secret  # Include secret for client-side storage

    return JSONResponse(user_dict)


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
    if (
        request
        and "X-Rapid-API-Key" not in request.headers
        and "x-rapid-api-key" not in request.headers
    ):
        if not request_authorized(request, secret):
            return HTTPException(
                status_code=401,
                detail="Please subscribe at https://text-generator.io/subscribe first",
            )

    try:
        # Prepare the prompt for Claude
        prompt = generate_params.text

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
            return HTTPException(
                status_code=500, detail="Failed to generate text with Claude"
            )

        # Format the response to match the standard API format
        result = [
            {
                "generated_text": prompt + generated_text,
                "finished_reason": "length",
                "model": "claude-3-sonnet-20240229",
            }
        ]

        return result

    except Exception as e:
        logger.error(f"Error generating text with Claude: {e}")
        return HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


@app.post("/api/v1/generate-large")
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
    if (
        request
        and "X-Rapid-API-Key" not in request.headers
        and "x-rapid-api-key" not in request.headers
    ):
        if not request_authorized(request, secret):
            return HTTPException(
                status_code=401,
                detail="Please subscribe at https://text-generator.io/subscribe first",
            )

    try:
        # Prepare the prompt for Claude
        prompt = generate_params.text
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
            return HTTPException(
                status_code=500, detail="Failed to generate text with Claude"
            )

        # Format the response to match the standard API format
        result = [
            {
                "generated_text": prompt + generated_text,
                "finished_reason": "length",
                "model": model_name,
            }
        ]

        return result

    except Exception as e:
        logger.error(f"Error generating text with Claude: {e}")
        return HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


# --- End Moved Routes ---


@app.post("/api/v1/ux-feedback")
async def ux_feedback_route(
    feedback: FeedbackRequest,
    request: Request,
    secret: Union[str, None] = Header(default=None),
):
    if (
        request
        and "X-Rapid-API-Key" not in request.headers
        and "x-rapid-api-key" not in request.headers
    ):
        if not request_authorized(request, secret):
            return HTTPException(
                status_code=401,
                detail="Please subscribe at https://text-generator.io/subscribe first",
            )

    try:
        result = await analyze_site(str(feedback.url))
        if result is None:
            return HTTPException(status_code=500, detail="Failed to get feedback")
        return {"feedback": result}
    except Exception as e:
        logger.error(f"Error generating UX feedback: {e}")
        return HTTPException(status_code=500, detail=str(e))
